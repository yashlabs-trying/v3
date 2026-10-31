#!/bin/bash
pkill -9 -f 'run_deepseek' 2>/dev/null
pkill -9 -f 'harbor run' 2>/dev/null
pkill -9 -f 'harbor/bin/python' 2>/dev/null
sleep 2
for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
sleep 1
echo "remaining harbor procs:"
ps aux | grep -E 'harbor|run_deepseek' | grep -v grep | wc -l
echo "remaining containers:"
docker ps -q | wc -l
