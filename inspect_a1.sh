#!/bin/bash
T=$(ls -d /home/yashs/dataforge/experiments/v3_1_baseline/jobs/ds-nodebb-a1/instance_* | head -1)
echo "trial=$T"
echo "=== files ==="
find "$T" -type f
echo "=== trajectory.json (first 2000 chars) ==="
head -c 2000 "$T/agent/trajectory.json"; echo
echo "=== trajectory.json keys ==="
python3 - <<PY
import json
j=json.load(open("$T/agent/trajectory.json"))
print(type(j), list(j.keys()) if isinstance(j,dict) else len(j))
if isinstance(j,dict):
    m=j.get("messages")
    print("messages:", len(m) if m else 0)
PY
echo "=== mini-swe-agent.txt size ==="
wc -c "$T/agent/mini-swe-agent.txt"
echo "=== transcript tail 40 ==="
tail -40 "$T/agent/mini-swe-agent.txt"
