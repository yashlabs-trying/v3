#!/bin/bash
set -uo pipefail
AUTH="$HOME/.local/share/opencode/auth.json"
# extract deepinfra key without printing it
KEY=$(python3 -c "import json;print(json.load(open('$AUTH'))['deepinfra']['key'])")
echo "key length: ${#KEY}"
echo "=== deepinfra models (deepseek) ==="
curl -sS --max-time 40 https://api.deepinfra.com/v1/openai/models -H "Authorization: Bearer $KEY" 2>&1 | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
except Exception as e:
    print('parse error', e); sys.exit()
ids=[m.get('id','') for m in d.get('data',[])]
ds=[i for i in ids if 'deepseek' in i.lower()]
print('total models:', len(ids))
for i in ds: print(' ', i)
" 2>&1
echo "=== tiny completion probe ==="
curl -sS --max-time 60 https://api.deepinfra.com/v1/openai/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-V4.1-Flash","messages":[{"role":"user","content":"reply with OK"}],"max_tokens":5}' 2>&1 | head -c 600
echo ""
