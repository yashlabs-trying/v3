#!/bin/bash
# Quick validation: DeepSeek via Harbor on flipt with the two fixes, short budget.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
AUD=/home/yashs/dataforge/experiments/v3_1_baseline/audit_tasks
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
MODEL="openai/deepseek-ai/DeepSeek-V4.1-Flash"
BASE="https://api.deepinfra.com/v1/openai"
T=instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f
timeout 1500 harbor run -p "$AUD" -i "$T" -e docker -n 1 \
  -a "locked_mini_swe:LockedMiniSwe" \
  --agent-setup-timeout-multiplier 6 \
  --agent-timeout-multiplier 0.15 \
  -m "$MODEL" \
  --ak config_file=v2/tooling/configs/mini_toolcall.yaml \
  --ae OPENAI_API_KEY="$KEY" \
  --ae OPENAI_BASE_URL="$BASE" \
  --ae OPENAI_API_BASE="$BASE" \
  --ae MSWEA_CONFIGURED=true \
  --ae UV_HTTP_TIMEOUT=1800 \
  --allow-agent-host api.deepinfra.com \
  -o "$OUT" --job-name val-flipt 2>&1 | tail -18
