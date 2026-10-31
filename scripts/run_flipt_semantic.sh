#!/bin/bash
# Reproduce the flipt semantic audit (V3.2, Phase 2).
# Runs the generated contract probes against a candidate middleware.go inside
# the task image. Usage: bash run_flipt_semantic.sh <candidate_middleware.go>
set -euo pipefail

IMAGE="dataforge-agent:instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f"
CANDIDATE="${1:-}"
if [ -z "$CANDIDATE" ]; then
  echo "usage: $0 <candidate_middleware.go>" >&2
  exit 2
fi
CANDIDATE_DIR="$(cd "$(dirname "$CANDIDATE")" && pwd)"
CANDIDATE_FILE="$(basename "$CANDIDATE")"

PROBE_FILE="zz_df_semantic_test.go"
if [ ! -f "$CANDIDATE_DIR/$PROBE_FILE" ]; then
  echo "generating probes via python..."
  python3 - "$CANDIDATE_DIR/$PROBE_FILE" <<'PY'
import sys
sys.path.insert(0, "/mnt/c/Users/yashs/dataforge/v3")
from dataforge_v3.semantic.tasks.flipt import generate_go_probes
open(sys.argv[1], "w", encoding="utf-8").write(generate_go_probes())
PY
fi

docker run --rm -v "$CANDIDATE_DIR:/overlay" "$IMAGE" bash -lc "
  set -e
  cp /overlay/$CANDIDATE_FILE /app/internal/server/auth/middleware.go
  cp /overlay/$PROBE_FILE /app/internal/server/auth/$PROBE_FILE
  cd /app
  export PATH=/usr/local/go/bin:/usr/bin:/bin:/usr/sbin:/sbin
  go test -count=1 -v -run '^TestDataForgeSemanticProbes$' ./internal/server/auth 2>&1
"
