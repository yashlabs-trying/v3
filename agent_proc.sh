#!/bin/bash
C=$(docker ps --format '{{.Names}}' | grep env-main | head -1)
echo "=== container: $C ==="
docker stats --no-stream "$C" 2>&1 | head -3
echo "=== processes inside ==="
docker exec "$C" bash -c "ps aux | grep -E 'mini-swe|python' | grep -v grep | head" 2>&1
echo "=== agent log dir ==="
docker exec "$C" bash -c "ls -la /logs/agent/ 2>/dev/null" 2>&1
