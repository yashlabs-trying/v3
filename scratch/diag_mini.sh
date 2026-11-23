#!/bin/bash
# Direct diagnostic: install mini-swe-agent (with mcp) inside a NodeBB container and run --help + a one-shot.
set -uo pipefail
IMG=ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
KEY=$(tr -d '\n' < "$HOME/.dataforge_creds/deepinfra.key")
echo "=== launching ephemeral container ==="
CID=$(docker run -d --rm "$IMG" sleep 1800)
echo "cid=$CID"
echo "=== install mini-swe-agent with mcp ==="
docker exec "$CID" bash -lc "export UV_HTTP_TIMEOUT=900; if ! command -v uv >/dev/null; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi; export PATH=\$HOME/.local/bin:\$PATH; uv tool install --python 3.12 mini-swe-agent --with litellm --with orjson --with fastapi --with mcp 2>&1 | tail -5; echo INSTALL_EXIT=\$?"
echo "=== mini-swe-agent --help ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; mini-swe-agent --help 2>&1 | head -5; echo HELP_EXIT=\$?"
echo "=== one-shot model call via mini-swe-agent ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; export OPENAI_API_KEY=$KEY; export OPENAI_API_BASE=https://api.deepinfra.com/v1/openai; export OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai; cd /app; timeout 120 mini-swe-agent --yolo --model=openai/deepseek-ai/DeepSeek-V4.1-Flash --task='print hello' -c model.model_kwargs.api_base=https://api.deepinfra.com/v1/openai -c model.model_kwargs.timeout=60 2>&1 | tail -25; echo SHOT_EXIT=\$?"
echo "=== done ==="
docker rm -f "$CID" >/dev/null 2>&1
