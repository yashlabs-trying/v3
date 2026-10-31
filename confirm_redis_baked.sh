#!/bin/bash
IMG=ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
CID=$(docker run -d --rm "$IMG" sleep 120)
echo "=== base image: appendonlydir present BEFORE any agent run? ==="
docker exec "$CID" bash -lc "ls -la /app/appendonlydir/ 2>&1"
echo "=== is it git-tracked? ==="
docker exec "$CID" bash -lc "cd /app && git ls-files appendonlydir/ | head; echo '--- status ---'; git status --short appendonlydir/ 2>&1 | head"
echo "=== .gitignore mention? ==="
docker exec "$CID" bash -lc "cd /app && grep -n appendonly .gitignore 2>/dev/null || echo 'not in .gitignore'"
docker rm -f "$CID" >/dev/null 2>&1
