# Six-Case Validation — Performance

All figures are **offline diagnostic processing** only: no model execution, no
Docker replay. Machine: Windows 11 (10.0.26200), Python 3.13.15, 8 logical CPUs.
Method: one cold run (fresh file reads) + 5 warm runs per case; wall time via
`time.perf_counter()`; memory via `tracemalloc` peak during a cold diagnosis.
Raw data: `experiments/six_case_validation/raw_outputs/run_summary.json`,
`metrics.json`.

## Per-case latency and memory

| Case | Cold (ms) | Warm median (ms) | Warm samples (ms, n=5) | Cold peak (MB) |
|---|---:|---:|---|---:|
| c1_vuls | 71.41 | 58.31 | 55.9, 57.2, 61.3, 65.3, 92.7 | 2.30 |
| c2_teleport_synthetic | 8.87 | 11.18 | 5.6, 6.9, 8.2, 9.6, 11.5 | 1.02 |
| c3_elementweb_synthetic | 10.37 | 5.34 | 4.8, 5.1, 7.1, 9.4, 9.5 | 1.02 |
| c4_openlibrary | 33.41 | 42.96 | 32.2, 34.9, 40.7, 46.1, 58.5 | 1.74 |
| c5_infra | 5.42 | 5.51 | 3.1, 4.8, 5.9, 7.8, 8.4 | 1.01 |
| c6_adversarial | 10.54 | 10.37 | 6.5, 12.5, 12.9, 14.6, 18.3 | 1.02 |

## Summary

| Metric | Value |
|---|---|
| Six-case sum of warm medians | **133.67 ms** |
| Throughput (single process, offline) | **≈ 44.9 records/s** |
| Observed warm latency range | 5.3 ms – 58.3 ms |
| Max cold peak (diagnosis-only) | **2.30 MB** (vuls: large patch + trajectory) |
| Max process RSS floor | ~31 MB (interpreter + imports; see `reports/V3_3_LOCAL_SMOKE.md`) |

## Interpretation (honest)

- The dominant cost is **evidence ingestion** (reading the 245 KB vuls patch and
  the ~760 KB vuls trajectory). Small cases (c3, c5) run in single-digit ms.
- Memory is dominated by the largest trajectory; even that is ~2.3 MB incremental.
- The engine's own attribution/report logic is a small fraction of each run
  (previously measured at ~6 ms/record for the added V3.3 layer).
- **n = 5 warm samples per case is too small for a population p95.** The table
  reports the observed sample maximum, not a p95 estimate. No p95 is claimed.
- Extra execution cost attributable to the six-case experiment: **$0** (no API
  calls, no Docker, no GPU). Compute used: < 2 s CPU total.

## What this is not

These figures do **not** cover model execution or V3.2 oracle execution. The
synthetic Go/Node oracle reproductions used to establish ground truth took
~2.4 s (Go) and <0.1 s (Node) each and are ground-truth tooling, not part of the
diagnostic latency.
