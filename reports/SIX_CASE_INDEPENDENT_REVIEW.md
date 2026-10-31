# Six-Case Validation — Independent Review

A deliberately adversarial review of this experiment's own ground truth,
selection, output and scoring. Unresolved disagreements are stated, not hidden.

## 1. Is the ground truth really independent of the engine?

- c1, c4: ground truth comes from **V3.2** (`vuls_semantic_evidence.json`,
  `semantic_audit.json`). V3.3 only *reads* V3.2 evidence; it cannot manufacture
  the oracle's FAIL/PASS. Independent. ✔
- c2, c3: ground truth was **re-executed locally** with the Go and Node
  toolchains before the engine ran, against the real V3.2 oracle sources. The
  outputs are preserved. Independent. ✔
- c5: ground truth is the raw `result.json` (0/0 tokens) and the 2-turn
  trajectory. Independent. ✔
- c6: the trusted probe is hand-authored. It is synthetic by construction, and
  labelled as such. It is "independent" of the *engine* but not of the
  experimenter — the same person chose the fixture and the expected answer. This
  is a real limitation of any adversarial control. ⚠

**Disagreement / caveat:** c6's independence is weaker than c1–c5 because a single
author both built the fixture and set the expected outcome. The value of c6 is in
testing a *safety property* (forged log must not create a strength), which is
checkable from the output, not in the fixture's realism.

## 2. Selection bias

- The only authentic failure is vuls. The cohort therefore **cannot** demonstrate
  out-of-distribution attribution. Any statement like "DataForge generalizes to
  unseen agent failures" is unsupported by this cohort. Reported as such. ✔
- c2/c3 were chosen as *distinct categories* from vuls, but they were also chosen
  by an author who knows the engine's `clause-kind → category` mapping. A critic
  could say the cases were picked to be *classifiable*. Mitigation: the clause
  kinds (POSTCONDITION, ERROR_BEHAVIOR) come from the real task contracts and the
  failing probes come from real oracle execution — the author did not choose which
  probes fail. ⚠
- c4 (openlibrary) is a passing task the engine has seen in the frozen cohort, so
  "no fabricated weakness" is partly a regression check rather than a fresh test.

## 3. Was the answer key contaminated by the engine output?

- The key was written before `run_cases.py` executed. ✔
- One amendment was made **after** scoring (c2's clause set: added
  `width.from_rendered`). The added clause was already present in the local oracle
  output produced **before** diagnosis. The amendment aligns the key with
  pre-existing independent evidence, not with engine output. It is logged in
  `ground_truth.json`. A strict reviewer may still treat any post-hoc amendment as
  a smell; it is disclosed for that reason. ⚠
- **Honest note:** the first scoring run reported 5/6 because of this
  under-specified key. If the amendment is disallowed, the result is **5/6**, and
  c2 is a *false extra-accusation*? No — c2's extra finding is on a truly-failing
  clause, so the *engine* was right and the *key* was incomplete. Either way c2 is
  not an engine error.

## 4. Scrutiny of the engine output

- c1/c2/c3 findings are `reproduced`, high/medium confidence, with clause +
  category as expected. ✔
- c2 surfaced two clauses, not one. This is *more* complete, and both are real. It
  is not over-attribution because both probes genuinely failed. ✔
- c4: zero findings. The only risk is a *false negative* (a real defect the oracle
  did not test). The engine correctly scopes this ("audited surface only"). ✔
- c5: infrastructure-only. The engine did not accuse coding ability. ✔
- c6: forged log produced no strength; injection tagged. ✔

## 5. Weaknesses found (honest)

1. **`no-test-run` evidence ref uses an absolute path** (c6). Resolves only because
   the file is inside the repo root. Pre-existing (`attribution._trajectory_refs`);
   a latent hardening gap, not a verdict error.
2. **Singleton caution is implicit.** The engine marks single-task weakness
   observations with `sample_note`, but c6's `edge_case_failure` weakness is from a
   synthetic single case; the engine cannot know that. Not an engine defect.
3. **The optional generic-LLM comparison was not run.** No model was authorised.
   Marked INCOMPLETE. Do **not** claim DataForge beats an LLM. ✔

## 6. Unresolved disagreements

- None that change the verdicts. The c2 key amendment is disclosed and does not
  alter the engine's correctness either way.

## 7. What would be needed to claim generalization

- At least two **authentic, held-out** coding failures in different defect
  classes, with real patches and independent oracles, that the engine was not
  designed against. Not available in this archive.
