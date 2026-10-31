#!/bin/bash
C=$(docker ps --format '{{.Names}}' | grep env-main | head -1)
echo "container=$C"
docker exec "$C" bash -c "ps -eo pid,ppid,etime,pcpu,args --sort=-pcpu | head -30" 2>&1
