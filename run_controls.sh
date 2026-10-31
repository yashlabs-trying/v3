#!/bin/bash
# Pre-run validation: oracle + no-op controls for the 7 selected tasks.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
LOGDIR=/home/yashs/dataforge/experiments/v3_1_baseline/logs
mkdir -p "$OUT" "$LOGDIR"
cd "$MIR"
export PYTHONPATH=v2/tooling

TASKS=(
  "instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan"
  "instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f"
  "instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed"
  "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866"
  "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d"
  "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad"
  "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan"
)

echo "=== pulling images ==="
for T in "${TASKS[@]}"; do
  IMG="ghcr.io/scaleapi/swe-bench_pro-v2:$T"
  if docker image inspect "$IMG" >/dev/null 2>&1; then
    echo "already: $T"
  else
    echo "pulling: $T"
    timeout 2400 docker pull "$IMG" > "$LOGDIR/pull_$T.log" 2>&1 && echo "  ok" || echo "  PULL_FAILED"
  fi
done

run_job() {
  local task="$1" agent="$2" name="$3"
  echo "=== $agent on $task ==="
  timeout 3600 harbor run -p v2/tasks -i "$task" -e docker -n 1 \
    -a "$agent" --agent-setup-timeout-multiplier 6 \
    -o "$OUT" --job-name "$name" > "$LOGDIR/${name}.log" 2>&1
  echo "  exit=$?"
}

for T in "${TASKS[@]}"; do
  run_job "$T" oracle "ctrl-oracle-${T:0:40}"
  run_job "$T" nop    "ctrl-nop-${T:0:40}"
done

echo "ALL_CONTROLS_DONE"
