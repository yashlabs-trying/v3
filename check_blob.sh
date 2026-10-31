#!/bin/bash
REPO=/home/yashs/SWE-bench_Pro-os
cd "$REPO"
echo "=== blob content of test.sh in git (should be LF) ==="
git show HEAD:v2/tasks/instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan/tests/test.sh | head -1 | cat -A
echo "=== global autocrlf (windows) ==="
git config --system --get core.autocrlf 2>&1
git config --global --get core.autocrlf 2>&1
echo "=== git version ==="
git --version
