#!/bin/bash
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
cd "$MIR"
export PYTHONPATH=v2/tooling
KEY=$(cat "$HOME/.dataforge_creds/deepinfra.key")
TASK=instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
MODEL="openai/deepseek-ai/DeepSeek-V4.1-Flash"
BASE="https://api.deepinfra.com/v1/openai"

timeout 3500 harbor run -p v2/tasks -i "$TASK" -e docker -n 1 \
  -a "locked_mini_swe:LockedMiniSwe" \
  --agent-setup-timeout-multiplier 6 \
  -m "$MODEL" \
  --ak config_file=v2/tooling/configs/mini_toolcall.yaml \
  --ae OPENAI_API_KEY="$KEY" \
  --ae OPENAI_BASE_URL="$BASE" \
  --ae OPENAI_API_BASE="$BASE" \
  --allow-agent-host api.deepinfra.com \
  --job-name pilot-deepseek-2 2>&1 | tail -45
echo "HARBOR_EXIT=${PIPESTATUS[0]}"
