#!/bin/bash
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
mkdir -p "$OUT"
cd "$MIR"
export PYTHONPATH=v2/tooling
TASK=instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
timeout 3000 harbor run -p v2/tasks -i "$TASK" -e docker -n 1 -a oracle -o "$OUT" --job-name smoke-oracle-lf 2>&1 | tail -35
echo "HARBOR_EXIT=${PIPESTATUS[0]}"
