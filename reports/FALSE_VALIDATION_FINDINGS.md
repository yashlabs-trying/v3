# False Validation Findings — DataForge V3.1 Phase 1A

Focus: could the evaluator accept bad evidence, or reject good evidence, incorrectly?

## FALSE PASS — none confirmed
- 5 DeepSeek passes were each checked against raw test output; all required tests were genuinely
  present and PASSED (flipt 13/13, openlibrary 3/3, teleport 3/3, ansible 48/48, elementweb 163/163).
- No case was found where a required test was absent yet the verdict was PASS.
- Structural safety: `success = all_required <= passed_tests` requires every required test to be
  observed PASSED; absence yields FAIL. Empty/partial output cannot produce a spurious pass.

## FALSE FAIL — one SUSPECTED (infrastructure-caused)
- nodebb original: reward 0.0 with **no model responses** (agent never ran). The 0.0 is a false
  representation of model ability, but it is an INFRASTRUCTURE failure, not a grader defect.
- Evidence: `agent/mini-swe-agent.txt` = prompt only; no trajectory; `model.patch` = Redis only.
- Recovery rerun (separately labelled) = 1.0.

## NULL REPLAY — CONFIRMED DEFECT (closest analogue to H8/H10)
- nodebb original regrade: `apply_rc=1`, no diff applied, yet reward 0.0 returned.
- The regrade "agrees" with the original only because both describe an unchanged pristine tree.
- This is the mechanism by which a broken/invalid capture can pass through regrade unnoticed.

## CONTRADICTORY EVIDENCE — none observed
- No task produced a required test appearing as both PASSED and FAILED.
- Parser dedup-by-name (openlibrary) is the theoretical locus; not triggered.

## EMPTY/INCOMPLETE EVIDENCE ACCEPTANCE — none observed
- Where output was empty (nodebb original), the verdict was correctly FAIL. The vulnerability is not
  that empty evidence passes; it is that a *contaminated* patch can silently become *empty* on replay
  while still yielding a verdict.

## Conclusion
No confirmed false PASS. One suspected false FAIL, caused by infrastructure, not grading logic.
One confirmed structural defect (null replay) that could mask invalid submissions.
