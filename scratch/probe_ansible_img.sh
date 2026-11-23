#!/bin/bash
IMG=ghcr.io/scaleapi/swe-bench_pro-v2:instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad
CID=$(docker run -d --rm "$IMG" sleep 120)
echo "--- os ---"
docker exec "$CID" cat /etc/os-release 2>/dev/null | head -3
echo "--- tools ---"
docker exec "$CID" bash -lc "for t in curl wget apt-get apk yum dnf python3 pip python; do command -v \$t >/dev/null && echo \"have \$t\" || echo \"MISSING \$t\"; done"
docker rm -f "$CID" >/dev/null 2>&1
