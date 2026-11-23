#!/bin/bash
set -uo pipefail
IMG=dataforge-agent:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
CID=$(docker run -d --rm "$IMG" sleep 500)
echo "cid=$CID"
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; export MSWEA_CONFIGURED=true; export OPENAI_API_KEY='$KEY'; export OPENAI_API_BASE=https://api.deepinfra.com/v1/openai; export OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai; cd /app; timeout 180 mini-swe-agent --yolo --model=openai/deepseek-ai/DeepSeek-V4.1-Flash --task='Run exactly one command: echo HI. Then run: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT' -c mini.yaml -c model.model_kwargs.timeout=120 -c model.model_kwargs.api_base=https://api.deepinfra.com/v1/openai --exit-immediately > /tmp/out.txt 2>&1; echo EXIT=\$?; wc -l /tmp/out.txt; tail -40 /tmp/out.txt"
docker rm -f "$CID" >/dev/null 2>&1
