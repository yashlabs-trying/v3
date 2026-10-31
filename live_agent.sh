#!/bin/bash
# tail live agent transcript from the running container
C=$(docker ps --format '{{.Names}}' | grep env-main | head -1)
echo "container: $C"
docker exec "$C" bash -c "cat /logs/agent/mini-swe-agent.txt 2>/dev/null | tail -55" 2>&1 | tail -60
