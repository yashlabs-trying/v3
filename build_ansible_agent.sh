#!/bin/bash
set -euo pipefail
BASE=ghcr.io/scaleapi/swe-bench_pro-v2:instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad
TAG=dataforge-agent:instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad
docker build --network=host -t "$TAG" -f - . <<'EOF'
FROM ghcr.io/scaleapi/swe-bench_pro-v2:instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad
USER root
ENV DEBIAN_FRONTEND=noninteractive
ENV UV_HTTP_TIMEOUT=1800
ENV UV_CONCURRENT_DOWNLOADS=4
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/* && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv tool install --python 3.12 mini-swe-agent --with litellm --with orjson --with fastapi --with mcp && \
    /root/.local/bin/mini-swe-agent --help >/dev/null && echo AGENT_OK
EOF
echo "built $TAG"
