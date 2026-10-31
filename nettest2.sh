#!/bin/bash
for i in 1 2 3; do
  timeout 30 curl -sS -o /dev/null -w "pypi try $i: %{http_code} %{time_total}s\n" https://pypi.org/simple/ 2>&1
done
echo "=== pip config ==="
cat ~/.pip/pip.conf ~/.config/pip/pip.conf /etc/pip.conf 2>/dev/null || echo "no pip config"
echo "=== uv config ==="
cat ~/.config/uv/uv.toml 2>/dev/null || echo "no uv config"
echo "=== env proxies ==="
env | grep -iE 'proxy|index' || echo "none"
