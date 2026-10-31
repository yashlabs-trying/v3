#!/bin/bash
KEYVAL=$(cat /home/user/.dataforge_creds/deepinfra.key)
echo "key prefix: ${KEYVAL:0:6}"
echo "=== literal key occurrences anywhere in audit dir ==="
grep -rlF "$KEYVAL" /home/user/dataforge/experiments/v3_1_baseline/ 2>/dev/null
echo "count: $(grep -rlF "$KEYVAL" /home/user/dataforge/experiments/v3_1_baseline/ 2>/dev/null | wc -l)"
echo "=== check jobs/ and logs/ specifically ==="
grep -rlF "$KEYVAL" /home/user/dataforge/experiments/v3_1_baseline/logs /home/user/dataforge/experiments/v3_1_baseline/jobs 2>/dev/null | head
echo "=== also check redacted form sk-di- prefix ==="
grep -rlE 'sk-di-[A-Za-z0-9]{20}' /home/user/dataforge/experiments/v3_1_baseline/jobs /home/user/dataforge/experiments/v3_1_baseline/logs 2>/dev/null | head
