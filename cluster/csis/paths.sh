# Sourced by every job on the BITS CSIS cluster (A100). Everything lives under $EA_ROOT:
# nothing is written to $HOME, to shared conda envs, or to other users' folders.
EA_ROOT=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit
export EA_ROOT
export EA_ENV=$EA_ROOT/env                 # conda env (python 3.10), created by setup_env.sbatch
export EA_EASYEDIT=$EA_ROOT/EasyEdit       # EasyEdit at commit 431d9bd; experiments/ -> $EA_REPO/experiments
# $EA_ROOT/repo is a symlink that sync.sh repoints to each new code snapshot. A job must keep the snapshot it
# started with (job 16983 broke when a sync repointed the link mid-run), so resolve it ONCE, here, at job start.
export EA_REPO="$(readlink -f "$EA_ROOT/repo")"
export EA_MODELS=$EA_ROOT/models           # model weights, one directory per model
export EA_HPARAMS=$EA_ROOT/hparams         # hparams as run (model_name pointing into $EA_MODELS)
export HF_HOME=$EA_ROOT/cache/hf
export CONDA_PKGS_DIRS=$EA_ROOT/cache/conda_pkgs
export PIP_CACHE_DIR=$EA_ROOT/cache/pip
export MPLCONFIGDIR=$EA_ROOT/cache/mpl
export NLTK_DATA=$EA_ROOT/cache/nltk
export TMPDIR=$EA_ROOT/cache/tmp
export PYTORCH_ALLOC_CONF="expandable_segments:True"
# Slurm here sets the soft virtual-memory limit (ulimit -v) to half of --mem, which breaks mmap of model weights
# and CUDA's address-space reservations (MemoryError / "failed to map segment" with only ~1.4 GB RSS, job 16972).
# The hard limit is unlimited, so raise the soft limit to it; real RAM is still capped by --mem (cgroup / ulimit -m).
ulimit -S -v "$(ulimit -H -v)"
mkdir -p "$EA_ROOT/logs" "$HF_HOME" "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR" "$MPLCONFIGDIR" "$NLTK_DATA" "$TMPDIR" \
         "$EA_MODELS" "$EA_HPARAMS"

# ea_workdir DIR: make DIR this job's working directory, with the relative paths EasyEdit and the experiment
# scripts use: data/ (statistics, projections: hparams say ./data/stats), hparams/, and experiments/ from THIS
# job's pinned snapshot. EasyEdit also writes logs/run.log relative to it. Never run jobs from $EA_EASYEDIT,
# whose experiments/ link follows the live (repointable) symlink.
ea_workdir() {
  mkdir -p "$1"
  ln -sfn "$EA_EASYEDIT/data" "$1/data"
  ln -sfn "$EA_EASYEDIT/hparams" "$1/hparams"
  ln -sfn "$EA_REPO/experiments" "$1/experiments"
  cd "$1"
  echo "workdir $1 | code snapshot $EA_REPO"
}

source /nfs_home/software/miniconda/etc/profile.d/conda.sh
if [ -d "$EA_ENV/conda-meta" ]; then
  conda activate "$EA_ENV"
  export PYTHONPATH="$EA_EASYEDIT:${PYTHONPATH:-}"
fi
