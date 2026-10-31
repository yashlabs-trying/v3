#!/bin/bash
D=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/jobs/pilot-deepseek-2
T=$(echo "$D"/instance_*)
echo "=== reward.txt ==="
cat "$T/verifier/reward.txt"; echo
echo "=== output.json ==="
cat "$T/verifier/output.json"; echo
echo "=== run-script-stdout.txt ==="
cat "$T/verifier/run-script-stdout.txt"
echo "=== run-script-stderr.txt ==="
cat "$T/verifier/run-script-stderr.txt"
echo "=== test-stdout.txt ==="
cat "$T/verifier/test-stdout.txt"
echo "=== model.patch stat ==="
head -5 "$T/agent/model.patch"
echo "..."
grep -c '^diff --git' "$T/agent/model.patch"
echo "files changed"
