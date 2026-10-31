#!/bin/bash
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
echo "=== mini_toolcall.yaml ==="
cat "$MIR/v2/tooling/configs/mini_toolcall.yaml"
echo ""
echo "=== mini_textbased.yaml ==="
cat "$MIR/v2/tooling/configs/mini_textbased.yaml"
echo ""
echo "=== locked_mini_swe.py full ==="
cat "$MIR/v2/tooling/locked_mini_swe.py"
