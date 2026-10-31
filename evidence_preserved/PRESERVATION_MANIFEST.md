# Evidence Preservation Manifest — mismatched final-vuls logs

**Date preserved:** 2026-10-31
**Freeze reference:** `evidence_checksums.txt` (mtime `2026-10-30 17:31:39 UTC`)
**Observed content mtime:** `2026-10-30 17:40:18 UTC` (both files)

These two files are the only checksum mismatches disclosed in
`reports/EVIDENCE_INTEGRITY_NOTE.md`. They were already rewritten ~9 minutes
after the checksum freeze, most likely by a late Harbor write to an incomplete
job directory. Nothing was repaired, truncated or overwritten. Byte-identical
copies of the observed WSL content are kept here so the mismatch remains
inspectable even though the WSL baseline lives outside this repository.

| File | Frozen (expected) sha256 | Preserved (observed) sha256 | Bytes | mtime (UTC) |
|---|---|---|---:|---|
| `job.log` | `a846370a6c7072fa33e2c6b08434c34b3ffc2969bc60a523416e73fd6abefae9` | `779a94682365c3f210f011513e71e89e3bedc8d25225be882f0d264bbd1baffb` | 10178 | 2026-10-30 17:40:18 |
| `instance_future-architect__vuls__8Cyvgz3/trial.log` | `c066a856234d856bed2249470566d62ae8b33cd13e67eb502e45ef1523e1dbef` | `fc1723f2061d8b5acc7449695b4539e166840fe63947c8cafb3cc17d2383e375` | 9972 | 2026-10-30 17:40:18 |

Source of the copies (untouched):
`/home/yashs/dataforge/experiments/v3_1_baseline/jobs/final-vuls/`

Copies were made with `cp --preserve=timestamps`, byte-for-byte. The hashes
above were reproduced independently on the Windows side with Python
`hashlib.sha256` over the preserved files.

## Scope of effect

`final-vuls` is an incomplete job (`n_running_trials=1`, empty `model.patch`,
no `verifier/output.json` or `verifier/reward.txt`). It is not the source of the
authoritative vuls outcome, which is `f3-vuls-a1` (completed, non-empty 4-file
patch, reward `0.0`). No verdict-bearing artifact is affected.

## Rule

A checksum mismatch is disclosed and preserved, never silently repaired.
