#!/bin/bash
REPO=/home/yashs/SWE-bench_Pro-os
T="instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan"
cd "$REPO"
echo "=== tests/test.sh ==="
cat -A "v2/tasks/$T/tests/test.sh"
echo ""
echo "=== tests/run_script.sh ==="
cat "v2/tasks/$T/tests/run_script.sh"
echo ""
echo "=== tests/parser.py ==="
cat "v2/tasks/$T/tests/parser.py"
