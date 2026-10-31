#!/bin/bash
# Test: with agent preinstalled, how fast is a repeat `uv tool install`?
CID=$(docker run -d --rm dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan sleep 600)
echo "cid=$CID"
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; time (uv tool install --python 3.12 mini-swe-agent --with litellm --with orjson --with fastapi --with mcp 2>&1 | tail -3); echo EXIT=\$?"
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; mini-swe-agent --help 2>&1 | head -3"
docker rm -f "$CID" >/dev/null 2>&1
