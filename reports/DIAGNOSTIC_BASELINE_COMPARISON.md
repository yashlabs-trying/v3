# Diagnostic Baseline Comparison — DataForge V3.3 (Phase G)

Machine-readable: `findings/intelligence/diagnostic_baseline_comparison.json`.
Answer key: independently-reviewed, in `dataforge_v3/intelligence/comparison.py`.

---

## 1. Design

Four approaches over the same frozen cohort and the same permitted evidence,
scored against an answer key that states the expected defect clause (or none) and
forbidden unsupported accusations:

- **A — raw benchmark report:** V2 verdict + observable failing test line +
  execution metadata.
- **A+ — raw + semantic:** A plus the V3.2 independent semantic findings (which
  name the failing probe and clause). This isolates the value of *additional
  semantic evidence*.
- **B — generic LLM:** a frozen prompt (`FROZEN_LLM_PROMPT`) over the same
  evidence. **Reported INCOMPLETE**: no external model execution was authorized,
  so no inputs/outputs were captured. It is not fabricated.
- **DF — DataForge V3.3:** the structured engine.

The design isolates the *semantic-evidence* contribution (A vs A+) from the
*diagnostic-engine* contribution (A+ vs DF).

## 2. Results

| Approach | Defects identified | Unsupported accusations | Unresolved evidence refs | Actionable recommendations | Tasks |
|---|---:|---:|---:|---:|---:|
| A raw benchmark | 0 / 1 | 0 | 0 | 0 | 8 |
| A+ raw + semantic | 1 / 1 | 0 | 0 | 0 | 8 |
| B generic LLM | INCOMPLETE | — | — | — | 0 |
| DF DataForge V3.3 | 1 / 1 | 0 | 0 | 1 | 8 |

Interpretation:

- **Clause-level attribution** (the exact violated contract clause) is only
  achieved where the V3.2 evidence names clauses — A+ and DF. Raw reporting
  identifies neither clause nor clause kind.
- **Actionability** is unique to DF: only it turns the finding into a measurable
  experiment (hypothesis + intervention + control + metric).
- **No approach** produced an unsupported accusation on this cohort; the specific
  advantage of DF over A+ here is structure (clause category, severity, competing
  explanations, recommendation), not headline accuracy.
- The **generic LLM** comparison is incomplete; the value of structured diagnosis
  over free text is therefore *not yet measured* on this cohort.

## 3. Measurement caveats (disclosed)

- The forbidden-phrase check is order- and negation-aware
  (`_is_unsupported_accusation`): an early naive version falsely flagged the
  correct statement "it does not evidence any model coding weakness". This is
  recorded because a contrast harness that punishes correct negations would be
  dishonest.
- n = 1 defect across 8 tasks. The comparison shows *capability differences*, not
  statistical rates.

## 4. Reproduce

```bash
python -c "from pathlib import Path; from dataforge_v3.intelligence.comparison import run_comparison; import json; print(json.dumps(run_comparison(Path('.'))['approaches'], indent=2))"
```
