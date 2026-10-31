#!/bin/bash
set -uo pipefail
echo "=== date ==="
date -u
echo "=== upstream ==="
git -C /home/yashs/SWE-bench_Pro-os rev-parse HEAD
git -C /home/yashs/SWE-bench_Pro-os status --porcelain | wc -l
echo "clean_lines_above"
git -C /home/yashs/SWE-bench_Pro-os branch --show-current
echo "=== mirror ==="
git -C /home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf rev-parse HEAD
echo "=== harbor ==="
~/.local/bin/harbor --version
echo "=== docker ==="
docker --version
docker info --format '{{.ServerVersion}} {{.Driver}} {{.OperatingSystem}}'
echo "=== cpu ==="
grep -m1 'model name' /proc/cpuinfo
nproc
echo "=== mem ==="
free -h | head -2
echo "=== disk ==="
df -h / | tail -1
echo "=== image digest for pilot task ==="
docker inspect --format '{{index .RepoDigests 0}}' ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan 2>&1
echo "=== wsl/kernel ==="
uname -a
