#!/bin/bash
D=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/jobs/pilot-deepseek/instance_NodeBB__NodeBB-00c70ce7__Zv6bsm5
echo "=== files ==="
find "$D" -type f
echo ""
echo "=== exception.txt ==="
sed -n '1,40p' "$D/exception.txt" 2>/dev/null
echo ""
echo "=== trial.log (tail 60) ==="
tail -60 "$D/trial.log" 2>/dev/null
