#!/bin/bash
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
cd "$MIR/v2/tasks"
for T in \
  instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866 \
  instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d \
  instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan ; do
  echo "############ $T parser.py (FULL) size=$(wc -l < "$T/tests/parser.py") ############"
  cat "$T/tests/parser.py"
  echo ""
done
