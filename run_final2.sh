#!/bin/bash
# Robust final runner: one official attempt per task; infrastructure stalls (no trajectory)
# are retried and each attempt preserved. First non-stalled attempt is the counted one.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
AUD=/home/yashs/dataforge/experiments/v3_1_baseline/audit_tasks
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
LOGDIR=/home/yashs/dataforge/experiments/v3_1_baseline/logs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
MODEL="openai/deepseek-ai/DeepSeek-V4.1-Flash"
BASE="https://api.deepinfra.com/v1/openai"

# task|short|already_counted_job(optional)
TASKS=(
  "instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed|vuls"
  "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866|openlibrary"
  "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d|teleport"
  "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad|ansible"
  "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan|elementweb"
)

run_one() {
  local T="$1" S="$2" A="$3"
  local JOB="final2-$S-a$A"
  echo "=== $S attempt $A START $(date -u +%H:%M:%S) ==="
  timeout 5400 harbor run -p "$AUD" -i "$T" -e docker -n 1 \
    -a "locked_mini_swe:LockedMiniSwe" \
    --agent-setup-timeout-multiplier 6 \
    --agent-timeout-multiplier 0.3 \
    -m "$MODEL" \
    --ak config_file=v2/tooling/configs/mini_toolcall.yaml \
    --ae OPENAI_API_KEY="$KEY" \
    --ae OPENAI_BASE_URL="$BASE" \
    --ae OPENAI_API_BASE="$BASE" \
    --ae MSWEA_CONFIGURED=true \
    --ae MSWEA_COST_TRACKING=ignore_errors \
    --ae UV_HTTP_TIMEOUT=1800 \
    --ae PIP_DEFAULT_TIMEOUT=1800 \
    --allow-agent-host api.deepinfra.com \
    -o "$OUT" --job-name "$JOB" > "$LOGDIR/$JOB.log" 2>&1
  local rc=$?
  # detect stall: trajectory message count
  local trj nmsg
  trj=$(ls "$OUT/$JOB"/instance_*/agent/mini-swe-agent.trajectory.json 2>/dev/null | head -1)
  nmsg=0
  [ -n "$trj" ] && nmsg=$(python3 -c "import json;d=json.load(open('$trj'));print(len(d.get('messages',[])))" 2>/dev/null || echo 0)
  echo "=== $S attempt $A DONE rc=$rc msgs=$nmsg $(date -u +%H:%M:%S) ==="
  for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
  echo "$nmsg" > /tmp/last_nmsg
}

for entry in "${TASKS[@]}"; do
  T="${entry%%|*}"; rest="${entry#*|}"; S="${rest%%|*}"
  if ! docker image inspect "dataforge-agent:$T" >/dev/null 2>&1; then
    echo "=== SKIP $S (no agent image) ==="; continue
  fi
  # skip if a counted attempt already yielded a trajectory
  done_job=$(ls -d "$OUT"/final2-$S-a* 2>/dev/null | while read d; do trj=$(ls "$d"/instance_*/agent/mini-swe-agent.trajectory.json 2>/dev/null | head -1); [ -n "$trj" ] && n=$(python3 -c "import json;print(len(json.load(open('$trj')).get('messages',[])))" 2>/dev/null||echo 0); [ "${n:-0}" -gt 3 ] && echo "$d"; done | head -1)
  if [ -n "$done_job" ]; then echo "=== SKIP $S (already has ran-attempt) ==="; continue; fi
  attempt=0
  while [ $attempt -lt 4 ]; do
    attempt=$((attempt+1))
    run_one "$T" "$S" "$attempt"
    nmsg=$(cat /tmp/last_nmsg 2>/dev/null || echo 0)
    [ "$nmsg" -gt 3 ] && break
    echo "  $S stalled (msgs=$nmsg); retrying"
  done
done
echo "ALL_FINAL2_DONE"
