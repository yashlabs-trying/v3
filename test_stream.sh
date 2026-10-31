#!/bin/bash
set -uo pipefail
IMG=dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 400)
echo "cid=$CID"
echo "=== NON-STREAM ==="
docker exec "$CID" bash -lc "/root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time
t=time.time()
r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'count to 20'}], api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=90, max_tokens=200, stream=False)
print('NONSTREAM %.1fs'%(time.time()-t), r.choices[0].message.content[:80])
PY" 2>&1 | tail -2
echo "=== STREAM ==="
docker exec "$CID" bash -lc "/root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm, time
t=time.time()
n=0
try:
    for chunk in litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'count to 20'}], api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', timeout=90, max_tokens=200, stream=True):
        n+=1
    print('STREAM %.1fs chunks=%d'%(time.time()-t, n))
except Exception as e:
    print('STREAM ERR %.1fs'%(time.time()-t), type(e).__name__, str(e)[:150])
PY" 2>&1 | tail -2
docker rm -f "$CID" >/dev/null 2>&1
