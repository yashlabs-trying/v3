# Thirty-Case Validation — Performance

All figures are **offline diagnostic processing only**. No model execution, no
Docker, no GPU. Machine: Windows 11 (10.0.26200), Python 3.13.15, 8 logical CPUs.
Method: 1 cold run + 5 warm runs per case; `time.perf_counter()` for wall time;
`tracemalloc` peak during the cold run. Raw data:
`experiments/thirty_case_validation/postfix_scores.json`, `performance.json`.

## Diagnostic latency and memory (30 cases)

| Metric | Value |
|---|---:|
| Warm median (per case) | min **2.24 ms**, median **10.73 ms**, max **50.80 ms** |
| Cold (per case) | min 2.28 ms, median 10.84 ms, max 60.21 ms |
| Sum of warm medians (whole cohort) | **315.7 ms** |
| Throughput (single process, offline) | **≈ 95 records/s** |
| Max cold peak (diagnosis-only) | **2.10 MB** |
| Evidence bytes processed | **1.18 MB** over 124 artifacts |

## Cost separation (do NOT conflate)

| Cost | Value |
|---|---|
| Diagnostic processing (per record) | 2–51 ms, evidence-ingestion dominated |
| Evidence ingestion | dominant share (file reads of patches / trajectories) |
| V3.3-added attribution + reporting | previously measured ≈ 6 ms/record |
| Independent oracle execution (ground truth) | pytest runs sub-second each; Go ≈ 2.4 s; Node ≈ 0.1 s — **not** part of diagnosis |
| Docker / container startup | 0 |
| External model cost | **$0** |

## Honest caveats

- Per-case n = 5 warm samples. Quantiles are **observed sample values**, not
  population estimates. No p95 is claimed.
- The largest cases (`auth_01_vuls`, `def_11`) are dominated by reading the large
  recorded vuls patch/trajectory; synthetic cases are small and fast.
- These figures say nothing about model-execution or V3.2 oracle-execution cost.
