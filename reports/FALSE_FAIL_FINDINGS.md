# FALSE_FAIL_FINDINGS — DataForge V3.2 (Phase 2)

Question: did the benchmark reject a solution that is genuinely correct, because
the grader is too strict, incomplete, or inconsistent with the task text?

Method: the same contracts and oracles as `FALSE_PASS_FINDINGS.md`, applied in
reverse. A suspected false FAIL requires an independently verified **correct
alternative** that the official grader would reject. The supplemental verifier
must itself accept every correct alternative (`MUTATION_TEST_RESULTS.md`).

## Result: no confirmed false FAIL in the selected submissions

Both selected submissions were **accepted by V2** (reward 1.0), so the false-FAIL
question in its strict form (V2 rejected something correct) does not arise for
them. V3.2 therefore evaluated two related questions:

1. **Would V3.2 reject a correct solution?** No. The `unordered` alternative for
   openlibrary and the DeepSeek submissions themselves are accepted. This is the
   false-alarm guard required by the acceptance criteria.
2. **Does the official required-test set demand behaviour the contract does not
   authorize?** Not observed. Every official assertion for both tasks maps to a
   contract clause or is neutral (error identity, which the contract states).

## The one task in the pilot that V2 rejected

`vuls` is the single genuine FAIL in the frozen pilot (66/67 required tests; one
`TestSortByConfident` failure). It is **not** in the Phase 2 two-task selection
(oracle feasibility is low for its broad Go surface). Based on the instruction
text, its requirements (confidence-type rename, `CpeVendorProductMatch` score 10,
JVN-vs-NVD sourcing, TUI score rendering) are largely expressible as contract
clauses, so it is the leading candidate for the expansion cohort's false-FAIL
investigation. No conclusion is drawn about it here.

## Parser-level false-FAIL surface (not observed, still noted)

Both official `test.sh` graders use `success = all_required <= passed_tests`. A
required test whose output is parsed away (missing/renamed) becomes a FAIL even
if it passed. For openlibrary the parser dedups by name (last wins). V3.1 already
owns detection of parser-drop / contradictory evidence; V3.2 does not reclassify
those as semantic defects, per the phase separation rule.

## Honest boundary

No false FAIL is confirmed or even strongly suspected in the two selected tasks.
This may simply mean the selected tasks are not where false FAILs live. That is a
valid Phase 2 outcome; it is not evidence that false FAILs do not occur in
SWE-bench Pro V2 generally.
