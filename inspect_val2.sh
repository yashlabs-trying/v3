#!/bin/bash
T=$(ls -d /home/yashs/dataforge/experiments/v3_1_baseline/jobs/val-flipt/instance_* | head -1)
echo "=== transcript (first 60 lines) ==="
head -60 "$T/agent/mini-swe-agent.txt"
echo ""
echo "=== grep for wizard/abort/error/retry ==="
grep -niE 'abort|wizard|to get started|error|retry|connection|refused' "$T/agent/mini-swe-agent.txt" | head -20
