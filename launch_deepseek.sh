#!/bin/bash
setsid bash /home/yashs/dataforge/experiments/v3_1_baseline/run_deepseek.sh > /home/yashs/dataforge/experiments/v3_1_baseline/logs/deepseek_main.log 2>&1 < /dev/null &
echo "STARTED_PID=$!"
sleep 5
ps aux | grep -E 'run_deepseek|harbor run' | grep -v grep | head -3
echo "--- log ---"
tail -10 /home/yashs/dataforge/experiments/v3_1_baseline/logs/deepseek_main.log
