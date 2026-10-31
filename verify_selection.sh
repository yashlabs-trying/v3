#!/bin/bash
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks
for T in \
  instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan \
  instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f \
  instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed \
  instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866 \
  instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d \
  instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad \
  instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan ; do
  if [ -d "$MIR/$T" ]; then
    echo "OK   $T"
  else
    echo "MISS $T"
  fi
done
echo "=== hashes of key files ==="
cd "$MIR"
for T in \
  instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan \
  instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f \
  instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed \
  instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866 \
  instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d \
  instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad \
  instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan ; do
  echo "$T"
  sha256sum "$T/tests/parser.py" "$T/tests/run_script.sh" "$T/tests/config.json" "$T/tests/test_patch.patch" 2>/dev/null | sed 's|^|  |'
done
