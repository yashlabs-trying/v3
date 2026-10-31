#!/bin/bash
# Section 5: one DeepSeek (V4.1-Flash) coding attempt per selected task, locked protocol.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
LOGDIR=/home/yashs/dataforge/experiments/v3_1_baseline/logs
cd "$MIR"
export PYTHONPATH=v2/tooling
KEY=$(tr -d '\n' < "$HOME/.dataforge_creds/deepinfra.key")
MODEL="openai/deepseek-ai/DeepSeek-V4.1-Flash"
BASE="https://api.deepinfra.com/v1/openai"

TASKS=(
  "instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan"
  "instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f"
  "instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed"
  "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866"
  "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d"
  "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad"
  "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan"
)

SHORT=(
  "nodebb" "flipt" "vuls" "openlibrary" "teleport" "ansible" "elementweb"
)

for i in "${!TASKS[@]}"; do
  T="${TASKS[$i]}"
  S="${SHORT[$i]}"
  echo "=== DEEPSEEK $S $T START $(date -u +%H:%M:%S) ==="
  timeout 4500 harbor run -p v2/tasks -i "$T" -e docker -n 1 \
    -a "locked_mini_swe:LockedMiniSwe" \
    --agent-setup-timeout-multiplier 6 \
    -m "$MODEL" \
    --ak config_file=v2/tooling/configs/mini_toolcall.yaml \
    --ae OPENAI_API_KEY="$KEY" \
    --ae OPENAI_BASE_URL="$BASE" \
    --ae OPENAI_API_BASE="$BASE" \
    --allow-agent-host api.deepinfra.com \
    -o "$OUT" --job-name "deepseek-$S" > "$LOGDIR/deepseek-$S.log" 2>&1
  echo "=== DEEPSEEK $S DONE exit=$? $(date -u +%H:%M:%S) ==="
done
echo "ALL_DEEPSEEK_DONE"
