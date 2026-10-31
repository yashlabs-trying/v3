#!/bin/bash
# Repeat-control stability: run the flipt ORACLE 2 more times and compare verdicts.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
LOGDIR=/home/yashs/dataforge/experiments/v3_1_baseline/logs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
T=instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f
for i in 2 3; do
  echo "=== REPEAT-CONTROL flipt-oracle run $i START $(date -u +%H:%M:%S) ==="
  timeout 1800 harbor run -p v2/tasks -i "$T" -e docker -n 1 -a oracle \
    -o "$OUT" --job-name "repeat-oracle-flipt-$i" > "$LOGDIR/repeat-oracle-flipt-$i.log" 2>&1
  echo "=== REPEAT-CONTROL flipt-oracle run $i DONE rc=$? $(date -u +%H:%M:%S) ==="
  for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
done
echo "ALL_REPEAT_DONE"
