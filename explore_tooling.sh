#!/bin/bash
REPO=/home/yashs/SWE-bench_Pro-os
cd "$REPO"
echo "=== tooling/bin/README.md ==="
cat v2/tooling/bin/README.md
echo ""
echo "=== patch_replay.py (head 120) ==="
sed -n '1,120p' v2/tooling/patch_replay.py
echo ""
echo "=== locked_mini_swe.py head ==="
sed -n '1,80p' v2/tooling/locked_mini_swe.py
