# Evidence Integrity Note — Phase 1B

**Status:** disclosed, not hidden. The mismatch does not change any authoritative verdict.

## What was checked

`evidence_checksums.txt` has 42 entries covering three job directories:

| Job | Entries | Verified OK | Mismatched |
|---|---:|---:|---:|
| `final-nodebb` | 17 | 17 | 0 |
| `final-flipt` | 18 | 18 | 0 |
| `final-vuls` | 7 | 5 | 2 |
| **Total** | **42** | **40** | **2** |

Verification was run in the WSL baseline copy at
`/home/yashs/dataforge/experiments/v3_1_baseline` with `sha256sum -c evidence_checksums.txt`.

## Mismatches

| File | Expected (frozen) | Actual (current) |
|---|---|---|
| `jobs/final-vuls/job.log` | `a846370a6c7072fa33e2c6b08434c34b3ffc2969bc60a523416e73fd6abefae9` | `779a94682365c3f210f011513e71e89e3bedc8d25225be882f0d264bbd1baffb` |
| `jobs/final-vuls/instance_future-architect__vuls__8Cyvgz3/trial.log` | `c066a856234d856bed2249470566d62ae8b33cd13e67eb502e45ef1523e1dbef` | `fc1723f2061d8b5acc7449695b4539e166840fe63947c8cafb3cc17d2383e375` |

### Timing

- `evidence_checksums.txt` mtime: `2026-10-30 17:31:39 UTC`
- Both mismatched logs mtime: `2026-10-30 17:40:18 UTC`

The logs were appended/rewritten about nine minutes after the checksum file was frozen.

Byte-identical copies of the observed (mismatched) content are preserved in
`evidence_preserved/final-vuls/`, with both hashes recorded in
`evidence_preserved/PRESERVATION_MANIFEST.md`. The originals were not repaired
or overwritten.

### Why this does not affect the verdict

1. Both mismatched files are mutable run logs, not verdict-bearing artifacts.
2. The affected job (`final-vuls`) is **incomplete**: its job-level `result.json` reports
   `n_running_trials=1`, and the trial has an empty `model.patch` and no
   `verifier/output.json` or `verifier/reward.txt`.
3. The authoritative vuls baseline is `f3-vuls-a1`, a completed job with a
   non-empty 4-file patch, verifier output, and reward `0.0`. None of its files
   are covered by the mismatched entries.
4. All 35 checksum entries for `final-nodebb` and `final-flipt` match.
5. The checksum file is evidence of historical state, not an input to the
   DataForge classifier. DataForge reads artifacts and records their hashes; it
   does not rewrite missing entries or assume a match.

## Related checks

- `selection_manifest.json`: **28 / 28** selected-task grading-file hashes match.
- Window/PC checkout: text files are stored with CRLF, so their raw hashes differ
  from the WSL baseline even when content is equivalent. All historical checksum
  verification was therefore performed in WSL.
- DataForge normalizes CRLF to LF before parsing/applying patches. The normalized
  flipt patch hash is `84d420e01cae3b638f55ccb24f856e769b67c0fd9eed993bb7a4e4c9cf785bee`,
  matching the frozen value.

## Recommendation

For Phase 2:

1. Freeze checksums over immutable, final job directories only.
2. Exclude `job.log` and `trial.log` from verdict-critical manifests, or mark them
   explicitly as mutable/non-authoritative.
3. If mutable logs must be retained, record both the freeze timestamp and the
   expected append-only policy, and verify the log content hash is a prefix of
   the current content rather than an equality check.
4. Keep the rule that a checksum mismatch is disclosed in the report, never
   silently repaired.
