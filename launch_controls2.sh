#!/bin/bash
mkdir -p /home/user/dataforge/experiments/v3_1_baseline/logs
setsid bash /home/user/dataforge/experiments/v3_1_baseline/run_controls.sh > /home/user/dataforge/experiments/v3_1_baseline/logs/controls_main.log 2>&1 < /dev/null &
echo "STARTED_PID=$!"
disown
sleep 5
echo "--- after 5s ---"
ps aux | grep -E 'run_controls|docker pull|harbor' | grep -v grep | head
echo "--- main log ---"
tail -20 /home/user/dataforge/experiments/v3_1_baseline/logs/controls_main.log
