#!/bin/bash
# NodeBB INFRASTRUCTURE-RECOVERY RERUN (separately labeled; NOT counted as the original attempt).
# Uses the corrected launcher (audit config). Original final-nodebb evidence is untouched.
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
T=instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
echo "=== NODEBB RECOVERY RERUN START $(date -u +%H:%M:%S) ==="
timeout 5400 harbor run -p "$AUD" -i "$T" -e docker -n 1 \
  -a "locked_mini_swe:LockedMiniSwe" \
  --agent-setup-timeout-multiplier 6 \
  -m "openai/deepseek-ai/DeepSeek-V4.1-Flash" \
  --ak config_file="$OVL/mini_toolcall_audit.yaml" \
  --ae OPENAI_API_KEY="$KEY" \
  --ae OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai \
  --ae OPENAI_API_BASE=https://api.deepinfra.com/v1/openai \
  --ae UV_HTTP_TIMEOUT=1800 \
  --allow-agent-host api.deepinfra.com \
  -o "$OUT" --job-name "nodebb-recovery" > "$LOGDIR/nodebb-recovery.log" 2>&1
echo "=== NODEBB RECOVERY RERUN DONE rc=$? $(date -u +%H:%M:%S) ==="
