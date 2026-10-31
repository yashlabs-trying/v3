# Six-Case Validation — Reproduction Guide

Everything here is offline: no model API calls, no Docker, no GPU. Total wall
time is a few seconds once the checkout exists.

## Freeze point

| Item | Value |
|---|---|
| Local repo | `C:\Users\yashs\dataforge\v3` |
| Upstream | `https://github.com/yashlabs-trying/v3` |
| Base branch | `v3.3-phase3` |
| Base revision | `6529401f362725acbb0be276ad9ec3e4d5b9ff05` |
| Working branch | `six-case-validation` (isolated; base branch untouched) |
| Python | 3.13.15 |
| Node (synthetic C3 oracle reproduction) | 26.7.0 |
| Go (synthetic C2 oracle reproduction) | 1.27.0 |

The frozen V3.1/V3.2/V3.3 research evidence under `findings/intelligence/` was
restored to its committed state after the run (`git checkout -- findings/intelligence/`);
the only tracked file changed is `dataforge_v3/cli.py` (an added subcommand).

## Added code (smallest necessary interface)

| File | Role |
|---|---|
| `dataforge_v3/intelligence/case_adapter.py` | Generic case-manifest loader; builds `TaskEvidence` + `SemanticInput` and calls the **existing** engine functions. No task special-casing. |
| `dataforge_v3/cli.py` | New `diagnose-case --manifest <path> --root . --out <path>` subcommand. |
| `dataforge_v3/tests/test_case_adapter.py` | 7 offline tests challenging the generic adapter. |
| `experiments/six_case_validation/` | Frozen manifests, ground truth, raw outputs, metrics, comparison, runner + scorer. |

No attribution/reporting logic was rewritten. The adapter calls
`attribution.attribute`, `driver._downgrade_unresolved`, `driver._strengths_from_semantic`,
`capabilities.analyze_capabilities`, `recommendations.recommend_for_findings`, and the
existing `reporting` renderers.

## Reproduction steps

```powershell
# 1. from the base checkout
git checkout v3.3-phase3
git checkout -b six-case-validation

# 2. regression safety (Gate A)
python -m pytest dataforge_v3/tests -q
# expected: 143 passed (136 pre-existing + 7 adapter tests)

# 3. reproduce the synthetic C2 ground truth independently (Go, no Docker)
cd experiments/six_case_validation/cases/c2_teleport_synthetic/accepted; go test -count=1 ./...
cd ../mutant;                                                        go test -count=1 ./...
# accepted: all subtests PASS; mutant: truncate.format + width.from_rendered FAIL

# 4. reproduce the synthetic C3 ground truth independently (Node, no jest)
cd ../../c3_elementweb_synthetic
node harness.mjs accepted\LruCache.mjs   # exit 0, all df_* PASS
node harness.mjs mutant\LruCache.mjs     # df_set_then_clear_on_error FAIL

# 5. run the engine over the six cases and capture raw outputs
python experiments/six_case_validation/run_cases.py

# 6. score against the frozen key
python experiments/six_case_validation/score_cases.py
```

## Data flow / answer-key isolation

```
cases/<id>/manifest.json  (evidence locations + V3.1/V3.2 labels)
        |
        v
case_adapter.load_case_evidence -> TaskEvidence
case_adapter._build_semantic   -> SemanticInput
        |
        v
existing engine: attribute -> downgrade -> capabilities -> recommendations -> Diagnosis
        |
        v
raw_outputs/<id>.diagnosis.{json,md}

ground_truth.json  (frozen independently)  --\
comparison.json    (scorer) <---------------/
```

`ground_truth.json` is never read by the engine. The engine only ever sees the
per-case `manifest.json`, which contains evidence and lower-layer labels — never
the expected answer.

## Determinism

Run `python experiments/six_case_validation/run_cases.py` twice: the verdicts,
findings, clauses, categories and strengths are identical. Only `runtime_seconds`
in the diagnostic JSON differs between runs.
