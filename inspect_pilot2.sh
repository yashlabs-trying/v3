#!/bin/bash
D=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/jobs/pilot-deepseek-2
find "$D" -type f | sort
echo ""
echo "=== agent dir ==="
ls -la "$D"/instance_*/agent/ 2>/dev/null
echo "=== verifier dir ==="
ls -la "$D"/instance_*/verifier/ 2>/dev/null
echo "=== result summary ==="
python3 -c "
import json,glob
r=json.load(open(glob.glob('$D/instance_*/result.json')[0]))
print('task:', r['task_name'])
print('reward:', (r.get('verifier_result') or {}).get('reward'))
print('agent_result:', r.get('agent_result'))
print('exception:', r.get('exception_info'))
print('agent_exec s:', r.get('agent_execution'))
print('verifier s:', r.get('verifier'))
"
