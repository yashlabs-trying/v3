#!/bin/bash
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
CID=$(docker run -d --rm "$IMG" sleep 300)
echo "=== grep global config logic ==="
docker exec "$CID" bash -lc "python3 - <<'PY'
import glob, re
base='/root/.local/share/uv/tools/mini-swe-agent/lib/python3.12/site-packages'
for f in glob.glob(base+'/minisweagent/**/*.py', recursive=True):
    try: t=open(f).read()
    except: continue
    if 'config' in f.lower() or 'global' in t.lower():
        for m in re.finditer(r'.{0,80}(MSWEA_CONFIG|global config|\.env|config_dir|setup wizard|is_setup|setup_config|provide your).{0,80}', t):
            print(f.split('site-packages/')[1], '::', m.group(0).replace(chr(10),' ')[:160])
PY" 2>&1 | head -50
docker rm -f "$CID" >/dev/null 2>&1
