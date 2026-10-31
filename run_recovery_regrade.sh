#!/bin/bash
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
T=instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
timeout 3000 harbor run -p v2/tasks -i "$T" -e docker -n 1 \
  -a "patch_replay:PatchReplayAgent" -m replay \
  --ak source_job="$OUT/nodebb-recovery" \
  -o "$OUT" --job-name "regrade-nodebb-recovery" 2>&1 | tail -12
