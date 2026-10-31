# PERFORMANCE_AND_COST — DataForge V3.2 (Phase 2)

Measured on the development machine (Windows host; Docker in WSL Ubuntu).
These are wall-clock, single-run, not statistical.

## Semantic audit cost (per submission)

| Task | Oracle kind | Probes | Wall time | Dominant cost |
|---|---|---:|---:|---|
| openlibrary | in-process Python | 8 | **0.03 s** | negligible |
| flipt | Docker + `go test` | 14 subtests | **62.4 s** | container start + Go build/compile |

## Engine-only cost (no task execution)

| Operation | Time | Notes |
|---|---:|---|
| Contract audit (6 clauses) | < 1 ms | pure logic |
| Probe generation (openlibrary, 8 cases) | < 1 ms | deterministic, seeded |
| Disagreement analysis | < 1 ms | pure logic |
| Full unit suite (90 tests) | ~3 s | includes all semantic tests |

## Interpretation

- The semantic layer adds **no cost** to the V2/V3.1 path. It is a separate audit.
- Per-submission cost is dominated by the need to execute candidate code:
  in-process oracles are essentially free; containerized Go oracles pay a fixed
  ~1 minute for build/startup regardless of probe count. Batching multiple
  candidates into one container (as the mutation runs did) amortizes this.
- No GPU, no network, no model calls are required for the oracles. A second LLM
  is intentionally not on the critical path (`INDEPENDENT_REVIEW.md`).

## Cost to reproduce

| Artifact | Cost |
|---|---|
| `python -m pytest dataforge_v3/tests -q` | ~3 s |
| openlibrary audit | ~0.03 s |
| flipt audit | ~1 min (Docker) |
| Full mutation sweep (openlibrary in-process) | ~0.1 s |
| Full mutation sweep (flipt, 4 mutants, 4 container runs) | ~4 min |
