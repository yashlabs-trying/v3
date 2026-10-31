#!/bin/bash
nohup bash /home/yashs/dataforge/experiments/v3_1_baseline/run_controls.sh > /home/yashs/dataforge/experiments/v3_1_baseline/logs/controls_main.log 2>&1 &
echo "STARTED_PID=$!"
echo "$!" > /home/yashs/dataforge/experiments/v3_1_baseline/logs/controls.pid
