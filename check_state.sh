#!/bin/bash
echo "=== active harbor jobs ==="
ps aux | grep -E 'harbor run|docker pull' | grep -v grep | sed -E 's/.*--job-name ([^ ]+).*/\1/' | head
echo "=== element-web nop result ==="
python3 - <<'PY'
import json, glob
f=glob.glob('/home/yashs/dataforge/experiments/v3_1_baseline/jobs/ctrl-nop-instance_element-hq__element-web-aec454d/instance_*/result.json')
if f:
    t=json.load(open(f[0]))
    print(json.dumps(t.get('verifier_result')))
else:
    print("NOT DONE")
PY
