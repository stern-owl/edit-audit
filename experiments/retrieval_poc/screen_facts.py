#!/usr/bin/env python3
"""Pre-edit screening of a templated fact set. Applies NO edit.

For every fact: builds its routes from relation_templates.json (same wording for every fact of a
relation), scores them with probe_scoring, judges each route against the fixed validity rules,
decides inclusion, and writes one probe file per fact for the later paired ROME runs.

Outputs under --output-dir/<tag>/:
  screen_report.csv     one row per (fact, route): the deciding answer, its rank/probability, valid?
  fact_summary.csv      one row per fact: valid route counts and the inclusion decision
  screen_full.jsonl     everything scored
  probes/<fact_id>.json probe file per fact (routes + validity), same format as the frozen pilot file
"""
import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_scoring import SCRIPT_VERSION, cap_gpu_memory, gpu_peak_gb, probe_prompt  # noqa: E402

SCREEN_VERSION = "screen_facts v1 (2026-10-24)"
FORWARD = ["forward_edit_prompt", "paraphrase_statement", "paraphrase_question", "contextual"]
REVERSE = ["reverse_most_famous", "reverse_best_known"]


def load_facts(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]
    ids = [r["fact_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fact_id in " + path)
    return rows


def pick_other(fact, facts):
    """Same-relation control fact whose answers cannot collide with this edit."""
    taken = {fact["target_old"], fact["target_new"]}
    for o in facts:
        if (o["fact_id"] != fact["fact_id"] and o["relation"] == fact["relation"]
                and o["target_old"] not in taken and o["subject"] not in (fact["new_alt"], fact["subject"])):
            return o
    return None


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
    other = pick_other(fact, facts)
    if other:
        routes.append({"route": "control_same_relation", "kind": "control", "control_fact": other["fact_id"],
                       "prompt": t["forward_edit_prompt"].format(subject=other["subject"]),
                       "answers": {"correct": other["target_old"], "edit_leak": new}})
    edit_prompt = routes[0]["prompt"]
    if s not in edit_prompt:
        raise ValueError(f"{fact['fact_id']}: subject {s!r} not in edit prompt {edit_prompt!r} (ROME needs it)")
    return {"fact_id": fact["fact_id"], "relation": fact["relation"], "notes": fact.get("notes", ""),
            "edit": {"subject": s, "prompt": edit_prompt, "target_old": old, "target_new": new},
            "routes": routes}


def judge(route, scored, rules):
    """Return (valid, deciding answer label) under the fixed rules."""
    a = scored["answers"]
    kind = route["kind"]
    if kind == "forward":
        return a["old_object"]["first_token_rank"] <= rules["forward_old_first_token_rank_max"], "old_object"
    if kind == "reverse_old":
        return a["subject"]["first_token_rank"] <= rules["reverse_old_subject_first_token_rank_max"], "subject"
    if kind == "reverse_new":
        return a["subject"]["first_token_rank"] >= rules["reverse_new_subject_first_token_rank_min"], "subject"
    if kind == "control":
        return a["correct"]["first_token_rank"] <= rules["control_correct_first_token_rank_max"], "correct"
    raise ValueError(kind)


def decide(probes):
    v = {r["route"]: r["valid"] for r in probes["routes"]}
    kinds = {k: sum(r["valid"] for r in probes["routes"] if r["kind"] == k) for k in ("reverse_old", "reverse_new", "control")}
    other_fwd = sum(v[n] for n in FORWARD[1:])
    included = v["forward_edit_prompt"] and other_fwd >= 2 and all(kinds[k] >= 1 for k in kinds)
    return {"edit_prompt_valid": v["forward_edit_prompt"], "other_forward_valid": other_fwd,
            "reverse_old_valid": kinds["reverse_old"], "reverse_new_valid": kinds["reverse_new"],
            "control_valid": kinds["control"], "included": included}


def screen(model, tokenizer, device, facts, templates):
    rules = templates["validity_rules"]
    for fact in facts:
        probes = build_probes(fact, facts, templates)
        scored = {}
        for r in probes["routes"]:
            scored[r["route"]] = probe_prompt(model, tokenizer, r["prompt"], list(r["answers"].items()), device)
            r["valid"], r["deciding_answer"] = judge(r, scored[r["route"]], rules)
        probes["screening"] = decide(probes)
        yield probes, scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", default="experiments/retrieval_poc/candidate_facts_v2.csv")
    ap.add_argument("--templates", default="experiments/retrieval_poc/relation_templates.json")
    ap.add_argument("--output-dir", default="experiments/retrieval_poc/results")
    ap.add_argument("--tag", default="screen_" + os.environ.get("SLURM_JOB_ID", "local"))
    ap.add_argument("--model", default="/localstorage/home/f20220930/EasyEdit/huggingface_cache/gpt2-xl")
    ap.add_argument("--hparams", default="./hparams/ROME/gpt2-xl")
    ap.add_argument("--gpu-mem-gb", type=float, default=float(os.environ.get("GPU_MEM_GB", "12")))
    args = ap.parse_args()

    facts = load_facts(args.facts)
    t_bytes = Path(args.templates).read_bytes()
    templates = json.loads(t_bytes)
    for f in facts:
        if f["relation"] not in templates["relations"]:
            raise ValueError(f"{f['fact_id']}: unknown relation {f['relation']!r}")
    print(SCREEN_VERSION, "|", SCRIPT_VERSION, "|", len(facts), "facts | templates md5",
          hashlib.md5(t_bytes).hexdigest(), flush=True)
    print("GPU memory:", cap_gpu_memory(args.gpu_mem_gb), flush=True)

    from easyeditor import BaseEditor, ROMEHyperParams
    from transformers import GPT2Tokenizer
    hparams = ROMEHyperParams.from_hparams(args.hparams)
    tokenizer = GPT2Tokenizer.from_pretrained(args.model)
    model = BaseEditor.from_hparams(hparams).model
    model.eval()
    device = next(model.parameters()).device
    if device.type != "cuda":
        raise RuntimeError("Model not on CUDA")

    out = Path(args.output_dir) / args.tag
    (out / "probes").mkdir(parents=True, exist_ok=True)
    report, summary = [], []
    with open(out / "screen_full.jsonl", "w", encoding="utf-8") as full:
        for i, (probes, scored) in enumerate(screen(model, tokenizer, device, facts, templates), 1):
            probes["screened_by"] = {"version": SCREEN_VERSION, "scorer": SCRIPT_VERSION,
                                     "templates_md5": hashlib.md5(t_bytes).hexdigest(), "tag": args.tag}
            with open(out / "probes" / f"{probes['fact_id']}.json", "w", encoding="utf-8") as pf:
                json.dump(probes, pf, ensure_ascii=False, indent=1)
            full.write(json.dumps({"probes": probes, "scored": scored}, ensure_ascii=False) + "\n")
            for r in probes["routes"]:
                s = scored[r["route"]]["answers"][r["deciding_answer"]]
                report.append({"fact_id": probes["fact_id"], "relation": probes["relation"], "route": r["route"],
                               "kind": r["kind"], "prompt": r["prompt"], "deciding_answer": s["answer"],
                               "first_token_rank": s["first_token_rank"],
                               "sequence_probability": s["sequence_probability"], "valid": r["valid"],
                               "greedy_continuation": scored[r["route"]]["greedy_continuation"]})
            summary.append({"fact_id": probes["fact_id"], "relation": probes["relation"], **probes["screening"]})
            print(f"[{i}/{len(facts)}] {probes['fact_id']}: included={probes['screening']['included']}", flush=True)
    for name, rows in (("screen_report.csv", report), ("fact_summary.csv", summary)):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    n_in = sum(s["included"] for s in summary)
    print(f"Included {n_in}/{len(summary)} facts. Saved under {out}", flush=True)
    print(f"Peak GPU memory allocated: {gpu_peak_gb()} GiB (cap {args.gpu_mem_gb} GiB)", flush=True)
    print("Baseline only: no edit was applied.", flush=True)


if __name__ == "__main__":
    main()
