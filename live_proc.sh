#!/bin/bash
C=$(docker ps --format '{{.Names}}' | grep env-main | head -1)
echo "container=$C"
docker stats --no-stream "$C" 2>&1 | tail -2
echo "=== agent proc ==="
docker exec "$C" bash -c "ps -eo pid,etime,pcpu,comm | grep -E 'mini|python' | grep -v grep" 2>&1 | head
echo "=== log dir ==="
docker exec "$C" bash -c "ls -la /logs/agent/ 2>/dev/null" 2>&1
