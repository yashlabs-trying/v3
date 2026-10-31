#!/bin/bash
set -uo pipefail
SRC=/home/yashs/SWE-bench_Pro-os
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
rm -rf "$MIR"
# Fresh clone from the existing local repo (no Windows autocrlf), then force LF working tree.
git -c core.autocrlf=false clone --no-hardlinks "file://$SRC" "$MIR" 2>&1 | tail -3
cd "$MIR"
git checkout -- . 2>/dev/null
# Ensure no CRLF anywhere in scripts
find . -type f \( -name '*.sh' -o -name '*.py' -o -name '*.toml' -o -name '*.json' -o -name '*.patch' -o -name '*.diff' \) -exec sed -i 's/\r$//' {} +
echo "=== verify ==="
file "v2/tasks/instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan/tests/test.sh"
head -1 "v2/tasks/instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan/tests/test.sh" | cat -A
git -C "$MIR" rev-parse HEAD
