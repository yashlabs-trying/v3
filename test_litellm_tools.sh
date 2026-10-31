#!/bin/bash
set -uo pipefail
IMG=dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 500)
docker cp /home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks/instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed/instruction.md "$CID:/tmp/task.txt"
echo "=== direct litellm with tools (function calling), task as user msg ==="
docker exec "$CID" bash -lc "export LITELLM_LOG=DEBUG; /root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time, json
task=open('/tmp/task.txt').read()
tools=[{'type':'function','function':{'name':'bash','description':'run a command','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}}]
t=time.time()
try:
    r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash',
      messages=[{'role':'user','content':'Please solve this issue: '+task}],
      tools=tools, tool_choice='auto',
      api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=120, max_tokens=512)
    print('OK in %.1fs'%(time.time()-t))
    print('msg:', json.dumps(r.choices[0].message.model_dump())[:400])
except Exception as e:
    print('ERR in %.1fs'%(time.time()-t), type(e).__name__, str(e)[:300])
PY" 2>&1 | grep -vE '^202[0-9]-|DEBUG|INFO|Giving up|Retrying|api_base|Selected|^\s*\$' | tail -20
docker rm -f "$CID" >/dev/null 2>&1
