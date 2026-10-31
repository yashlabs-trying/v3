#!/bin/bash
# Fresh-sandbox regrade (patch_replay) for each counted DeepSeek submission, restricted with -i.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
MIR=/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf
OVL=/home/yashs/dataforge/experiments/v3_1_baseline/tooling_overlay
OUT=/home/yashs/dataforge/experiments/v3_1_baseline/jobs
LOGDIR=/home/yashs/dataforge/experiments/v3_1_baseline/logs
cd "$MIR"
export PYTHONPATH="$OVL:$MIR/v2/tooling"

# srcjob|task|short
JOBS=(
  "final-nodebb|instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan|nodebb"
  "final-flipt|instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f|flipt"
  "f3-vuls-a1|instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed|vuls"
  "f3-openlibrary-a1|instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866|openlibrary"
  "f3-teleport-a1|instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d|teleport"
  "f3-ansible-a1|instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad|ansible"
  "f3-elementweb-a1|instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan|elementweb"
)

for entry in "${JOBS[@]}"; do
  SRC="${entry%%|*}"; rest="${entry#*|}"; T="${rest%%|*}"; S="${rest##*|}"
  echo "=== REGRADE $S START $(date -u +%H:%M:%S) ==="
  timeout 3000 harbor run -p v2/tasks -i "$T" -e docker -n 1 \
    -a "patch_replay:PatchReplayAgent" -m replay \
    --ak source_job="$OUT/$SRC" \
    -o "$OUT" --job-name "regrade-$S" > "$LOGDIR/regrade-$S.log" 2>&1
  echo "=== REGRADE $S DONE rc=$? $(date -u +%H:%M:%S) ==="
  for c in $(docker ps -q); do docker rm -f "$c" >/dev/null 2>&1; done
done
echo "ALL_REGRADE_DONE"
