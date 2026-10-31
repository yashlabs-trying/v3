#!/bin/bash
echo "=== ghcr token fetch x5 ==="
for i in 1 2 3 4 5; do
  R=$(timeout 40 curl -sS -o /dev/null -w '%{http_code} %{time_total}' 'https://ghcr.io/token?scope=repository:scaleapi/swe-bench_pro-v2:pull&service=ghcr.io' 2>&1)
  echo "attempt $i: $R"
done
echo "=== ping ==="
timeout 20 curl -sS -o /dev/null -w 'ghcr.io: %{http_code} %{time_total}s\n' https://ghcr.io/v2/ 2>&1
echo "=== dns ==="
getent hosts ghcr.io pkg-containers.githubusercontent.com 2>&1
