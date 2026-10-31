#!/bin/bash
for J in deepseek-nodebb deepseek-flipt deepseek-vuls; do
  echo "########## $J ##########"
  D=/home/yashs/dataforge/experiments/v3_1_baseline/jobs/$J
  T=$(ls -d "$D"/instance_* 2>/dev/null | head -1)
  echo "trial dir: $T"
  echo "--- exception.txt ---"
  sed -n '1,25p' "$T/exception.txt" 2>/dev/null
  echo "--- trial.log tail 40 ---"
  tail -40 "$T/trial.log" 2>/dev/null
  echo ""
done
