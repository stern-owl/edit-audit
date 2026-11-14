#!/usr/bin/env python3
"""Pre-edit screening (v4) of a templated fact set on ANY causal LM. Applies NO edit.

Same procedure, routes, validity rules and output format as screen_facts.py (v1, unchanged for provenance), with:
  * any model: AutoModelForCausalLM / AutoTokenizer and probe_scoring_v4 (BOS and answer tokenisation per tokenizer);
    no EasyEdit import, so screening a model needs no editor hparams;
  * two same-relation neighbour controls per fact instead of one (more side-effect reads per edit), chosen by a hash
    of the two fact ids instead of "first eligible fact in file order" (with hundreds of facts the old rule made a few
    facts everybody's neighbour). Eligibility is v1's: no shared answers with the edit, not the new object's own fact;
    in addition not in the same CounterFact dup_group;
  * dup_group resolution (relation_templates_v3.json design_rules): among INCLUDED facts of one dup_group only the one
    with the highest subject log-probability on a valid reverse_old route stays included (ties: lowest cf_case_id).

Outputs under --output-dir/<tag>/: screen_report.csv, fact_summary.csv, screen_full.jsonl, probes/<fact_id>.json
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_scoring_v4 as ps  # noqa: E402
from screen_facts import FORWARD, REVERSE, decide, judge, load_facts  # noqa: E402

SCREEN_VERSION = "screen_facts_v4 v1.0 (2026-10-31)"
N_NEIGHBOURS = 2


def pick_neighbours(fact, facts, k=N_NEIGHBOURS):
    taken = {fact["target_old"], fact["target_new"]}
    ok = [o for o in facts
          if o["fact_id"] != fact["fact_id"] and o["relation"] == fact["relation"]
          and o["target_old"] not in taken and o["subject"] not in (fact.get("new_alt"), fact["subject"])
          and not (fact.get("dup_group") and o.get("dup_group") == fact["dup_group"])]
    key = lambda o: hashlib.sha256(f"{fact['fact_id']}|{o['fact_id']}".encode()).hexdigest()
    return sorted(ok, key=key)[:k]


def build_probes(fact, facts, templates):
    t = templates["relations"][fact["relation"]]
    s, old, new = fact["subject"], fact["target_old"], fact["target_new"]
    routes = [{"route": name, "kind": "forward", "prompt": t[name].format(subject=s),
               "answers": {"old_object": old, "new_object": new}} for name in FORWARD]
    for name in REVERSE:
        for side, entity, alt in (("old", old, fact.get("old_alt")), ("new", new, fact.get("new_alt"))):
            answers = {"subject": s}
            if alt:
                answers[f"alt:{alt}"] = alt
            routes.append({"route": f"reverse_{side}_{name[len('reverse_'):]}", "kind": f"reverse_{side}",
                           "prompt": t[name].format(entity=entity), "answers": answers})
    if fact.get("new_alt"):
        routes.append({"route": "control_new_object_own_fact", "kind": "control",
                       "prompt": t["forward_edit_prompt"].format(subject=fact["new_alt"]),
                       "answers": {"correct": new, "edit_leak": old}})
    for i, other in enumerate(pick_neighbours(fact, facts), 1):
        routes.append({"route": "control_same_relation" + ("" if i == 1 else f"_{i}"), "kind": "control",
                       "control_fact": other["fact_id"],
                       "prompt": t["forward_edit_prompt"].format(subject=other["subject"]),
                       "answers": {"correct": other["target_old"], "edit_leak": new}})
    edit_prompt = routes[0]["prompt"]
    if s not in edit_prompt:
        raise ValueError(f"{fact['fact_id']}: subject {s!r} not in edit prompt {edit_prompt!r}")
    return {"fact_id": fact["fact_id"], "relation": fact["relation"], "notes": fact.get("notes", ""),
            "source": fact.get("source", ""), "cf_case_id": fact.get("cf_case_id", ""), "dup_group": fact.get("dup_group", ""),
            "cardinality": t.get("cardinality"),
            "edit": {"subject": s, "prompt": edit_prompt, "target_old": old, "target_new": new},
            "routes": routes}


def screen(model, tokenizer, device, facts, templates):
    rules = templates["validity_rules"]
    for fact in facts:
        probes = build_probes(fact, facts, templates)
        scored = {}
        for r in probes["routes"]:
            scored[r["route"]] = ps.probe_prompt(model, tokenizer, r["prompt"], list(r["answers"].items()), device)
            r["valid"], r["deciding_answer"] = judge(r, scored[r["route"]], rules)
        probes["screening"] = decide(probes)
        yield probes, scored


def resolve_dup_groups(results):
    """results: list of (probes, scored). Keeps one included fact per dup_group (see module docstring)."""
    groups = {}
    for p, sc in results:
        if p["dup_group"] and p["screening"]["included"]:
            best = max(sc[r["route"]]["answers"]["subject"]["sum_logprob"]
                       for r in p["routes"] if r["kind"] == "reverse_old" and r["valid"])
            groups.setdefault(p["dup_group"], []).append((-best, int(p["cf_case_id"] or 0), p))
    for g, members in groups.items():
        members.sort(key=lambda x: (x[0], x[1]))
        winner = members[0][2]["fact_id"]
        for _, _, p in members[1:]:
            p["screening"]["included"] = False
            p["screening"]["excluded_by_dup_group"] = winner
    return {g: m[0][2]["fact_id"] for g, m in groups.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", required=True)
    ap.add_argument("--templates", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--tag", default="screen_" + os.environ.get("SLURM_JOB_ID", "local"))
    ap.add_argument("--gpu-mem-gb", type=float, default=float(os.environ.get("GPU_MEM_GB", "0")))
    args = ap.parse_args()

    facts = load_facts(args.facts)
    f_bytes, t_bytes = Path(args.facts).read_bytes(), Path(args.templates).read_bytes()
    templates = json.loads(t_bytes)
    for f in facts:
        if f["relation"] not in templates["relations"]:
            raise ValueError(f"{f['fact_id']}: unknown relation {f['relation']!r}")
    print(SCREEN_VERSION, "|", ps.SCRIPT_VERSION, "|", len(facts), "facts | facts md5", hashlib.md5(f_bytes).hexdigest(),
          "| templates md5", hashlib.md5(t_bytes).hexdigest(), flush=True)
    print("GPU memory:", ps.cap_gpu_memory(args.gpu_mem_gb), flush=True)

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.float32).eval().to("cuda")
    device = next(model.parameters()).device
    src = Path(args.model) / "SOURCE.txt"
    print("model", args.model, "|", type(model).__name__, "| tokenizer", type(tokenizer).__name__, "| BOS prepended:",
          bool(ps.bos_prefix(tokenizer)), "|", src.read_text().replace("\n", " ") if src.exists() else "", flush=True)

    out = Path(args.output_dir) / args.tag
    (out / "probes").mkdir(parents=True, exist_ok=True)
    results = []
    with open(out / "screen_full.jsonl", "w", encoding="utf-8") as full:
        for i, (probes, scored) in enumerate(screen(model, tokenizer, device, facts, templates), 1):
            results.append((probes, scored))
            full.write(json.dumps({"probes": probes, "scored": scored}, ensure_ascii=False) + "\n")
            if i % 25 == 0 or i == len(facts):
                print(f"[{i}/{len(facts)}] screened; included so far {sum(p['screening']['included'] for p, _ in results)}", flush=True)
    winners = resolve_dup_groups(results)
    report, summary = [], []
    for probes, scored in results:
        probes["screened_by"] = {"version": SCREEN_VERSION, "scorer": ps.SCRIPT_VERSION, "model": args.model,
                                 "facts_md5": hashlib.md5(f_bytes).hexdigest(),
                                 "templates_md5": hashlib.md5(t_bytes).hexdigest(), "tag": args.tag}
        with open(out / "probes" / f"{probes['fact_id']}.json", "w", encoding="utf-8") as pf:
            json.dump(probes, pf, ensure_ascii=False, indent=1)
        for r in probes["routes"]:
            s = scored[r["route"]]["answers"][r["deciding_answer"]]
            report.append({"fact_id": probes["fact_id"], "relation": probes["relation"], "route": r["route"],
                           "kind": r["kind"], "prompt": r["prompt"], "deciding_answer": s["answer"],
                           "first_token_rank": s["first_token_rank"], "sequence_probability": s["sequence_probability"],
                           "valid": r["valid"], "greedy_continuation": scored[r["route"]]["greedy_continuation"]})
        summary.append({"fact_id": probes["fact_id"], "relation": probes["relation"], "source": probes["source"],
                        **probes["screening"]})
    for name, rows in (("screen_report.csv", report), ("fact_summary.csv", summary)):
        fields = list(dict.fromkeys(k for r in rows for k in r))
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, restval="")
            w.writeheader()
            w.writerows(rows)
    print(f"dup groups resolved: {len(winners)}", flush=True)
    by_rel = {}
    for s in summary:
        a, b = by_rel.get(s["relation"], (0, 0))
        by_rel[s["relation"]] = (a + s["included"], b + 1)
    for rel, (a, b) in sorted(by_rel.items()):
        print(f"  {rel:20s} included {a:3d} / {b}", flush=True)
    n_in = sum(s["included"] for s in summary)
    print(f"Included {n_in}/{len(summary)} facts. Saved under {out}", flush=True)
    print(f"Peak GPU memory allocated: {ps.gpu_peak_gb()} GiB", flush=True)
    print("SCREEN COMPLETE. Baseline only: no edit was applied.", flush=True)


if __name__ == "__main__":
    main()
