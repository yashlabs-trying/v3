#!/bin/bash
echo "=== sidecar container ==="
SIDECAR=$(docker ps --format '{{.Names}}' | grep sidecar | head -1)
echo "sidecar=$SIDECAR"
if [ -n "$SIDECAR" ]; then
  docker logs "$SIDECAR" 2>&1 | tail -30
fi
echo "=== agent container network test to deepinfra (via sidecar) ==="
C=$(docker ps --format '{{.Names}}' | grep env-main | head -1)
echo "agent=$C"
docker exec "$C" bash -lc "timeout 20 curl -sS -o /dev/null -w 'deepinfra via sidecar: %{http_code} %{time_total}s\n' https://api.deepinfra.com/v1/openai/models 2>&1" 2>&1
