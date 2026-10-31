# Performance and Cost — DataForge V3.3 (Phase H)

Machine-readable: `findings/intelligence/performance.json`. All figures from this
run on the recorded evidence (plus clearly-labelled synthetic scale tests).

---

## 1. Real cohort

| Metric | Value |
|---|---|
| Tasks analysed | 8 |
| Total fleet runtime | **~0.54 s** |
| Peak traced memory | **~6.4 MB** |
| Slowest task | vuls (~6 ms) |

Per-task analytic time is milliseconds; the engine is offline and deterministic.

## 2. Component timings

| Operation | Value |
|---|---|
| Parse one recorded trajectory (vuls, 188 events) | ~27 ms |
| Evidence-reference validation (2 refs × 1000 iters) | ~0.94 s (~0.94 ms/validation) |
| Findings derivation + report render per task | < 10 ms |

## 3. Scaling (synthetic, labelled `synthetic`)

`dedupe + stable-order` on synthetic event lists:

| Events | Seconds | Events/s |
|---:|---:|---:|
| 1,000 | 0.0028 | ~354,000 |
| 10,000 | 0.036 | ~277,000 |
| 100,000 | 0.237 | ~422,000 |

Scaling is linear in event count; no super-linear blowup observed.

## 4. Cost

| Item | Value |
|---|---|
| New model/API calls | **0** (offline analysis of frozen evidence) |
| Token cost | **0** |
| Wall-clock cost | < 1 s per cohort |
| LLM enrichment | not used; would be optional and isolated |

## 5. What is NOT claimed

- No million-event scalability claim: the largest measured point is 100k synthetic
  events, and the real trajectories are ~200 events.
- Concurrency throughput was not measured (analysis is trivially parallelisable by
  task but no multi-process benchmark was run); this is a documented gap, not a
  claim.
- The 0.94 ms/validation figure includes read-time hashing of a 245 KB patch; cold
  cache would be slower.

## 6. Reproduce

```bash
python -c "from pathlib import Path; from dataforge_v3.intelligence.performance import run_all; import json; print(json.dumps(run_all(Path('.')), indent=2))"
```
