#!/bin/bash
# Section 5 (final): DeepSeek V4.1-Flash, one official attempt per task.
# Audit overlay adds '--with mcp' to the agent install (litellm runtime import fix).
# This changes ONLY the execution harness setup, never the task tests/graders/parsers.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
LOGDIR=/home/yashs/dataforge/experiments/v3_1_baseline/logs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
KEY=$(tr -d '\n' < "$HOME/.dataforge_creds/deepinfra.key")
MODEL="openai/deepseek-ai/DeepSeek-V4.1-Flash"
BASE="https://api.deepinfra.com/v1/openai"

TASKS=(
  "instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan|nodebb"
  "instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f|flipt"
  "instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed|vuls"
  "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866|openlibrary"
  "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d|teleport"
  "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad|ansible"
  "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan|elementweb"
)

for entry in "${TASKS[@]}"; do
  T="${entry%%|*}"
  S="${entry##*|}"
  echo "=== DEEPSEEK-F $S START $(date -u +%H:%M:%S) ==="
  attempt=0
  while [ $attempt -lt 4 ]; do
    attempt=$((attempt+1))
    JOB="deepseekf-$S-a$attempt"
    timeout 5400 harbor run -p v2/tasks -i "$T" -e docker -n 1 \
      -a "locked_mini_swe:LockedMiniSwe" \
      --agent-setup-timeout-multiplier 10 \
      -m "$MODEL" \
      --ak config_file=v2/tooling/configs/mini_toolcall.yaml \
      --ae OPENAI_API_KEY="$KEY" \
      --ae OPENAI_BASE_URL="$BASE" \
      --ae OPENAI_API_BASE="$BASE" \
      --ae UV_HTTP_TIMEOUT=900 \
      --ae PIP_DEFAULT_TIMEOUT=900 \
      --allow-agent-host api.deepinfra.com \
      -o "$OUT" --job-name "$JOB" > "$LOGDIR/$JOB.log" 2>&1
    rc=$?
    # Success = a substantive captured patch OR an agent that actually started (has messages beyond the crash)
    pat=$(ls "$OUT/$JOB"/instance_*/agent/model.patch 2>/dev/null | head -1)
    traj=$(ls "$OUT/$JOB"/instance_*/agent/mini-swe-agent.trajectory.json 2>/dev/null | head -1)
    nmsg=0
    if [ -n "$traj" ]; then
      nmsg=$(python3 -c "import json,sys; d=json.load(open('$traj')); print(len(d.get('messages',[])) if isinstance(d,dict) else len(d))" 2>/dev/null || echo 0)
    fi
    echo "   attempt $attempt rc=$rc patch_bytes=$( [ -n "$pat" ] && wc -c < "$pat" || echo NA ) messages=$nmsg"
    # agent genuinely ran if it exchanged more than the 3 seed messages
    if [ "$nmsg" -gt 3 ]; then
      echo "=== DEEPSEEK-F $S ran (messages=$nmsg) ==="
      break
    fi
    echo "   setup/agent did not start cleanly; retrying"
    for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
  done
  echo "=== DEEPSEEK-F $S DONE $(date -u +%H:%M:%S) ==="
done
echo "ALL_DEEPSEEK_F_DONE"
