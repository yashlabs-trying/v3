# Thirty-Case Validation — Reproduction Guide

Everything is offline: no model API calls, no Docker, no GPU.

## Freeze point

| Item | Value |
|---|---|
| Local repo | `C:\Users\yashs\dataforge\v3` |
| Base branch | `v3.3-phase3` @ `6529401f362725acbb0be276ad9ec3e4d5b9ff05` |
| Working branch | `six-case-validation` (carries the six-case work too) |
| Python | 3.13.15 |
| Toolchains for ground truth | pytest, Go 1.27, Node 26.7 |

## Added/changed code

| File | Change |
|---|---|
| `dataforge_v3/intelligence/evidence.py` | **Security fix:** approved-evidence-root containment; reject absolute/UNC/traversal and any path outside `jobs`/`findings` + declared roots. |
| `dataforge_v3/intelligence/attribution.py` | **General fix:** contradictory probe evidence on one clause downgrades to hypothesis; trajectory refs normalised to repo-relative. |
| `dataforge_v3/intelligence/case_adapter.py` | Generic case-manifest adapter (from the six-case work) + `evidence_roots` support. |
| `dataforge_v3/cli.py` | `diagnose-case` subcommand. |
| `dataforge_v3/tests/test_intelligence_engine.py` | +9 tests (containment, trajectory normalisation, contradiction). |
| `dataforge_v3/tests/test_case_adapter.py` | +7 tests. |

## Steps

```powershell
# 0. regression safety
python -m pytest dataforge_v3/tests -q          # 154 passed

# 1. evidence-path security: reproduce pre-fix and post-fix
#    (pre-fix uses the committed evidence.py; post-fix uses the working tree)
git show HEAD:dataforge_v3/intelligence/evidence.py > $env:TEMP\evidence_orig.py
python experiments/thirty_case_validation/security/_run_prefix.py $env:TEMP\evidence_orig.py
python experiments/thirty_case_validation/security/reproduce_security.py --root . --label post-fix
# pre-fix: 8/11 expectations met ; post-fix: 11/11

# 2. rebuild the frozen cohort (deterministic)
python experiments/thirty_case_validation/builder/run_oracles.py      # real pytest oracle ground truth
python experiments/thirty_case_validation/builder/build_cohort.py     # 30 cases + frozen manifests
python experiments/thirty_case_validation/builder/build_evidence_manifest.py

# 3. run the engine (post-fix tree)
python experiments/thirty_case_validation/run_cases.py --label postfix
python experiments/thirty_case_validation/score_cases.py --label postfix
# postfix: correct 30/30 | evidence 30/30 | unresolved 0
```

## Answer-key isolation

`ground_truth.json` is never read by the engine. A case is described only by its
`manifest.json` (evidence locations + V3.1/V3.2 labels). The engine derives findings
from evidence content; it has no access to the expected clause or category.

## Pre-fix / post-fix raw results

- `original_scores.prefix.json` / `original_comparison.prefix.json` — the very first
  run (naive key) before any fix.
- `original_scores.json` — the pre-contradiction-fix engine scored against the
  adjudicated key (29/30).
- `postfix_scores.json` / `postfix_comparison.json` — after the general fixes (30/30).
- `raw_outputs/original/` and `raw_outputs/postfix/` — full per-case JSON + Markdown.
