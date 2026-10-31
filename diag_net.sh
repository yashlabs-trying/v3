#!/bin/bash
CID=$(docker run -d --rm ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan sleep 1800)
echo "cid=$CID"
echo "=== network speed test inside container ==="
docker exec "$CID" bash -lc "time curl -sS -o /dev/null -w 'pypi:%{http_code} %{time_total}s\n' https://pypi.org/simple/ 2>&1"
docker exec "$CID" bash -lc "time curl -sS -o /dev/null -w 'files.pythonhosted:%{http_code} %{time_total}s\n' https://files.pythonhosted.org/ 2>&1"
docker exec "$CID" bash -lc "time curl -sS -o /dev/null -w 'astral:%{http_code} %{time_total}s\n' https://astral.sh/ 2>&1"
echo "=== pip install toml (small) timing ==="
docker exec "$CID" bash -lc "pip install --no-cache-dir toml 2>&1 | tail -3; echo PIP_EXIT=\$?"
docker rm -f "$CID" >/dev/null 2>&1
