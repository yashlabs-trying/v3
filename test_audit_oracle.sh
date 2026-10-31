#!/bin/bash
# Validate: oracle control against the audit overlay (pre-baked agent image).
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
AUD=/home/yashs/dataforge/experiments/v3_1_baseline/audit_tasks
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"
T=instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f
timeout 1800 harbor run -p "$AUD" -i "$T" -e docker -n 1 -a oracle \
  -o "$OUT" --job-name audit-oracle-flipt 2>&1 | tail -20
