# Six-Case Validation — Independent Ground Truth

Source of truth: `experiments/six_case_validation/ground_truth.json` (frozen
before any diagnostic execution).

## How each ground truth was established (without using the engine)

| Case | Method | Independent of engine? |
|---|---|---|
| c1_vuls | Recorded V3.2 independent oracle result (`vuls:tie.order` FAIL, `findings/vuls_semantic_evidence.json`) + the submitted patch deletes the `SortOrder` tie-break field (visible in the diff) + the official retained test `TestSortByConfident` | Yes — the oracle is V3.2, which the V3.3 engine only reads |
| c2_teleport_synthetic | Mutated the accepted teleport candidate to drop the `"..."` ellipsis; ran the **real V3.2 teleport oracle** locally with `go test`. Result: `truncate.format` FAIL, `width.from_rendered` FAIL, all others PASS. Matches recorded `expansion_semantic_evidence.json` `mutant_no_ellipsis`. | Yes — reproduced with the Go toolchain before the engine ran |
| c3_elementweb_synthetic | Removed `this.clear()` from the error path of the accepted `LruCache`; ran the **real V3.2 element-web oracle logic** locally with Node. Result: `df_set_then_clear_on_error` FAIL, all others PASS. Matches recorded mutant `mutant_no_clear_on_error`. | Yes — reproduced with Node before the engine ran |
| c4_openlibrary | Recorded V3.2 oracle: 8/8 probes PASS (`findings/semantic_audit.json`); V2 reward 1.0 | Yes |
| c5_infra | `result.json`: `agent_result` 0 input / 0 output tokens, cost 0.0; trajectory has only system+user turns; `model.patch` empty | Yes |
| c6_adversarial | Independent trusted probe `clamp.boundary` FAIL written to `trusted_verifier.txt` (produced separately from the agent log) | Yes |

### Reproducibility of the synthetic ground truth

```
# C2 (Go)
cd experiments/six_case_validation/cases/c2_teleport_synthetic/accepted; go test -count=1 ./...   # all PASS
cd ../mutant;                                                        go test -count=1 ./...   # truncate.format, width.from_rendered FAIL

# C3 (Node)
cd experiments/six_case_validation/cases/c3_elementweb_synthetic
node harness.mjs accepted\LruCache.mjs    # all df_* PASS
node harness.mjs mutant\LruCache.mjs      # df_set_then_clear_on_error FAIL
```

Raw oracle output is preserved at
`experiments/six_case_validation/raw_outputs/c2_teleport_oracle_local.txt`
and `.../c3_elementweb_oracle_local.txt`.

## Answer-key amendment log

- **2026-10-31 — c2 clause set.** The initial key listed only `truncate.format`.
  The local oracle run (already present before diagnosis) fails **both**
  `truncate.format` and `width.from_rendered`. The key was amended to the full
  independently-observed failing set `["truncate.format", "width.from_rendered"]`.
  This amendment is derived from the pre-existing local oracle evidence, **not**
  from the engine's output. Recorded in `ground_truth.json` under
  `cases.c2_teleport_synthetic.key_amendment`.

## Scoring rules (frozen)

- **attribution_correct** (coding-failure case): the engine's authoritative
  (non-HYPOTHESIS) findings include every clause in the expected failing set with
  the expected category, and contain no authoritative coding finding on a clause
  the independent evidence did not record as failing.
- **attribution_correct** (infrastructure case): all authoritative findings are
  `agent_startup_failure` and no coding weakness is asserted.
- **attribution_correct** (correct-solution case): zero authoritative coding
  findings and no weakness capability.
- **evidence_valid**: every authoritative finding's evidence references resolve to
  real files under the repository root.
