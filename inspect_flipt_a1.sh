#!/bin/bash
D=/home/yashs/dataforge/experiments/v3_1_baseline/jobs/deepseek2-flipt-a1
T=$(ls -d "$D"/instance_* 2>/dev/null | head -1)
echo "trial: $T"
echo "--- files ---"
find "$T" -type f | sed "s|$T/||" | sort
echo "--- agent dir ---"
ls -la "$T/agent" 2>/dev/null
echo "--- model.patch size ---"
wc -c "$T/agent/model.patch" 2>/dev/null || echo "NO model.patch"
echo "--- verifier reward ---"
cat "$T/verifier/reward.txt" 2>/dev/null; echo
echo "--- verifier output.json ---"
cat "$T/verifier/output.json" 2>/dev/null | head -40
echo "--- trial.log tail 30 ---"
tail -30 "$T/trial.log" 2>/dev/null
