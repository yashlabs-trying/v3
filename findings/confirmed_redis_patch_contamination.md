# CONFIRMED DEFECT — NodeBB patch capture & replay

Classification: **CONFIRMED DEFECT** (harness/evidence-integrity), independent of the agent-startup failure.

## Summary
On Redis-backed NodeBB tasks, the locked-protocol `model.patch` capture is polluted by
pre-existing, untracked, non-source Redis AOF files that are baked into the upstream
container image. Consequently (a) `model.patch` can be composed entirely of binary state
rather than agent code, and (b) fresh-sandbox `patch_replay` silently applies nothing.

## Exact mechanism
1. The upstream image
   `ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7...`
   ships `/app/appendonlydir/` containing:
   - appendonly.aof.1.base.rdb   (89 B)
   - appendonly.aof.1.incr.aof   (149,888 B)
   - appendonly.aof.manifest     (88 B)
   These are dated 2025-07-07 (baked at image build), i.e. present BEFORE any agent run.
2. They are NOT tracked by git (`git ls-files appendonlydir/` is empty) and NOT listed in
   `.gitignore`. Therefore `git status` in a pristine container already reports `?? appendonlydir/`.
3. `locked_mini_swe.py` captures the patch with:
   `git add -A; git diff --cached > /logs/agent/model.patch; git reset -q`
   `git add -A` stages the untracked Redis files, so they are written into model.patch.
4. The captured NodeBB patch is 166,347 bytes whose only `diff --git` entries are the three
   appendonlydir files. There are ZERO source-code hunks. (Source sha256 of the patch is in
   evidence_checksums.txt.)
5. Replay (`patch_replay:PatchReplayAgent`, which runs
   `git apply --verbose ... || git apply --3way ... || patch --fuzz=3 -p1 ...`):
   - `git apply` fails: "appendonlydir/appendonly.aof.1.base.rdb: already exists in working directory"
     (because the files are already in the pristine image).
   - `git apply --3way` fails: "does not apply".
   - The `|| patch --fuzz=3` fallback also cannot create already-existing files.
   - Net effect: NOTHING is applied; the verifier runs on the pristine tree.
6. Because the replay command's final `||` returns success, Harbor does not treat the
   empty replay as an error; a reward is still produced.

## Consequence
- The "authoritative fresh-sandbox regrade" for NodeBB is a NULL REPLAY. It cannot reflect
  the agent's work, because the only content in model.patch is pre-existing binary state.
- If an agent DID edit source files, those edits would appear in model.patch alongside the
  Redis state; but git apply would still fail on the Redis entries first (git apply is
  atomic per file, and the patch fails overall), so source edits could also be dropped in
  naive replay. (Observed: replay applied nothing.)
- Reward 0.0 from NodeBB cannot be used as evidence about model coding ability.

## Reproduction (no official grading code modified)
```bash
IMG=ghcr.io/scaleapi/swe-bench_pro-v2:instance_NodeBB__NodeBB-00c70ce7...-vnan
docker run -d --rm $IMG sleep 300            # pristine image
docker exec <cid> bash -c 'cd /app && git status --short | head'   # shows: ?? appendonlydir/
P=<job>/instance_*/agent/model.patch          # 166347 bytes
docker cp "$P" <cid>:/tmp/replay.patch
docker exec <cid> bash -c 'cd /app && git apply --verbose /tmp/replay.patch; echo rc=$?'
# -> errors "already exists in working directory" for all three files
```

## Severity
High: undermines the authoritative regrade step for an entire task family (all NodeBB tasks,
38 in V2, and any repo that ships untracked runtime state in the image).
