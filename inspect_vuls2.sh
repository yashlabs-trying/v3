#!/bin/bash
T=/home/yashs/dataforge/experiments/v3_1_baseline/jobs/f3-vuls-a1/instance_future-architect__vuls__sNqH5s4
echo "=== files in verifier ==="
ls -la "$T/verifier/"
echo "=== SortByConfident in output.json ==="
grep -n 'SortByConfident' "$T/verifier/output.json" || echo "NOT PRESENT in output.json"
echo "=== SortByConfident anywhere in verifier dir ==="
grep -rn 'SortByConfident' "$T/verifier/" 2>&1 | head
echo "=== FAIL lines in run-script-stdout ==="
grep -nE -- '--- FAIL' "$T/verifier/run-script-stdout.txt" 2>&1 | head -20
echo "=== PASS count / FAIL count ==="
grep -cE -- '--- PASS' "$T/verifier/run-script-stdout.txt" 2>&1
grep -cE -- '--- FAIL' "$T/verifier/run-script-stdout.txt" 2>&1
echo "=== tail of run-script-stdout ==="
tail -30 "$T/verifier/run-script-stdout.txt" 2>&1
