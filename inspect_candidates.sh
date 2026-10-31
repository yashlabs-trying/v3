#!/bin/bash
# Inspect candidate tasks' risk mechanics for selection justification.
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
cd "$MIR/v2/tasks"
for T in \
  instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f \
  instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed \
  instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866 ; do
  echo "############ $T ############"
  echo "--- run_script.sh ---"
  cat "$T/tests/run_script.sh"
  echo "--- parser.py (below DO NOT MODIFY marker) ---"
  sed -n '/Implement the parsing logic below/,/Implement the parsing logic above/p' "$T/tests/parser.py"
  echo ""
done
