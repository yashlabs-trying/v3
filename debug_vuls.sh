#!/bin/bash
# Reproduce vuls stall with litellm debug, short cap, direct in container (no Harbor).
set -uo pipefail
IMG=dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed
KEY=$(tr -d '\r\n' < "$HOME/.dataforge_creds/deepinfra.key")
TASK=$(cat /home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks/instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed/instruction.md)
CID=$(docker run -d --rm "$IMG" sleep 500)
echo "cid=$CID"
docker cp /home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tooling/configs/mini_toolcall.yaml "$CID:/tmp/cfg.yaml"
docker cp /home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks/instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed/instruction.md "$CID:/tmp/task.txt"
docker exec "$CID" bash -lc "export PATH=\$HOME/.local/bin:\$PATH; export MSWEA_CONFIGURED=true; export MSWEA_COST_TRACKING=ignore_errors; export LITELLM_LOG=DEBUG; export OPENAI_API_KEY='$KEY'; export OPENAI_API_BASE=https://api.deepinfra.com/v1/openai; export OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai; cd /app; timeout 300 mini-swe-agent --yolo --model=openai/deepseek-ai/DeepSeek-V4.1-Flash --task=\"\$(cat /tmp/task.txt)\" -c /tmp/cfg.yaml -c model.model_kwargs.timeout=120 -c model.model_kwargs.api_base=https://api.deepinfra.com/v1/openai --exit-immediately > /tmp/out.txt 2>&1; echo EXIT=\$?; echo '--- grep model/http errors ---'; grep -iE 'completion|error|retry|timeout|status|exception|APIError|Connect' /tmp/out.txt | tail -25; echo '--- last 15 ---'; tail -15 /tmp/out.txt" 2>&1 || true
docker rm -f "$CID" >/dev/null 2>&1
