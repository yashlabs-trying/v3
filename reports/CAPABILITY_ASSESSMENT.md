# Capability Assessment — DataForge V3.3 (System C)

## 1. Design rule

The engine reports **counts of verified observations tied to specific tasks**. It
never emits an ability score, percentage or ranking. A single task can produce a
capability *observation*, never a general claim about a language, framework or
domain.

- Valid output: "Observed on vuls: removal of an established, test-covered
  ordering invariant (one observation)."
- Invalid output (never produced): "DeepSeek is 42% weaker at understanding
  existing code."

## 2. Taxonomy

`requirements_preservation, codebase_investigation, correct_implementation,
testing_discipline, regression_avoidance, debugging, tool_usage, api_compatibility,
state_and_concurrency, error_recovery`.

Mapping is generic: a finding's `category` maps to a dimension (e.g.
`existing_behavior_removed → regression_avoidance`); infrastructure categories map
to **no** dimension, so an invalid run yields no capability weakness.

## 3. Observation schema

`dimension, polarity(strength|weakness), statement, task_id, clause_ids[],
evidence[], n_events, confidence, kind`.

`n_events` = number of independent evidence items; it makes small samples visible.

## 4. Aggregation

`aggregate_observations` groups by dimension and returns, per dimension:
`observations`, `n_tasks`, `strength_tasks[]`, `weakness_tasks[]`, and a
`sample_note`. When `n_tasks <= 1` the note is
`"single-task observation; not a general ability claim"`.

## 5. This cohort's preliminary profile

| Dimension | Observations | n_tasks | Strength tasks | Weakness tasks |
|---|---:|---:|---|---|
| correct_implementation | 2 | 2 | openlibrary, vuls | — |
| regression_avoidance | 1 | 1 | — | vuls |
| testing_discipline | 7 | 7 | all valid tasks | — |

Interpretation, stated conservatively:

- **One verified weakness**: vuls removed an established ordering invariant. This
  is a single observation; it does not establish a general defect in the model's
  regression behavior.
- **Demonstrated strengths**: independent probes passed on the audited surface of
  openlibrary and, for the score-ordering clause only, vuls; tests were observed
  being run on all seven valid tasks.
- NodeBB original contributes **no** capability observation (INVALID).

## 6. Uncertainty

Counts are over a small, controlled, non-random cohort of seven tasks with
heterogeneous audit depth (element-web is LruCache-only; NodeBB has no oracle).
The profile is preliminary and explicitly non-calibrated.
