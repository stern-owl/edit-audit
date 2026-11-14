#!/bin/bash
# Run on the laptop: copy this repo's working tree (including uncommitted changes) to the cluster as a NEW
# snapshot $EA_ROOT/repo_snapshots/<timestamp>/, then atomically repoint the symlink $EA_ROOT/repo at it.
#
# Why snapshots: bash reads a running script from its file in chunks. Re-extracting files in place while a job
# runs can truncate a script under bash, which then sees end-of-file and exits 0 without running the rest
# (this cut reproduce.sh short in job 16978). With snapshots, a running job keeps the files it started with;
# only jobs submitted after the sync see the new code. Old snapshots are small and are kept for provenance.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
ROOT=/nfs_home/users/yashsinha/F20220612_Aadit/edit-audit
HOST="${HOST:-bits-cluster}"
COMMIT="$(git -C "$REPO" rev-parse HEAD)"
DIRTY="$(git -C "$REPO" status --porcelain | wc -l | tr -d ' ')"
TS="$(date +%Y%m%d-%H%M%S)"
SNAP=$ROOT/repo_snapshots/$TS
tar -C "$REPO" --exclude=.git --exclude=__pycache__ --exclude=results_rerun -czf - . \
  | ssh -o ConnectTimeout=15 "$HOST" "set -e; mkdir -p $SNAP && tar -C $SNAP -xzf - && \
      printf 'commit %s\nuncommitted_files %s\nsynced %s\nsnapshot %s\n' $COMMIT $DIRTY \"\$(date -Is)\" $SNAP > $SNAP/SYNCED_FROM.txt && \
      if [ -d $ROOT/repo ] && [ ! -L $ROOT/repo ]; then echo 'repo/ is a plain directory: run the one-time migration first' >&2; exit 3; fi && \
      ln -sfn $SNAP $ROOT/repo.tmp && mv -T $ROOT/repo.tmp $ROOT/repo && cat $ROOT/repo/SYNCED_FROM.txt"
