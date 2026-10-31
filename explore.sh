#!/bin/bash
set -e
REPO=/home/yashs/SWE-bench_Pro-os
cd "$REPO"
echo "=== v2/README.md ==="
sed -n '1,120p' v2/README.md
echo ""
echo "=== GATE.md ==="
sed -n '1,120p' v2/GATE.md
echo ""
echo "=== tooling listing ==="
find v2/tooling -maxdepth 2 -type f | sort
echo ""
echo "=== hard51 head ==="
head -10 v2/hard51_ids.txt
echo "hard51 count:"
wc -l v2/hard51_ids.txt
