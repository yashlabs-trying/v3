#!/bin/bash
# Retry-pull missing images with backoff.
IMS=(
  "ghcr.io/scaleapi/swe-bench_pro-v2:instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f"
  "ghcr.io/scaleapi/swe-bench_pro-v2:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed"
  "ghcr.io/scaleapi/swe-bench_pro-v2:instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad"
  "ghcr.io/scaleapi/swe-bench_pro-v2:instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan"
)
for IMG in "${IMS[@]}"; do
  for attempt in 1 2 3 4 5 6; do
    if docker image inspect "$IMG" >/dev/null 2>&1; then echo "present: $IMG"; break; fi
    echo "pull attempt $attempt: $IMG"
    if timeout 3000 docker pull "$IMG" >/dev/null 2>&1; then
      echo "  ok: $IMG"; break
    else
      echo "  failed attempt $attempt"; sleep 10
    fi
  done
done
echo "RETRY_PULL_DONE"
