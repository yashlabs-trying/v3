#!/bin/bash
# Build a derived image with mini-swe-agent+mcp preinstalled for a given base image.
# Usage: build_agent_image.sh <base_image>
set -euo pipefail
BASE="$1"
TAG="${BASE/ghcr.io\/scaleapi\/swe-bench_pro-v2:/dataforge-agent:}"
echo "base=$BASE"
echo "tag=$TAG"
# Detect interpreter/package manager present.
docker build --network=host -t "$TAG" -f - . <<EOF
FROM $BASE
USER root
ENV UV_HTTP_TIMEOUT=1800
ENV UV_CONCURRENT_DOWNLOADS=4
RUN if ! command -v uv >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi && \
    export PATH=\$HOME/.local/bin:\$PATH && \
    uv tool install --python 3.12 mini-swe-agent --with litellm --with orjson --with fastapi --with mcp && \
    mini-swe-agent --help >/dev/null && echo AGENT_OK
EOF
echo "built $TAG"
