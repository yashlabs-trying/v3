#!/bin/bash
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
AUD=/home/yashs/dataforge/experiments/v3_1_baseline/audit_tasks
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
BASE="https://api.deepinfra.com/v1/openai"
T=instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
timeout 1500 harbor run -p "$AUD" -i "$T" -e docker -n 1 \
  -a "locked_mini_swe:LockedMiniSwe" \
  --agent-setup-timeout-multiplier 6 --agent-timeout-multiplier 0.3 \
  -m "openai/deepseek-ai/DeepSeek-V4.1-Flash" \
  --ak config_file=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay/mini_toolcall_audit.yaml \
  --ae OPENAI_API_KEY="$KEY" --ae OPENAI_BASE_URL="$BASE" --ae OPENAI_API_BASE="$BASE" \
  --ae UV_HTTP_TIMEOUT=1800 --allow-agent-host api.deepinfra.com \
  -o "$OUT" --job-name "auditcfg-vuls" 2>&1 | tail -8
