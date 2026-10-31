#!/bin/bash
# FINAL: DeepSeek V4.1-Flash, one official attempt per task, locked protocol.
# Fixes applied (harness setup only, NOT benchmark): MSWEA_CONFIGURED=true (skip 2.4.6 wizard),
# clean API key, pre-baked agent image.
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

# task|short  (order: user wants first 3 = nodebb, flipt, vuls)
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
  T="${entry%%|*}"; S="${entry##*|}"
  if ! docker image inspect "dataforge-agent:$T" >/dev/null 2>&1; then
    echo "=== SKIP $S (agent image missing) ==="; continue
  fi
  JOB="final-$S"
  if ls "$OUT/$JOB"/instance_*/result.json >/dev/null 2>&1; then
    echo "=== SKIP $S (already ran) ==="; continue
  fi
  echo "=== FINAL $S START $(date -u +%H:%M:%S) ==="
  timeout 5400 harbor run -p "$AUD" -i "$T" -e docker -n 1 \
    -a "locked_mini_swe:LockedMiniSwe" \
    --agent-setup-timeout-multiplier 6 \
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
  echo "=== FINAL $S DONE rc=$? $(date -u +%H:%M:%S) ==="
  for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
done
echo "ALL_FINAL_DONE"
