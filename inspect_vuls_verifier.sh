#!/bin/bash
D=/home/yashs/dataforge/experiments/v3_1_baseline/jobs/f3-vuls-a1
T=$(ls -d "$D"/instance_* | head -1)
echo "trial=$T"
echo "=== output.json ==="
cat "$T/verifier/output.json" | head -80
echo ""
echo "=== raw go test lines mentioning SortByConfident ==="
grep -n 'SortByConfident' "$T/verifier/run-script-stdout.txt" | head
echo "=== all --- FAIL lines ==="
grep -nE -- '--- FAIL' "$T/verifier/run-script-stdout.txt" | head
echo "=== all --- PASS lines count ==="
grep -cE -- '--- PASS' "$T/verifier/run-script-stdout.txt"
