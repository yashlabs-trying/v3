#!/bin/bash
# FINAL runner v3: audit config (stream=false, timeout=120, num_retries=3) fixes the stall.
# Full agent budget. Stall-retry preserved.
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
CFG="$OVL/mini_toolcall_audit.yaml"

TASKS=(
  "instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed|vuls"
  "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866|openlibrary"
  "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d|teleport"
  "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad|ansible"
  "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan|elementweb"
)

for entry in "${TASKS[@]}"; do
  T="${entry%%|*}"; S="${entry##*|}"
  docker image inspect "dataforge-agent:$T" >/dev/null 2>&1 || { echo "=== SKIP $S (no image) ==="; continue; }
  # skip if already produced a trajectory-based run
  have=$(ls -d "$OUT"/f3-$S-a* 2>/dev/null | while read d; do trj=$(ls "$d"/instance_*/agent/mini-swe-agent.trajectory.json 2>/dev/null|head -1); [ -n "$trj" ] && n=$(python3 -c "import json;print(len(json.load(open('$trj')).get('messages',[])))" 2>/dev/null||echo 0); [ "${n:-0}" -gt 3 ] && echo x; done | head -1)
  [ -n "$have" ] && { echo "=== SKIP $S (done) ==="; continue; }
  attempt=0
  while [ $attempt -lt 4 ]; do
    attempt=$((attempt+1))
    JOB="f3-$S-a$attempt"
    echo "=== $S attempt $attempt START $(date -u +%H:%M:%S) ==="
    timeout 5400 harbor run -p "$AUD" -i "$T" -e docker -n 1 \
      -a "locked_mini_swe:LockedMiniSwe" \
      --agent-setup-timeout-multiplier 6 \
      -m "$MODEL" \
      --ak config_file="$CFG" \
      --ae OPENAI_API_KEY="$KEY" \
      --ae OPENAI_BASE_URL="$BASE" --ae OPENAI_API_BASE="$BASE" \
      --ae UV_HTTP_TIMEOUT=1800 --ae PIP_DEFAULT_TIMEOUT=1800 \
      --allow-agent-host api.deepinfra.com \
      -o "$OUT" --job-name "$JOB" > "$LOGDIR/$JOB.log" 2>&1
    rc=$?
    trj=$(ls "$OUT/$JOB"/instance_*/agent/mini-swe-agent.trajectory.json 2>/dev/null|head -1)
    nmsg=0; [ -n "$trj" ] && nmsg=$(python3 -c "import json;print(len(json.load(open('$trj')).get('messages',[])))" 2>/dev/null||echo 0)
    echo "=== $S attempt $attempt DONE rc=$rc msgs=$nmsg $(date -u +%H:%M:%S) ==="
    for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
    [ "$nmsg" -gt 3 ] && break
    echo "  $S stalled; retrying"
  done
done
echo "ALL_F3_DONE"
