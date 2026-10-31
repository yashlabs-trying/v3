#!/bin/bash
echo "=== containers ==="
docker ps --format '{{.Names}} {{.Status}}'
echo "=== nodebb log tail ==="
tail -8 /home/yashs/dataforge/experiments/v3_1_baseline/logs/deepseekf-nodebb-a1.log 2>/dev/null
echo "=== active job ==="
ps aux | grep 'harbor run' | grep -v grep | sed -E 's/.*--job-name ([^ ]+).*/\1/' | head -1
