#!/bin/bash
set -e
cd /home/yashs/dataforge/experiments/v3_1_baseline
git init -q
git config user.email "dataforge@local"
git config user.name "DataForge Audit"
git add -A
echo "=== staged file count ==="
git diff --cached --numstat | wc -l
echo "=== staged size (approx) ==="
git diff --cached --numstat | awk '{s+=$1+$2} END {print s" lines"}'
echo "=== confirm upstream_lf excluded ==="
git diff --cached --name-only | grep -c '^upstream_lf/' || true
echo "=== confirm no key file staged ==="
git diff --cached --name-only | grep -iE 'deepinfra.key|auth.json' || echo "none"
git commit -q -m "DataForge V3.1 Phase 1A: SWE-bench Pro V2 baseline reliability audit (DeepSeek V4.1-Flash)"
echo "=== commit done ==="
git log --oneline -1
git rev-parse HEAD
