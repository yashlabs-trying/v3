#!/bin/bash
# Replicate Harbor's exact mini-swe-agent invocation inside the pre-baked image.
set -uo pipefail
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
KEY=$(tr -d '\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 400)
echo "cid=$CID"
echo "=== check for global config file presence ==="
docker exec "$CID" bash -lc "ls -la /root/.config/mini-swe-agent/ 2>&1; echo '--- .env ---'; cat /root/.config/mini-swe-agent/.env 2>&1"
echo "=== replicate harbor invocation with custom.yaml ==="
docker exec "$CID" bash -lc "mkdir -p /tmp/mswea-config && cat > /tmp/mswea-config/custom.yaml <<'YAML'
model:
  model_name: openai/deepseek-ai/DeepSeek-V4.1-Flash
YAML
export PATH=\$HOME/.local/bin:\$PATH; export OPENAI_API_KEY='$KEY'; export OPENAI_API_BASE=https://api.deepinfra.com/v1/openai; export OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai; cd /app; timeout 150 mini-swe-agent --yolo --model=openai/deepseek-ai/DeepSeek-V4.1-Flash --task='Run the single command: echo hello. Then stop.' --output=/tmp/traj.json --cost-limit 0 -c mini -c model.model_kwargs.timeout=60 -c /tmp/mswea-config/custom.yaml -c model.model_kwargs.api_base=https://api.deepinfra.com/v1/openai --exit-immediately 2>&1 | tail -30; echo SHOT_EXIT=\$?"
docker rm -f "$CID" >/dev/null 2>&1
