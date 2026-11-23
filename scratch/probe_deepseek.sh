#!/bin/bash
set -uo pipefail
KEY=$(cat "$HOME/.dataforge_creds/deepinfra.key")
echo "=== probe DeepSeek-V4.1-Flash ==="
curl -sS --max-time 90 https://api.deepinfra.com/v1/openai/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-V4.1-Flash","messages":[{"role":"user","content":"Reply with exactly: OK123"}],"max_tokens":16}' 2>&1 | head -c 800
echo ""
echo "=== probe DeepSeek-V4-Pro ==="
curl -sS --max-time 90 https://api.deepinfra.com/v1/openai/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-V4-Pro","messages":[{"role":"user","content":"Reply with exactly: OK123"}],"max_tokens":16}' 2>&1 | head -c 800
echo ""
