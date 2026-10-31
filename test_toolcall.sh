#!/bin/bash
# Test the EXACT toolcall config Harbor uses, directly in a container.
set -uo pipefail
IMG=dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
CFG=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tooling/configs/mini_toolcall.yaml
CID=$(docker run -d --rm "$IMG" sleep 400)
echo "cid=$CID"
docker cp "$CFG" "$CID:/tmp/mini_toolcall.yaml"
echo "=== run with toolcall config, 150s cap ==="
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; export MSWEA_CONFIGURED=true; export MSWEA_COST_TRACKING=ignore_errors; export OPENAI_API_KEY='$KEY'; export OPENAI_API_BASE=https://api.deepinfra.com/v1/openai; export OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai; cd /app; timeout 150 mini-swe-agent --yolo --model=openai/deepseek-ai/DeepSeek-V4.1-Flash --task='Run exactly one command: echo HI. Then run: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT' -c /tmp/mini_toolcall.yaml -c model.model_kwargs.timeout=120 -c model.model_kwargs.api_base=https://api.deepinfra.com/v1/openai --exit-immediately > /tmp/out.txt 2>&1; echo EXIT=\$?; echo '--- tail 35 ---'; tail -35 /tmp/out.txt"
docker rm -f "$CID" >/dev/null 2>&1
