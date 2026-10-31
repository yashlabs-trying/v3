#!/bin/bash
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
CID=$(docker run -d --rm "$IMG" sleep 300)
echo "=== mini-extra config options ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; mini-extra --help 2>&1 | head -30; echo '==='; mini-extra config --help 2>&1 | head -30; echo '==='; mini-extra config set --help 2>&1 | head -40"
echo "=== search package for global config requirements ==="
docker exec "$CID" bash -lc "python3 - <<'PY'
import glob
base='/root/.local/share/uv/tools/mini-swe-agent/lib/python3.12/site-packages'
for pat in ['minisweagent/__init__.py','minisweagent/config/global*','minisweagent/config/**/*.py']:
    for f in glob.glob(base+'/'+pat, recursive=True)[:5]:
        print('FILE', f)
PY"
docker rm -f "$CID" >/dev/null 2>&1
