#!/bin/bash
T=$(ls -d /home/yashs/dataforge/experiments/v3_1_baseline/jobs/val-flipt/instance_* | head -1)
echo "trial=$T"
echo "=== transcript size ==="
wc -c "$T/agent/mini-swe-agent.txt" 2>/dev/null
echo "=== transcript tail 30 ==="
tail -30 "$T/agent/mini-swe-agent.txt" 2>/dev/null
echo "=== trajectory messages ==="
python3 - <<PY
import json,glob
f=glob.glob("$T/agent/*trajectory*.json")
for x in f:
    try:
        j=json.load(open(x)); print(x, "msgs:", len(j.get("messages",[])) if isinstance(j,dict) else len(j))
    except Exception as e: print(x, "ERR", e)
PY
echo "=== model.patch ==="
wc -c "$T/agent/model.patch" 2>/dev/null
head -5 "$T/agent/model.patch" 2>/dev/null
