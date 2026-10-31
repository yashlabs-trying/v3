#!/bin/bash
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
REPO=/home/yashs/SWE-bench_Pro-os
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
mkdir -p "$OUT"
cd "$REPO"
export PYTHONPATH=v2/tooling
TASK=instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
timeout 2400 harbor run -p v2/tasks -i "$TASK" -e docker -n 1 -a oracle -o "$OUT" --job-name smoke-oracle 2>&1 | tail -50
echo "HARBOR_EXIT=${PIPESTATUS[0]}"
