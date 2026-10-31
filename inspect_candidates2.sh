#!/bin/bash
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
cd "$MIR/v2/tasks"
dump() {
  local T="$1"
  echo "############ $T ############"
  if [ ! -d "$T" ]; then echo "MISSING"; return; fi
  echo "--- task.toml [verifier] ---"
  grep -A2 '\[verifier\]' "$T/task.toml"
  echo "--- config.json ---"
  cat "$T/tests/config.json"
  echo ""
  echo "--- run_script.sh ---"
  cat "$T/tests/run_script.sh"
  echo "--- parser.py body ---"
  sed -n '/Implement the parsing logic below/,/Implement the parsing logic above/p' "$T/tests/parser.py"
  echo ""
}
# pick specific candidate instances
dump "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866"
dump "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d"
dump "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad"
dump "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan"
