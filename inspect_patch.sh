#!/bin/bash
P=$(ls -d /home/yashs/dataforge/experiments/v3_1_baseline/jobs/ds-nodebb-a1/instance_*/agent/model.patch | head -1)
echo "=== patch file summary ==="
wc -c "$P"
echo "=== diff --git lines ==="
grep '^diff --git' "$P"
echo "=== new file / deleted file lines ==="
grep -E '^(new file|deleted file|Binary files)' "$P" | head -30
echo "=== source files changed (.js) ==="
grep '^diff --git' "$P" | grep -E '\.js' | head -40
