#!/bin/bash
set -uo pipefail
IMG=dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 600)
docker cp /home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks/instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed/instruction.md "$CID:/tmp/task.txt"
echo "=== full vuls task + tools, timeout 90 ==="
docker exec "$CID" bash -lc "/root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time
task=open('/tmp/task.txt').read()
tools=[{'type':'function','function':{'name':'bash','description':'run','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}}]
t=time.time()
try:
    r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'Please solve this issue: '+task}], tools=tools, api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=90, max_tokens=2048)
    print('FULL+T OOLS OK %.1fs'%(time.time()-t))
    print(str(r.choices[0].message)[:300])
except Exception as e:
    print('FULL+TOOLS ERR %.1fs'%(time.time()-t), type(e).__name__, str(e)[:200])
PY" 2>&1 | tail -5
echo "=== full vuls task, NO tools, timeout 90 ==="
docker exec "$CID" bash -lc "/root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time
task=open('/tmp/task.txt').read()
t=time.time()
try:
    r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'Please solve this issue: '+task}], api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=90, max_tokens=2048)
    print('FULL NO-TOOLS OK %.1fs'%(time.time()-t))
    print(str(r.choices[0].message)[:300])
except Exception as e:
    print('FULL NO-TOOLS ERR %.1fs'%(time.time()-t), type(e).__name__, str(e)[:200])
PY" 2>&1 | tail -5
docker rm -f "$CID" >/dev/null 2>&1
