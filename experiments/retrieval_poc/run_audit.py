#!/usr/bin/env python3
"""Edit audit for any EasyEdit locate-then-edit method on any Hugging Face causal LM, one seed per process.

Generalises run_method_study.py (which stays unchanged for provenance) in three ways:
  * any model: AutoTokenizer + probe_scoring_v4 (BOS and answer tokenisation per tokenizer);
  * distributional side effects: every read keeps the full next-token distribution, and every post-edit read
    is compared with the unedited read (KL, JS, TV, top-10 overlap; plus divergences over the route's answers);
  * three edit schedules (--mode):
      independent  each fact is edited from the unedited model and restored afterwards (the draft's protocol);
      sequential   facts are edited one after another without restoring. After every edit the just-edited fact
                   is read; at checkpoints (--checkpoints, default: every step) every fact in the set is read,
                   edited or not, so earlier edits and untouched facts are re-audited. One restore at the end;
      batch        facts are edited in chunks of --batch-size with EasyEdit's batch_edit (MEMIT, AlphaEdit),
                   without restoring between chunks; every fact is read after every chunk;
      pairs        commutativity (N1): for every pair (A, B) in --pairs, edit A then B, read A, B and the sentinel
                   facts, restore; edit B then A, read, restore. The two final states are compared read by read
                   (commute.csv) and weight by weight (pairs.csv), with the overlap of the two subjects' keys at the
                   rewrite layers of the unedited model as a conflict predictor;
      programs     edit programs from make_programs.py (N5 compensating edits, N2 cascading repair): each program starts
                   from the unedited weights, applies its steps (a step with several edits is one batch_edit call),
                   reads after chosen steps and is restored exactly (audit_programs).

Checks (the run stops if one fails; nothing is reported from a failed run):
  A  two reads of the unedited model are identical for every fact;
  B  every edit call changes the rewrite weights relative to the state just before that call;
  C  restoring the original weights reproduces the unedited reads (independent: after each fact; otherwise at the end).

AlphaEdit keeps a record of earlier edit keys (cache_c). independent mode clears it before every edit, as in
run_method_study.py; sequential and batch modes clear it once at the start and then let it accumulate, which is
AlphaEdit's intended use for edit sequences. Logged as alphaedit_cache_policy.

Outputs in --output-dir/audit_<tag>_<model>_<method>_<mode>_seed<N>/:
  deltas.csv   one row per (step, read fact, route, answer): unedited and current scores and ranks
  dist.csv     one row per (step, read fact, route): divergences of the current read from the unedited read
  checks.csv   one row per edit step: checks B (and C in independent mode), update norms
  commute.csv  pairs mode: one row per (pair, read fact, route): divergences between the AB and BA reads
  pairs.csv    pairs mode: one row per pair: checks, update norms, order gap and additivity gap of the weight updates,
               cosine of the two first-edit updates, cosine of the two subjects' keys
  manifest.json
In pairs mode, deltas/dist rows have step "<pair_id>:AB" or "<pair_id>:BA", edited_facts in application order and
fact_edit_step 1 or 2 (position in that order); both orders are compared with the same unedited reads.
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_scoring_v4 as ps  # noqa: E402
from rome_paired_pilot import max_score_diff, max_weight_diff, restore, set_seed, snapshot  # noqa: E402

AUDIT_VERSION = "run_audit v1.3.1 (2026-11-11)"
MODES = ("independent", "sequential", "batch", "pairs", "programs")
DELTA_FIELDS = ["mode", "step", "edited_facts", "fact_id", "relation", "fact_edited", "fact_edit_step", "seed",
                "route", "kind", "route_valid", "answer_label", "answer", "pre_sum_logprob", "post_sum_logprob",
                "delta_sum_logprob", "pre_sequence_probability", "post_sequence_probability",
                "pre_first_token_rank", "post_first_token_rank", "boundary_merge", "pre_greedy", "post_greedy",
                "control_fact"]
DIST_FIELDS = ["mode", "step", "edited_facts", "fact_id", "relation", "fact_edited", "fact_edit_step", "seed",
               "route", "kind", "route_valid", "kl_pre_post", "kl_post_pre", "js_bits", "tv", "argmax_changed",
               "top10_overlap", "n_candidates", "cand_kl_pre_post", "cand_js_bits", "cand_tv"]
CHECK_FIELDS = ["mode", "step", "edited_facts", "seed", "check_A_repeat_max_diff", "check_B_weight_change_max_abs",
                "check_C_restore_max_diff", "step_delta_frobenius_norm", "cumulative_delta_frobenius_norm"]
COMMUTE_FIELDS = ["pair_id", "pair_class", "fact_a", "fact_b", "seed", "fact_id", "role", "route", "kind", "route_valid",
                  "kl_ab_ba", "kl_ba_ab", "js_bits", "tv", "argmax_changed", "top10_overlap"]
PAIR_FIELDS = ["pair_id", "pair_class", "fact_a", "fact_b", "seed", "check_B_min", "check_C_max",
               "norm_dA", "norm_dB", "cos_dA_dB", "norm_dAB", "norm_dBA", "gap_AB_BA", "add_gap_AB", "add_gap_BA",
               "key_cos_mean", "key_cos_last_layer"]


# ---------------------------------------------------------------- reads
def read_fact(model, tokenizer, probes, device, gen_tokens):
    return {r["route"]: ps.probe_prompt(model, tokenizer, r["prompt"], list(r["answers"].items()), device,
                                        gen_tokens=gen_tokens, keep_distribution=True)
            for r in probes["routes"]}


def strip(read):
    """A read without the in-memory distributions (for JSON)."""
    return {route: {k: v for k, v in r.items() if not k.startswith("_")} for route, r in read.items()}


def delta_rows(ctx, probes, pre, post):
    for r in probes["routes"]:
        a_pre, a_post = pre[r["route"]]["answers"], post[r["route"]]["answers"]
        for label in a_pre:
            x, y = a_pre[label], a_post[label]
            yield {**ctx, "route": r["route"], "kind": r["kind"], "route_valid": r["valid"], "answer_label": label,
                   "answer": x["answer"], "pre_sum_logprob": x["sum_logprob"], "post_sum_logprob": y["sum_logprob"],
                   "delta_sum_logprob": y["sum_logprob"] - x["sum_logprob"],
                   "pre_sequence_probability": x["sequence_probability"],
                   "post_sequence_probability": y["sequence_probability"],
                   "pre_first_token_rank": x["first_token_rank"], "post_first_token_rank": y["first_token_rank"],
                   "boundary_merge": x["boundary_merge"], "pre_greedy": pre[r["route"]]["greedy_continuation"],
                   "post_greedy": post[r["route"]]["greedy_continuation"], "control_fact": r.get("control_fact", "")}


def dist_rows(ctx, probes, pre, post):
    for r in probes["routes"]:
        a, b = pre[r["route"]], post[r["route"]]
        d = ps.next_token_shift(a["_next_token_logprobs"], b["_next_token_logprobs"])
        row = {**ctx, "route": r["route"], "kind": r["kind"], "route_valid": r["valid"], **d,
               "n_candidates": len(a["answers"]), "cand_kl_pre_post": "", "cand_js_bits": "", "cand_tv": ""}
        if len(a["answers"]) >= 2:
            c = ps.candidate_shift({k: v["sum_logprob"] for k, v in a["answers"].items()},
                                   {k: v["sum_logprob"] for k, v in b["answers"].items()})
            row.update({"cand_kl_pre_post": c["kl_pre_post"], "cand_js_bits": c["js_bits"], "cand_tv": c["tv"]})
        yield row


# ---------------------------------------------------------------- core (no EasyEdit; tested offline)
def audit(model, tokenizer, device, facts, steps, edit_fn, rewrite_params, mode, emit, seed=0,
          checkpoints=None, gen_tokens=10, reread_gen_tokens=10, tol=1e-4):
    """facts: list of probe dicts; steps: list of lists of indices into facts, edited together at that step.
    edit_fn(list of edit dicts) performs one edit call and returns EasyEdit's result.
    emit(kind, rows) receives "delta" / "dist" / "check" rows as they are produced."""
    if mode not in ("independent", "sequential", "batch"):
        raise ValueError(f"audit() does not run mode {mode!r} (pairs: audit_pairs; programs: audit_programs)")
    restore_each = mode == "independent"
    base = {p["fact_id"]: read_fact(model, tokenizer, p, device, gen_tokens) for p in facts}
    worst_a = max(max_score_diff(base[p["fact_id"]], read_fact(model, tokenizer, p, device, gen_tokens)) for p in facts)
    if worst_a > tol:
        raise RuntimeError(f"Check A failed: repeat reads differ by {worst_a}")
    original = snapshot(model, rewrite_params)
    edited_at = {}
    for k, idxs in enumerate(steps, 1):
        names = [facts[i]["fact_id"] for i in idxs]
        before = original if restore_each else snapshot(model, rewrite_params)
        result = edit_fn([facts[i]["edit"] for i in idxs])
        out_model = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 and isinstance(result[1], torch.nn.Module) else model
        if out_model is not model:
            raise RuntimeError("editor returned a different model object; reads would not see the edit")
        chk = {"mode": mode, "step": k, "edited_facts": "|".join(names), "seed": seed,
               "check_A_repeat_max_diff": worst_a, "check_B_weight_change_max_abs": max_weight_diff(model, before)}
        if chk["check_B_weight_change_max_abs"] == 0.0:
            raise RuntimeError(f"step {k} ({names}): check B failed (edit not live)")
        chk["step_delta_frobenius_norm"] = sum(float((model.get_parameter(n).detach() - w).norm()) for n, w in before.items())
        chk["cumulative_delta_frobenius_norm"] = sum(float((model.get_parameter(n).detach() - w).norm()) for n, w in original.items())
        for n in names:
            edited_at[n] = k
        read_all = not restore_each and (checkpoints is None or k in checkpoints or k == len(steps))
        to_read = facts if read_all else [facts[i] for i in idxs]
        for p in to_read:
            fid = p["fact_id"]
            post = read_fact(model, tokenizer, p, device, gen_tokens if fid in names else reread_gen_tokens)
            pre = base[fid] if reread_gen_tokens == gen_tokens or fid in names else {
                route: {**r, "greedy_continuation": ""} for route, r in base[fid].items()}
            ctx = {"mode": mode, "step": k, "edited_facts": "|".join(names), "fact_id": fid,
                   "relation": p["relation"], "fact_edited": fid in edited_at, "fact_edit_step": edited_at.get(fid, ""),
                   "seed": seed}
            emit("delta", list(delta_rows(ctx, p, pre, post)))
            emit("dist", list(dist_rows(ctx, p, pre, post)))
        if restore_each:
            restore(model, original)
            chk["check_C_restore_max_diff"] = max(max_score_diff(base[facts[i]["fact_id"]],
                                                                 read_fact(model, tokenizer, facts[i], device, gen_tokens))
                                                  for i in idxs)
            if chk["check_C_restore_max_diff"] > tol:
                raise RuntimeError(f"step {k} ({names}): check C failed {chk['check_C_restore_max_diff']}")
        emit("check", [chk])
    if not restore_each:
        restore(model, original)
        worst_c = max(max_score_diff(base[p["fact_id"]], read_fact(model, tokenizer, p, device, gen_tokens)) for p in facts)
        if worst_c > tol:
            raise RuntimeError(f"Check C failed: restored model differs from unedited reads by {worst_c}")
        emit("check", [{"mode": mode, "step": "final_restore", "edited_facts": "", "seed": seed,
                        "check_A_repeat_max_diff": worst_a, "check_C_restore_max_diff": worst_c}])
    return {p["fact_id"]: strip(base[p["fact_id"]]) for p in facts}


def subject_keys(model, tokenizer, device, fact, modules):
    """Input of each rewrite module at the subject's last token of the edit prompt (the key the editors write to; ROME
    and MEMIT average it over extra context prefixes, which is not done here). Returns float32 CPU vectors."""
    prompt, subject = fact["edit"]["prompt"], fact["edit"]["subject"]
    if subject not in prompt:
        raise ValueError(f"{fact['fact_id']}: subject {subject!r} not in prompt {prompt!r}")
    ids = ps.encode_prompt(tokenizer, prompt)
    idx = len(ps.encode_prompt(tokenizer, prompt[:prompt.index(subject) + len(subject)])) - 1
    got = {}
    hooks = [model.get_submodule(m).register_forward_hook(
        lambda mod, inp, out, m=m: got.__setitem__(m, inp[0][0, idx].detach().float().cpu())) for m in modules]
    try:
        with torch.inference_mode():
            model(torch.tensor([ids], device=device))
    finally:
        for hk in hooks:
            hk.remove()
    return [got[m] for m in modules]


def _flat_stats(xs, ys):
    """Frobenius norms of two weight-update dicts and their cosine (over all rewrite matrices together)."""
    dot = sum(float((xs[n].double() * ys[n].double()).sum()) for n in xs)
    nx = sum(float(xs[n].double().pow(2).sum()) for n in xs) ** 0.5
    ny = sum(float(ys[n].double().pow(2).sum()) for n in ys) ** 0.5
    return nx, ny, (dot / (nx * ny) if nx and ny else float("nan"))


def _diff_norm(xs, ys):
    return sum(float((xs[n].double() - ys[n].double()).pow(2).sum()) for n in xs) ** 0.5


def audit_pairs(model, tokenizer, device, facts, pairs, sentinels, edit_fn, rewrite_params, emit, seed=0,
                reset_fn=None, key_modules=None, gen_tokens=10, reread_gen_tokens=10, tol=1e-4):
    """Commutativity of edit pairs. facts: fact_id -> probe dict; pairs: dicts with pair_id, pair_class, fact_a, fact_b;
    sentinels: fact_ids read after every pair and never edited. For each pair and order (AB, BA): from the unedited
    weights (reset_fn() first, e.g. AlphaEdit's cache), edit the first fact, then the second without restoring (check B
    for each call), read both facts and the sentinels, restore, re-read both facts (check C). Then compare the AB and
    BA reads (emit "commute") and the weight updates (emit "pair"). Returns the unedited reads without distributions."""
    if not set(sentinels).isdisjoint({x for p in pairs for x in (p["fact_a"], p["fact_b"])}):
        raise ValueError("a sentinel is also part of a pair")
    involved = sorted({x for p in pairs for x in (p["fact_a"], p["fact_b"])} | set(sentinels))
    base = {f: read_fact(model, tokenizer, facts[f], device, gen_tokens) for f in involved}
    worst_a = max(max_score_diff(base[f], read_fact(model, tokenizer, facts[f], device, gen_tokens)) for f in involved)
    if worst_a > tol:
        raise RuntimeError(f"Check A failed: repeat reads differ by {worst_a}")
    keys = {f: subject_keys(model, tokenizer, device, facts[f], key_modules) for f in involved} if key_modules else {}
    original = snapshot(model, rewrite_params)
    for pr in pairs:
        pid, a, b = pr["pair_id"], pr["fact_a"], pr["fact_b"]
        reads, first, final, check_b, check_c = {}, {}, {}, [], []
        for order, seq in (("AB", (a, b)), ("BA", (b, a))):
            if reset_fn is not None:
                reset_fn()
            for pos, f in enumerate(seq, 1):
                before = snapshot(model, rewrite_params)
                result = edit_fn([facts[f]["edit"]])
                out_model = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 and isinstance(result[1], torch.nn.Module) else model
                if out_model is not model:
                    raise RuntimeError("editor returned a different model object; reads would not see the edit")
                check_b.append(max_weight_diff(model, before))
                if check_b[-1] == 0.0:
                    raise RuntimeError(f"{pid}:{order} edit {pos} ({f}): check B failed (edit not live)")
                if pos == 1:
                    first[f] = {n: model.get_parameter(n).detach() - w for n, w in original.items()}
            final[order] = {n: model.get_parameter(n).detach() - w for n, w in original.items()}
            reads[order] = {}
            for f in (a, b, *sentinels):
                edited = f in seq
                post = read_fact(model, tokenizer, facts[f], device, gen_tokens if edited else reread_gen_tokens)
                pre = base[f] if reread_gen_tokens == gen_tokens or edited else {
                    route: {**r, "greedy_continuation": ""} for route, r in base[f].items()}
                ctx = {"mode": "pairs", "step": f"{pid}:{order}", "edited_facts": "|".join(seq), "fact_id": f,
                       "relation": facts[f]["relation"], "fact_edited": edited,
                       "fact_edit_step": seq.index(f) + 1 if edited else "", "seed": seed}
                emit("delta", list(delta_rows(ctx, facts[f], pre, post)))
                emit("dist", list(dist_rows(ctx, facts[f], pre, post)))
                reads[order][f] = post
            restore(model, original)
            check_c.append(max(max_score_diff(base[f], read_fact(model, tokenizer, facts[f], device, 0)) for f in seq))
            if check_c[-1] > tol:
                raise RuntimeError(f"{pid}:{order}: check C failed {check_c[-1]}")
            emit("check", [{"mode": "pairs", "step": f"{pid}:{order}", "edited_facts": "|".join(seq), "seed": seed,
                            "check_A_repeat_max_diff": worst_a, "check_B_weight_change_max_abs": min(check_b[-2:]),
                            "check_C_restore_max_diff": check_c[-1],
                            "cumulative_delta_frobenius_norm": _flat_stats(final[order], final[order])[0]}])
        crow = []
        for f in (a, b, *sentinels):
            role = "A" if f == a else "B" if f == b else "sentinel"
            for r in facts[f]["routes"]:
                d = ps.next_token_shift(reads["AB"][f][r["route"]]["_next_token_logprobs"],
                                        reads["BA"][f][r["route"]]["_next_token_logprobs"])
                crow.append({"pair_id": pid, "pair_class": pr["pair_class"], "fact_a": a, "fact_b": b, "seed": seed,
                             "fact_id": f, "role": role, "route": r["route"], "kind": r["kind"], "route_valid": r["valid"],
                             "kl_ab_ba": d["kl_pre_post"], "kl_ba_ab": d["kl_post_pre"], "js_bits": d["js_bits"],
                             "tv": d["tv"], "argmax_changed": d["argmax_changed"], "top10_overlap": d["top10_overlap"]})
        emit("commute", crow)
        na, nb, cos_ab = _flat_stats(first[a], first[b])
        add = {n: first[a][n] + first[b][n] for n in original}
        row = {"pair_id": pid, "pair_class": pr["pair_class"], "fact_a": a, "fact_b": b, "seed": seed,
               "check_B_min": min(check_b), "check_C_max": max(check_c), "norm_dA": na, "norm_dB": nb, "cos_dA_dB": cos_ab,
               "norm_dAB": _flat_stats(final["AB"], final["AB"])[0], "norm_dBA": _flat_stats(final["BA"], final["BA"])[0],
               "gap_AB_BA": _diff_norm(final["AB"], final["BA"]),
               "add_gap_AB": _diff_norm(final["AB"], add), "add_gap_BA": _diff_norm(final["BA"], add)}
        if keys:
            cs = [float(torch.nn.functional.cosine_similarity(x, y, dim=0)) for x, y in zip(keys[a], keys[b])]
            row.update({"key_cos_mean": sum(cs) / len(cs), "key_cos_last_layer": cs[-1]})
        emit("pair", [row])
    return {f: strip(base[f]) for f in involved}


def program_edit(facts, item):
    """Edit request of a program item {"fact": id, "dir": "fwd" | "inv"}; inv reverses the fact's edit (o* -> o)."""
    e = facts[item["fact"]]["edit"]
    if item["dir"] == "fwd":
        return dict(e)
    if item["dir"] == "inv":
        return {**e, "target_old": e["target_new"], "target_new": e["target_old"]}
    raise ValueError(item)


def audit_programs(model, tokenizer, device, facts, programs, sentinels, edit_fn, rewrite_params, emit, seed=0,
                   reset_fn=None, derived=(), rules=None, gen_tokens=10, reread_gen_tokens=10, tol=1e-4):
    """Edit programs (N2, N5; see make_programs.py). facts: fact_id -> probe dict; derived: fact_ids whose routes have no
    validity yet (judged here on the unedited reads with the screening rules). Each program starts from the unedited
    weights (reset_fn() first), applies its steps (edit_fn gets the list of edit requests of one step: one edit, or a
    batch), checks B after every step, reads its facts and the sentinels after the steps in read_at, restores and
    re-reads the edited facts (check C). A program with compare_to is also compared read by read with the final reads
    of that (earlier) program (emit "commute"). Returns the unedited reads without distributions."""
    from screen_facts import judge
    involved = sorted({f for p in programs for f in p["read"]} | set(sentinels))
    if not set(sentinels).isdisjoint({it["fact"] for p in programs for st in p["steps"] for it in st}):
        raise ValueError("a sentinel is edited by a program")
    base = {f: read_fact(model, tokenizer, facts[f], device, gen_tokens) for f in involved}
    for f in derived:
        if f not in base:
            continue                                  # not read by any program: its validity is never used
        for r in facts[f]["routes"]:
            r["valid"], r["deciding_answer"] = judge(r, base[f][r["route"]], rules)
    worst_a = max(max_score_diff(base[f], read_fact(model, tokenizer, facts[f], device, gen_tokens)) for f in involved)
    if worst_a > tol:
        raise RuntimeError(f"Check A failed: repeat reads differ by {worst_a}")
    original = snapshot(model, rewrite_params)
    final_reads = {}
    keep = {p["compare_to"] for p in programs if p.get("compare_to")}
    for pr in programs:
        pid = pr["program_id"]
        if reset_fn is not None:
            reset_fn()
        applied, edited_at, reads = [], {}, {}
        for k, step in enumerate(pr["steps"], 1):
            before = snapshot(model, rewrite_params)
            result = edit_fn([program_edit(facts, it) for it in step])
            out_model = result[1] if isinstance(result, (tuple, list)) and len(result) > 1 and isinstance(result[1], torch.nn.Module) else model
            if out_model is not model:
                raise RuntimeError("editor returned a different model object; reads would not see the edit")
            chk = {"mode": "programs", "step": f"{pid}:{k}", "seed": seed, "check_A_repeat_max_diff": worst_a,
                   "check_B_weight_change_max_abs": max_weight_diff(model, before)}
            if chk["check_B_weight_change_max_abs"] == 0.0:
                raise RuntimeError(f"{pid} step {k}: check B failed (edit not live)")
            chk["step_delta_frobenius_norm"] = sum(float((model.get_parameter(n).detach() - w).norm()) for n, w in before.items())
            chk["cumulative_delta_frobenius_norm"] = sum(float((model.get_parameter(n).detach() - w).norm()) for n, w in original.items())
            for it in step:
                applied.append(it["fact"] + ("~inv" if it["dir"] == "inv" else ""))
                edited_at[it["fact"]] = k
            chk["edited_facts"] = "|".join(applied)
            if k in pr["read_at"]:
                for f in (*pr["read"], *sentinels):
                    edited = f in edited_at
                    post = read_fact(model, tokenizer, facts[f], device, gen_tokens if edited else reread_gen_tokens)
                    pre = base[f] if reread_gen_tokens == gen_tokens or edited else {
                        route: {**r, "greedy_continuation": ""} for route, r in base[f].items()}
                    ctx = {"mode": "programs", "step": f"{pid}:{k}", "edited_facts": "|".join(applied), "fact_id": f,
                           "relation": facts[f]["relation"], "fact_edited": edited, "fact_edit_step": edited_at.get(f, ""),
                           "seed": seed}
                    emit("delta", list(delta_rows(ctx, facts[f], pre, post)))
                    emit("dist", list(dist_rows(ctx, facts[f], pre, post)))
                    reads[f] = post
            if k < len(pr["steps"]):
                emit("check", [chk])
        restore(model, original)
        chk["check_C_restore_max_diff"] = max(max_score_diff(base[f], read_fact(model, tokenizer, facts[f], device, 0))
                                              for f in sorted(set(edited_at) & set(involved)) or pr["read"])
        if chk["check_C_restore_max_diff"] > tol:
            raise RuntimeError(f"{pid}: check C failed {chk['check_C_restore_max_diff']}")
        emit("check", [chk])
        if pr.get("compare_to"):
            ref = final_reads.pop(pr["compare_to"])
            crow = []
            for f in (*pr["read"], *sentinels):
                for r in facts[f]["routes"]:
                    d = ps.next_token_shift(ref[f][r["route"]]["_next_token_logprobs"], reads[f][r["route"]]["_next_token_logprobs"])
                    crow.append({"pair_id": pid, "pair_class": pr["kind"], "fact_a": pr["compare_to"], "fact_b": pid,
                                 "seed": seed, "fact_id": f, "role": "sentinel" if f in sentinels else "read",
                                 "route": r["route"], "kind": r["kind"], "route_valid": r["valid"],
                                 "kl_ab_ba": d["kl_pre_post"], "kl_ba_ab": d["kl_post_pre"], "js_bits": d["js_bits"],
                                 "tv": d["tv"], "argmax_changed": d["argmax_changed"], "top10_overlap": d["top10_overlap"]})
            emit("commute", crow)
        if pid in keep:
            final_reads[pid] = reads
    return {f: strip(base[f]) for f in involved}


def alphaedit_reset(alpha_main, model, hparams):
    """Clear AlphaEdit's record of earlier edit keys (cache_c) for any architecture.

    EasyEdit 431d9bd re-initialises cache_c when cache_c_new is False, but only for llama/qwen/gpt2-xl model names
    (AlphaEdit_main.py, apply_AlphaEdit_to_model), although its projection code also handles GPT-J. On GPT-J the
    re-initialisation is skipped and the first edit fails with NameError: name 'cache_c' is not defined (job 16997).
    Here the zero matrix is created directly with the rewrite module's input dimension (nn.Linear: in_features;
    GPT-2's Conv1D stores weights as (in, out): weight.shape[0]). For GPT-2 XL this is exactly EasyEdit's own
    re-initialisation (zeros of shape (len(layers), 6400, 6400) on the CPU)."""
    mod = model.get_submodule(hparams.rewrite_module_tmp.format(hparams.layers[-1]))
    d = mod.in_features if isinstance(mod, torch.nn.Linear) else mod.weight.shape[0]
    alpha_main.cache_c = torch.zeros((len(hparams.layers), d, d), device="cpu")
    alpha_main.cache_c_new = True


def make_steps(n, mode, batch_size):
    if mode in ("independent", "sequential"):
        return [[i] for i in range(n)]
    return [list(range(i, min(i + batch_size, n))) for i in range(0, n, batch_size)]


class CsvSink:
    """Streams rows to deltas.csv / dist.csv / checks.csv so a long run leaves usable partial output."""
    def __init__(self, out, pairs=False):
        self.files, self.writers = {}, {}
        kinds = [("delta", "deltas.csv", DELTA_FIELDS), ("dist", "dist.csv", DIST_FIELDS), ("check", "checks.csv", CHECK_FIELDS)]
        if pairs:
            kinds += [("commute", "commute.csv", COMMUTE_FIELDS), ("pair", "pairs.csv", PAIR_FIELDS)]
        for kind, name, fields in kinds:
            self.files[kind] = open(out / name, "w", newline="", encoding="utf-8")
            self.writers[kind] = csv.DictWriter(self.files[kind], fieldnames=fields, restval="")
            self.writers[kind].writeheader()

    def __call__(self, kind, rows):
        self.writers[kind].writerows(rows)
        self.files[kind].flush()
        if kind in ("check", "pair"):
            for r in rows:
                print("step" if kind == "check" else "pair", r.get("step", r.get("pair_id")), {k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()
                                          if k.startswith(("check", "gap", "key_cos", "cos_")) or k.endswith("norm")}, flush=True)

    def close(self):
        for f in self.files.values():
            f.close()


# ---------------------------------------------------------------- EasyEdit wiring
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_mode_args(args):
    """Refuse flags that the chosen mode would silently ignore. Runs before the model is loaded.
    v1.3.1: replaces a guard that also fired in pairs mode (jobs 18781-18784 failed on it)."""
    allowed = {"pairs": {"pairs", "sentinels_file"}, "programs": {"programs", "sentinels_file", "derived_facts"}}
    given = {k for k in ("pairs", "programs", "sentinels_file", "derived_facts") if getattr(args, k)}
    extra = given - allowed.get(args.mode, set())
    if extra:
        raise ValueError(f"{args.mode} mode does not use {sorted('--' + k.replace('_', '-') for k in extra)}")
    if args.mode == "pairs" and not args.pairs:
        raise ValueError("pairs mode needs --pairs")
    if args.mode == "programs" and not args.programs:
        raise ValueError("programs mode needs --programs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=("ROME", "MEMIT", "AlphaEdit"))
    ap.add_argument("--hparams", required=True, help="EasyEdit hparams path without .yaml")
    ap.add_argument("--model", required=True, help="local model directory; must equal model_name in the hparams")
    ap.add_argument("--probes-dir", required=True, nargs="+")
    ap.add_argument("--mode", required=True, choices=MODES)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--order", default="sorted", help="'sorted' (by fact_id) or 'shuffle:<int>' (sequential/batch)")
    ap.add_argument("--batch-size", type=int, default=0, help="batch mode: facts per batch_edit chunk (0 = all)")
    ap.add_argument("--checkpoints", default="", help="sequential: steps at which all facts are read, separated by ':' or ','"
                                                      " (default every step; the last step is always included). Use ':'"
                                                      " inside sbatch --export, which splits on commas (job 16996).")
    ap.add_argument("--holdout", type=int, default=0,
                    help="sequential/batch: the last N facts of the order are never edited, only read (sentinels for "
                         "side effects on untouched facts; job 16996 had none, so every neighbour was itself edited)")
    ap.add_argument("--reread-gen-tokens", type=int, default=10,
                    help="greedy tokens for re-reads of facts not edited at this step (0 skips generation)")
    ap.add_argument("--pairs", default="", help="pairs mode: pairs.csv from make_pairs.py (pair_id, pair_class, fact_a, fact_b)")
    ap.add_argument("--sentinels-file", default="", help="pairs/programs: fact_ids read after every read, one per line")
    ap.add_argument("--programs", default="", help="programs mode: programs.jsonl from make_programs.py")
    ap.add_argument("--derived-facts", default="", help="programs mode: derived_facts.csv (facts made for repairs)")
    ap.add_argument("--candidates", default="", help="programs mode: candidate fact file, neighbour pool for derived facts")
    ap.add_argument("--templates", default="", help="programs mode: relation templates (probes and validity of derived facts)")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--tag", default=os.environ.get("SLURM_ARRAY_JOB_ID", os.environ.get("SLURM_JOB_ID", "local")))
    ap.add_argument("--gpu-mem-gb", type=float, default=float(os.environ.get("GPU_MEM_GB", "0")))
    args = ap.parse_args()
    check_mode_args(args)

    from run_method_study import load_many, stats_files  # same probe loading and stats lookup as the draft's runs
    facts = [p for p, _ in load_many(args.probes_dir)]
    probe_md5 = {p["fact_id"]: m for p, m in load_many(args.probes_dir)}
    if args.order.startswith("shuffle:"):
        random.Random(int(args.order.split(":", 1)[1])).shuffle(facts)
    elif args.order != "sorted":
        raise ValueError(args.order)
    print(AUDIT_VERSION, "|", ps.SCRIPT_VERSION, "|", args.method, args.mode, "seed", args.seed, "|", len(facts),
          "facts in order:", [p["fact_id"] for p in facts], flush=True)
    print("GPU memory:", ps.cap_gpu_memory(args.gpu_mem_gb), flush=True)

    import easyeditor
    from transformers import AutoTokenizer
    hparams = getattr(easyeditor, f"{args.method}HyperParams").from_hparams(args.hparams)
    if hparams.alg_name != args.method:
        raise ValueError(f"hparams alg_name={hparams.alg_name!r} but --method={args.method!r}")
    if Path(str(hparams.model_name)).expanduser().resolve() != Path(args.model).expanduser().resolve():
        raise ValueError(f"Model mismatch: hparams model_name={hparams.model_name!r}; --model={args.model!r}")
    hp_file = args.hparams + ".yaml"
    stats = stats_files(hparams)
    if "MISSING" in stats.values():
        raise FileNotFoundError(f"Covariance statistics missing: {stats}")
    p_md5, alpha_main = None, None
    if args.method == "AlphaEdit":
        if not Path(hparams.P_loc).exists():
            raise FileNotFoundError(f"AlphaEdit projection {hparams.P_loc} missing")
        p_md5 = md5(hparams.P_loc)
        import importlib  # easyeditor.models is shadowed by easyeditor.trainer.models as an attribute
        alpha_main = importlib.import_module("easyeditor.models.alphaedit.AlphaEdit_main")
    if args.holdout and args.mode in ("independent", "pairs", "programs"):
        raise ValueError("--holdout only applies to sequential/batch runs")
    pairs, sentinels = [], []
    if args.mode == "pairs":
        if not args.pairs:
            raise ValueError("pairs mode needs --pairs")
        with open(args.pairs, newline="", encoding="utf-8") as fh:
            pairs = list(csv.DictReader(fh))
        sentinels = [x.strip() for x in open(args.sentinels_file, encoding="utf-8") if x.strip()] if args.sentinels_file else []
        missing = ({x for p in pairs for x in (p["fact_a"], p["fact_b"])} | set(sentinels)) - {p["fact_id"] for p in facts}
        if missing:
            raise ValueError(f"pairs/sentinels name facts not in the probes: {sorted(missing)}")
        print("pairs:", len(pairs), "| sentinels:", sentinels, flush=True)
    programs, derived, rules, skipped = [], [], None, []
    if args.mode == "programs":
        import screen_facts_v4 as sv
        from screen_facts import load_facts
        with open(args.programs, encoding="utf-8") as fh:
            programs = [json.loads(x) for x in fh if x.strip()]
        sentinels = [x.strip() for x in open(args.sentinels_file, encoding="utf-8") if x.strip()] if args.sentinels_file else []
        templates = json.loads(Path(args.templates).read_text(encoding="utf-8"))
        rules = templates["validity_rules"]
        if args.derived_facts:
            pool = load_facts(args.candidates)
            for row in load_facts(args.derived_facts):
                facts.append(sv.build_probes(row, pool, templates))
                derived.append(row["fact_id"])
        if args.method == "ROME":                     # no batch_edit for ROME: programs with a multi-edit step are skipped
            skipped = [p["program_id"] for p in programs if any(len(st) > 1 for st in p["steps"])]
            programs = [p for p in programs if p["program_id"] not in skipped]
        names = {p["fact_id"] for p in facts}
        missing = ({it["fact"] for p in programs for st in p["steps"] for it in st} | {f for p in programs for f in p["read"]}
                   | set(sentinels)) - names
        if missing:
            raise ValueError(f"programs/sentinels name facts not in the probes: {sorted(missing)}")
        print("programs:", len(programs), "| skipped (batch, ROME):", skipped, "| derived facts:", derived,
              "| sentinels:", sentinels, flush=True)
    n_edit = len(facts) - args.holdout
    if n_edit < 1:
        raise ValueError(f"--holdout {args.holdout} leaves no fact to edit")
    holdout_ids = [p["fact_id"] for p in facts[n_edit:]]
    steps = make_steps(n_edit, args.mode, args.batch_size or n_edit)
    if args.mode == "batch":
        hparams.batch_size = args.batch_size or n_edit
    # Name the fact each control route reads, so an analysis can tell whether that fact was itself edited by step k:
    # same-relation neighbours carry control_fact from screening; the new object's own fact is the loaded fact of the
    # same relation whose old object is this edit's new object ("" if that fact is not in the set: never edited).
    owner = {(p["relation"], p["edit"]["target_old"]): p["fact_id"] for p in facts}
    for p in facts:
        for r in p["routes"]:
            if r["route"] == "control_new_object_own_fact":
                r["control_fact"] = owner.get((p["relation"], p["edit"]["target_new"]), "")
    print("edited:", n_edit, "| held out (read only):", holdout_ids, flush=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    editor = easyeditor.BaseEditor.from_hparams(hparams)
    model = editor.model
    model.eval()
    device = next(model.parameters()).device
    if device.type != "cuda":
        raise RuntimeError("Model not on CUDA")
    rewrite_params = [hparams.rewrite_module_tmp.format(layer) + ".weight" for layer in hparams.layers]
    if alpha_main is not None:
        alphaedit_reset(alpha_main, model, hparams)          # sequential/batch: once, here; independent: before every edit
        print("AlphaEdit cache_c initialised:", tuple(alpha_main.cache_c.shape), flush=True)
    print("tokenizer", type(tokenizer).__name__, "| BOS prepended:", bool(ps.bos_prefix(tokenizer)),
          "| dtype", next(model.parameters()).dtype, "| rewrite params", rewrite_params, flush=True)

    def edit_fn(edits):
        set_seed(args.seed)
        if args.mode == "independent" and alpha_main is not None:
            alphaedit_reset(alpha_main, model, hparams)   # forget keys of earlier (already restored) edits
        kw = dict(prompts=[e["prompt"] for e in edits], ground_truth=[e["target_old"] for e in edits],
                  target_new=[e["target_new"] for e in edits], subject=[e["subject"] for e in edits],
                  sequential_edit=True, verbose=False)
        batch = args.mode == "batch" or (args.mode == "programs" and len(edits) > 1)
        if args.mode == "programs":
            # EasyEdit's edit() asserts batch_size == 1 and batch_edit() chunks by batch_size (editor.hparams is this
            # object): set it per call (job 18046 failed with the run-wide maximum)
            hparams.batch_size = len(edits)
        return editor.batch_edit(**kw) if batch else editor.edit(**kw)

    checkpoints = {int(x) for x in args.checkpoints.replace(":", ",").split(",") if x.strip()} or None
    print("checkpoints:", sorted(checkpoints) if checkpoints else "every step", flush=True)
    out = Path(args.output_dir) / f"audit_{args.tag}_{Path(args.model).name}_{args.method}_{args.mode}_seed{args.seed}"
    out.mkdir(parents=True, exist_ok=True)
    sink = CsvSink(out, pairs=args.mode in ("pairs", "programs"))
    try:
        if args.mode == "pairs":
            base = audit_pairs(model, tokenizer, device, {p["fact_id"]: p for p in facts}, pairs, sentinels, edit_fn,
                               rewrite_params, sink, seed=args.seed,
                               reset_fn=(lambda: alphaedit_reset(alpha_main, model, hparams)) if alpha_main is not None else None,
                               key_modules=[hparams.rewrite_module_tmp.format(layer) for layer in hparams.layers],
                               reread_gen_tokens=args.reread_gen_tokens)
            steps = [[p["fact_a"], p["fact_b"]] for p in pairs]
        elif args.mode == "programs":
            base = audit_programs(model, tokenizer, device, {p["fact_id"]: p for p in facts}, programs, sentinels, edit_fn,
                                  rewrite_params, sink, seed=args.seed,
                                  reset_fn=(lambda: alphaedit_reset(alpha_main, model, hparams)) if alpha_main is not None else None,
                                  derived=derived, rules=rules, reread_gen_tokens=args.reread_gen_tokens)
            steps = [p["program_id"] for p in programs]
        else:
            base = audit(model, tokenizer, device, facts, steps, edit_fn, rewrite_params, args.mode, sink, seed=args.seed,
                         checkpoints=checkpoints, reread_gen_tokens=args.reread_gen_tokens)
            steps = [[facts[i]["fact_id"] for i in s] for s in steps]
    finally:
        sink.close()
    with open(out / "baseline_reads.json", "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False)
    src = Path(args.model) / "SOURCE.txt"
    with open(out / "manifest.json", "w") as f:
        json.dump({"audit_version": AUDIT_VERSION, "scorer": ps.SCRIPT_VERSION, "method": args.method,
                   "mode": args.mode, "seed": args.seed, "order": [p["fact_id"] for p in facts],
                   "steps": steps, "checkpoints": sorted(checkpoints or []),
                   "holdout": holdout_ids, "pairs_file": args.pairs or None,
                   "pairs_md5": md5(args.pairs) if args.pairs else None, "sentinels": sentinels,
                   "programs_file": args.programs or None, "programs_md5": md5(args.programs) if args.programs else None,
                   "programs_skipped": skipped, "derived_facts": derived,
                   "derived_facts_md5": md5(args.derived_facts) if args.derived_facts else None,
                   "templates_md5": md5(args.templates) if args.templates else None,
                   "reread_gen_tokens": args.reread_gen_tokens, "probes_dirs": args.probes_dir, "probe_md5": probe_md5,
                   "model": args.model, "model_source": src.read_text() if src.exists() else None,
                   "tokenizer_class": type(tokenizer).__name__, "bos_prepended": bool(ps.bos_prefix(tokenizer)),
                   "dtype": str(next(model.parameters()).dtype), "hparams_file": hp_file, "hparams_md5": md5(hp_file),
                   "layers": hparams.layers, "mom2_adjustment": getattr(hparams, "mom2_adjustment", None),
                   "stats_md5": stats, "alphaedit_projection_md5": p_md5,
                   "alphaedit_cache_policy": None if alpha_main is None else
                   ("reset before every edit" if args.mode == "independent" else
                    "reset before each order of each pair, accumulate over its two edits" if args.mode == "pairs" else
                    "reset before each program, accumulate over its steps" if args.mode == "programs" else
                    "reset once at start, then accumulate"),
                   "torch": torch.__version__, "transformers": __import__("transformers").__version__,
                   "gpu": torch.cuda.get_device_name(0), "gpu_peak_gb": ps.gpu_peak_gb()}, f, indent=1)
    print("Saved under", out, flush=True)
    print(f"Peak GPU memory allocated: {ps.gpu_peak_gb()} GiB", flush=True)
    print(f"AUDIT COMPLETE: {args.method} {args.mode}, {len(facts)} facts, {len(steps)} steps, seed {args.seed}, "
          "all checks passed. Descriptive only.", flush=True)


if __name__ == "__main__":
    main()
