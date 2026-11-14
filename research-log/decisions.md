# Decisions

Each decision: ID, date raised, question, options, status, outcome, reason.

## D1: Venue and scope
- **Raised:** 2026-10-31
- **Question:** Keep the PVLDB Vision track, or expand to a research-track paper?
- **Options:** (a) Vision: strengthen with phase 1 and a slice of phase 2. (b) Research track: phases 1–4 at the scale in `next-steps.txt` §5.
- **Status:** deferred by the user ("we will finalize the venue and draft the paper later").
- **Consequence for now:** work proceeds in plan order; phases 1–2 serve both options.

## D2: Which cluster account runs the jobs
- **Raised:** 2026-10-31
- **Finding:** This laptop's `~/.ssh/config` has host `bits-cluster` (172.24.16.132), commented "CalibRead / BITS GPU cluster", user `yashsinha`, key `~/.ssh/id_ed25519`. Passwordless login works. It is the CSIS cluster (Dell R7525, NVIDIA A100), Slurm, login node `csis.mn1`, compute nodes `csis.cn[1-4]`; GPU partitions `gpu-short` (8 h), `gpu-long` (12 h), `gpu-1day`, `gpu-3day`, `test-gpu` (7 days).
- **Concern:** the account appears to belong to Prof. Yash Sinha and the config label points at another project (CalibRead). The original runs used a different cluster (`h100-mig` partition, home `/localstorage/home/f20220930`, Yash Aggarwal).
- **Status:** **settled 2026-10-31.** The user confirmed the `yashsinha` account and gave the working path.
- **Outcome / rules from the user:**
  - All code, data, logs and results go inside `/nfs_home/users/yashsinha/F20220612_Aadit` (this project: `.../F20220612_Aadit/edit-audit/`).
  - Login node only for editing files and submitting jobs; all CPU/GPU-heavy work through Slurm.
  - Do not modify other users' folders, shared environments or system packages without asking.
  - Existing content of `F20220612_Aadit/` (`calibread/`, `steering_pilot*/`, `venv/`, `hf_cache/`, `ollama_models/`, `bin/`, `lib/`, `logs/`, `fen_analysis.csv`) belongs to other work and is not touched.
- **Credentials:** SSH key auth from the laptop works, so no password is used or stored anywhere in this log, the repo, or the scripts.

## D3: Keep shipped artefact byte-identical; work on a branch
- **Raised / settled:** 2026-10-31
- **Outcome:** all new work is on git branch `phase2` of the user's fork (`origin` = github.com/AaditS04/edit-audit, `upstream` = github.com/stern-owl/edit-audit). Colleague's `slurm/` scripts are left as they are for provenance; CSIS-specific scripts live in `cluster/csis/`. Nothing committed or pushed yet.

## D4: Modern model (plan 2.5)
- **Raised:** 2026-10-31. Llama-3-8B (gated: Meta approval + HF token) vs Qwen2.5-7B (open; covariance statistics must be computed).
- **Status:** open, waiting for the user.

## D5: No re-runs; freeze v3; one seed for large runs
- **Raised / settled:** 2026-10-31 ~02:10, by the user: "I don't want to waste much time on reruns, and want to test new things."
- **Outcome:** the v3 fact set, templates and screening stay frozen (the revision proposed in entry 06 is not applied; its
  findings become stated limitations). New large runs use seed 0 only (seeds agreed closely in the draft and E0).
  Priority goes to new experiments: v3 audit at scale (E4), sequential editing (E7), GPT-J (E5).

## D5 · Publishing the phase-2 work (2026-11-14) · settled
- **Options:** PR in the own fork vs in the original repo (stern-owl/edit-audit); code only vs code + research log vs
  code + log + raw runs; given the fork is public: new private repo vs public fork.
- **Outcome (user):** PR in the own fork AaditS04/edit-audit (PR #1), with code, research log and `data/raw_runs/`, on
  the public fork, accepting that unpublished results, novelty notes and cluster details become public.
- **Excluded (gitignored):** `next-steps.txt`, the draft PDF, `data/counterfact/`, `data/cluster_mirror/`, weights.
  Commits authored by the user only; no tool attribution.
- **2026-11-14, later:** branch renamed `csis-phase2` → `phase2` (GitHub rename; local branch tracks `origin/phase2`).
  PR #1 was merged into the fork's `main` (merge commit 83ff6c4, 14:52 IST) by an assistant `gh pr merge` call that the
  user had meant to stop (the tool reported it as rejected, but it had run). The user then synced `stern-owl:main` into
  the branch (d595a08). Next: PR from `AaditS04:phase2` into `stern-owl/edit-audit` main (user has read access only
  there; Yash Aggarwal merges).
