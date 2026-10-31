#!/bin/bash
REPO=/home/yashs/SWE-bench_Pro-os
cd "$REPO"
echo "=== core.autocrlf ==="
git config --get core.autocrlf
echo "=== git attributes ==="
ls -la .gitattributes 2>&1
cat .gitattributes 2>/dev/null
echo "=== file line endings sample ==="
file "v2/tasks/instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan/tests/test.sh"
file "v2/tasks/instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan/tests/run_script.sh"
echo "=== cat -A first line ==="
head -1 "v2/tasks/instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan/tests/test.sh" | cat -A
