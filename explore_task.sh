#!/bin/bash
REPO=/home/yashs/SWE-bench_Pro-os
T="instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan"
cd "$REPO"
echo "=== task tree: $T ==="
find "v2/tasks/$T" -type f | sed "s|v2/tasks/$T/||" | sort
echo ""
echo "=== task.toml ==="
cat "v2/tasks/$T/task.toml"
echo ""
echo "=== environment/Dockerfile ==="
cat "v2/tasks/$T/environment/Dockerfile"
echo ""
echo "=== tests/config.json ==="
cat "v2/tasks/$T/tests/config.json"
