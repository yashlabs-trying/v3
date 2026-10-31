#!/bin/bash
# Create audit-side task overlays: same task content, but environment/Dockerfile
# is replaced with `FROM dataforge-agent:<instance_id>` (agent preinstalled).
# Nothing else is changed (tests/parser/config/instruction/gold untouched).
set -uo pipefail
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks
DST=/home/yashs/dataforge/experiments/v3_1_baseline/audit_tasks
rm -rf "$DST"; mkdir -p "$DST"

TASKS=(
  "instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan"
  "instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f"
  "instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed"
  "instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866"
  "instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d"
  "instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad"
  "instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan"
)

for T in "${TASKS[@]}"; do
  mkdir -p "$DST/$T/environment" "$DST/$T/tests" "$DST/$T/solution"
  cp "$MIR/$T/instruction.md" "$DST/$T/" 2>/dev/null || true
  cp "$MIR/$T/task.toml" "$DST/$T/"
  # Point the task at the pre-baked agent image (agent preinstalled, tests untouched).
  sed -i "s|^docker_image = .*|docker_image = \"dataforge-agent:$T\"|" "$DST/$T/task.toml"
  cp -r "$MIR/$T/tests/." "$DST/$T/tests/"
  cp -r "$MIR/$T/solution/." "$DST/$T/solution/" 2>/dev/null || true
  # Keep the same base image reference so the environment is identical, but pre-baked with the agent.
  echo "FROM dataforge-agent:$T" > "$DST/$T/environment/Dockerfile"
done
echo "audit overlays created:"
ls "$DST"
echo "--- sample dockerfile ---"
cat "$DST/instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f/environment/Dockerfile"
