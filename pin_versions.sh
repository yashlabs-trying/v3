#!/bin/bash
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
CID=$(docker run -d --rm "$IMG" sleep 120)
echo "=== mini-swe-agent version ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; mini-swe-agent --version 2>&1 | head -2"
echo "=== pip freeze (key pkgs) ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; uv pip list --python /root/.local/share/uv/tools/mini-swe-agent/bin/python 2>/dev/null | grep -iE 'mini-swe|litellm|mcp|openai|httpx|pydantic|datasets|pandas|numpy|orjson|fastapi'"
echo "=== full freeze hash ==="
docker exec "$CID" bash -lc "uv pip freeze --python /root/.local/share/uv/tools/mini-swe-agent/bin/python 2>/dev/null | sha256sum"
docker rm -f "$CID" >/dev/null 2>&1
