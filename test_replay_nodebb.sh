#!/bin/bash
# Independently test whether the captured NodeBB model.patch (166KB Redis dumps) can be replayed.
set -uo pipefail
IMG=ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
P=$(ls /home/yashs/dataforge/experiments/v3_1_baseline/jobs/final-nodebb/instance_*/agent/model.patch | head -1)
echo "patch: $P ($(wc -c < "$P") bytes)"
CID=$(docker run -d --rm "$IMG" sleep 400)
echo "cid=$CID"
echo "=== where is the repo ==="
docker exec "$CID" bash -lc "ls -d /app /testbed 2>/dev/null"
echo "=== copy patch in ==="
docker cp "$P" "$CID:/tmp/replay.patch"
echo "=== git apply --verbose (exact replay command) ==="
docker exec "$CID" bash -lc "cd /app 2>/dev/null || cd /testbed; git apply --verbose /tmp/replay.patch 2>&1 | tail -30; echo APPLY_RC=\$?"
echo "=== git status after apply ==="
docker exec "$CID" bash -lc "cd /app 2>/dev/null || cd /testbed; git status --short | head; echo '---'; ls -la appendonlydir/ 2>&1 | head"
echo "=== retry with 3way / patch fuzz (replay fallbacks) ==="
docker exec "$CID" bash -lc "cd /app 2>/dev/null || cd /testbed; git apply --3way /tmp/replay.patch 2>&1 | tail -5; echo THREE_RC=\$?"
docker rm -f "$CID" >/dev/null 2>&1
