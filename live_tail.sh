#!/bin/bash
C=$(docker ps --format '{{.Names}}' | grep env-main | head -1)
echo "container=$C"
if [ -z "$C" ]; then echo "no container yet"; exit 0; fi
docker exec "$C" bash -c 'wc -c /logs/agent/mini-swe-agent.txt 2>/dev/null; echo "---tail---"; tail -25 /logs/agent/mini-swe-agent.txt 2>/dev/null'
