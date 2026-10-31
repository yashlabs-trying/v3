#!/bin/bash
set -uo pipefail
IMG=dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 600)
echo "cid=$CID"
echo "########## A) NO TOOLS, short prompt ##########"
docker exec "$CID" bash -lc "/root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time
t=time.time()
try:
    r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'say OK'}], api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=90, max_tokens=10)
    print('NO-TOOLS OK %.1fs:'%(time.time()-t), r.choices[0].message.content)
except Exception as e:
    print('NO-TOOLS ERR %.1fs'%(time.time()-t), type(e).__name__, str(e)[:150])
PY" 2>&1 | tail -3
echo "########## B) WITH TOOLS, short prompt ##########"
docker exec "$CID" bash -lc "/root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time
tools=[{'type':'function','function':{'name':'bash','description':'run','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}}]
t=time.time()
try:
    r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'say OK'}], tools=tools, api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=90, max_tokens=10)
    print('TOOLS OK %.1fs'%(time.time()-t), str(r.choices[0].message)[:150])
except Exception as e:
    print('TOOLS ERR %.1fs'%(time.time()-t), type(e).__name__, str(e)[:150])
PY" 2>&1 | tail -3
docker rm -f "$CID" >/dev/null 2>&1
