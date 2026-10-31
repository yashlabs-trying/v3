# Reproduction Steps — DataForge V3.1 Phase 1A

All commands run inside WSL Ubuntu. Audit dir: `/home/yashs/dataforge/experiments/v3_1_baseline`.
Upstream commit: 66f92766bba642462d4bbe5479e83f91f9211862 (unmodified).

## 0. Setup
```bash
uv tool install harbor               # harbor 0.25.0
git clone https://github.com/scaleapi/SWE-bench_Pro-os
# LF mirror to avoid Windows CRLF (same commit):
git -c core.autocrlf=false clone file:///home/yashs/SWE-bench_Pro-os upstream_lf
find upstream_lf -type f \( -name '*.sh' -o -name '*.py' \) -exec sed -i 's/\r$//' {} +
```

## 1. Controls (oracle/no-op) — expected 1.0 / 0.0
```bash
cd upstream_lf
PYTHONPATH=v2/tooling harbor run -p v2/tasks -i <TASK> -e docker -n 1 -a oracle
PYTHONPATH=v2/tooling harbor run -p v2/tasks -i <TASK> -e docker -n 1 -a nop
```

## 2. Pre-baked agent image (network resilience)
```bash
bash build_agent_image.sh ghcr.io/scaleapi/swe-bench_pro-v2:<TASK>   # -> dataforge-agent:<TASK>
```
The audit overlay `audit_tasks/<TASK>/task.toml` sets `docker_image = "dataforge-agent:<TASK>"`;
tests/parser/config/instruction are byte-identical to upstream.

## 3. DeepSeek run (locked protocol)
```bash
cd upstream_lf
PYTHONPATH=tooling_overlay:v2/tooling harbor run -p audit_tasks -i <TASK> -e docker -n 1 \
  -a locked_mini_swe:LockedMiniSwe --agent-setup-timeout-multiplier 6 \
  -m openai/deepseek-ai/DeepSeek-V4.1-Flash \
  --ak config_file=tooling_overlay/mini_toolcall_audit.yaml \
  --ae OPENAI_API_KEY=... --ae OPENAI_BASE_URL=https://api.deepinfra.com/v1/openai \
  --allow-agent-host api.deepinfra.com --job-name <job>
```
(tooling_overlay/mini_toolcall_audit.yaml adds model_kwargs: timeout 120, num_retries 3, stream false.)

## 4. Fresh-sandbox regrade (authoritative)
```bash
cd upstream_lf
PYTHONPATH=tooling_overlay:v2/tooling harbor run -p v2/tasks -i <TASK> -e docker -n 1 \
  -a patch_replay:PatchReplayAgent -m replay --ak source_job=jobs/<job> --job-name regrade-<short>
```

## 5. The null-replay defect (independent proof, no official grading changed)
```bash
IMG=ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7...-vnan
CID=$(docker run -d --rm $IMG sleep 300)
docker exec $CID bash -lc 'cd /app && git status --short'   # shows ?? appendonlydir/
docker cp <job>/instance_*/agent/model.patch $CID:/tmp/replay.patch
docker exec $CID bash -lc 'cd /app && git apply --verbose /tmp/replay.patch; echo rc=$?'
# -> "already exists in working directory" for all three appendonlydir files
```

## 6. Stall reproduction + fix
- Stall: run agent; transcript stops at ~8.3 KB (prompt only); sidecar log shows ~892 s held connection.
- Fix: `stream:false`, `timeout:120`, `num_retries:3` in the agent model_kwargs.

## 7. Stability check
```bash
for i in 2 3; do PYTHONPATH=v2/tooling harbor run -p v2/tasks -i <flipt-task> -e docker -a oracle \
  --job-name repeat-oracle-flipt-$i; done   # expects 1.0, 1.0, 1.0
```
