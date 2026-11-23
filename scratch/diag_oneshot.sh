#!/bin/bash
# Direct one-shot: mini-swe-agent against DeepInfra inside the pre-baked image, no Harbor.
set -uo pipefail
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
KEY=$(tr -d '\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 400)
echo "cid=$CID"
echo "=== connectivity from container to deepinfra ==="
docker exec "$CID" bash -lc "timeout 30 curl -sS -o /dev/null -w 'deepinfra:%{http_code} %{time_total}s\n' https://api.deepinfra.com/v1/openai/models 2>&1"
echo "=== mini-swe-agent one-shot (2 min cap) ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; export OPENAI_API_KEY='$KEY'; export OPENAI_API_BASE=https://api.deepinfra.com/v1/openai; export OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai; cd /app; timeout 150 mini-swe-agent --yolo --model=openai/deepseek-ai/DeepSeek-V4.1-Flash --task='Run the single command: echo hello. Then stop.' --cost-limit 0 -c model.model_kwargs.api_base=https://api.deepinfra.com/v1/openai -c model.model_kwargs.timeout=60 2>&1 | tail -40; echo SHOT_EXIT=\$?"
docker rm -f "$CID" >/dev/null 2>&1
