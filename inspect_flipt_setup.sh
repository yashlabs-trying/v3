#!/bin/bash
T=/home/yashs/dataforge/experiments/v3_1_baseline/jobs/deepseek2-flipt-a1/instance_flipt-io__flipt-6fe76d0__KGCvVE5
echo "--- setup dir ---"
ls -la "$T/agent/setup/"
echo "--- mcp mentions in trial.log ---"
grep -n 'mcp\|No module\|command not found\|error' "$T/trial.log" | head -30
echo "--- mini-swe-agent.txt head (agent transcript) ---"
head -20 "$T/agent/mini-swe-agent.txt"
echo "--- mini-swe-agent.txt tail ---"
tail -20 "$T/agent/mini-swe-agent.txt"
