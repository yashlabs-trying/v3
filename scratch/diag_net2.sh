#!/bin/bash
set -uo pipefail
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
KEY=$(tr -d '\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 400)
echo "cid=$CID"
echo "=== python httpx direct to deepinfra ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; /root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import httpx, os
key='$KEY'
for i in range(3):
    try:
        r=httpx.post('https://api.deepinfra.com/v1/openai/chat/completions',
          headers={'Authorization':'Bearer '+key},
          json={'model':'deepseek-ai/DeepSeek-V4.1-Flash','messages':[{'role':'user','content':'say OK'}],'max_tokens':5},
          timeout=60)
        print('try',i,'status',r.status_code, r.text[:100])
    except Exception as e:
        print('try',i,'ERR',type(e).__name__, str(e)[:150])
PY"
echo "=== litellm direct ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; export OPENAI_API_KEY='$KEY'; /root/.local/share/uv/tools/mini-swe-agent/bin/python - <<PY
import litellm
try:
    r=litellm.completion(model='openai/deepseek-ai/DeepSeek-V4.1-Flash', messages=[{'role':'user','content':'say OK'}], api_base='https://api.deepinfra.com/v1/openai', api_key='$KEY', max_tokens=5, timeout=60)
    print('litellm OK:', r.choices[0].message.content)
except Exception as e:
    print('litellm ERR:', type(e).__name__, str(e)[:200])
PY"
docker rm -f "$CID" >/dev/null 2>&1
