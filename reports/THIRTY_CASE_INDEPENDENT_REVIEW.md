# Thirty-Case Validation — Independent Review

Adversarial self-review of ground truth, selection, engine output, scoring and the
fix process. Unresolved disagreements are stated.

## 1. Ground-truth independence

- Controlled defects: the failing-probe sets come from running the **real pytest
  oracle** (`builder/run_oracles.py`), not from hand assertion and not from the
  engine. Re-runnable. ✔
- Correct solutions: verified to pass the same oracles. ✔
- vuls: recorded V3.2 oracle + patch inspection. ✔
- Adversarial: the trusted failing probe is authored next to the fixture (one
  author for both), a real limitation of any adversarial control. Its value is the
  *safety property* it checks, not realism. ⚠

## 2. Selection bias

- Real mechanisms and real oracles were used, but the **12 defect mechanisms were
  chosen by an author who knows the engine's clause-kind → category mapping**. A
  critic can say the cohort is tuned to be classifiable. Mitigation: the clause
  kinds come from the mechanisms themselves; the failing probes come from the real
  oracle. ⚠
- Only **one** authentic failure exists (vuls). This cohort **cannot** establish
  generalization to unseen authentic agent failures. Stated everywhere. ✔
- Correct-solution cases are all synthetic (real mechanisms, but not agent
  submissions). A false-accusation result on six synthetic corrects is weaker than
  on six real passing submissions; the four REUSED correct tasks (six-case cohort)
  partially cover this.

## 3. The fix process (anti-overfitting check)

- **One** engine attribution change was made: contradictory-probe downgrade. It is
  a *general* rule with regression tests, not a task special-case. ✔
- Four of the six first-pass mismatches were **answer-key corrections** (the
  documented INVARIANT→requirement_omitted fallback), not engine changes. The key
  change is disclosed and derived from documented engine behaviour + fixture shape,
  not from output tuning. ⚠ (a strict reviewer will treat post-hoc key edits as a
  smell; they are logged).
- **No** task-specific `if task == ...` rule was added. Verified by the existing
  not-hardcoded test and the adapter's no-special-case test. ✔
- Two pre-existing latent defects were surfaced by the hardening and fixed
  generally (absolute-path evidence ref; broad evidence trust). ✔

## 4. Scrutiny of results

- 30/30 with 0 false accusations and 0 infra→model confusions is suspiciously
  clean; it is explained by the cohort being controlled and the key accepting the
  documented fallback. The **strict-category** rate is 26/30, and that gap is
  disclosed rather than hidden. 
- `def_01`/`def_11`/`auth_02` emit two clause findings; both correspond to genuine
  oracle failures, so this is completeness, not over-attribution. ✔
- `no-test-run` process findings appear on adversarial cases; they are `observed`,
  low-confidence, and about the fixture. Not a coding accusation. ✔

## 5. Evidence integrity

- Security fix verified before/after: pre-fix 8/11 expectations, post-fix 11/11.
  `.git/config` and answer keys are no longer reachable as evidence. ✔
- All 30 cases resolve every authoritative reference (0 unresolved). ✔

## 6. Unresolved disagreements

- None that change the verdict. Disclosed caveats: single-author adversarial
  controls; synthetic correct solutions; post-hoc key amendments.

## 7. What would justify a GO (vs CONDITIONAL GO)

At least two **authentic, held-out** failures in different mechanisms, plus correct
solutions drawn from real agent submissions. Not available in this archive; a new
model campaign was not authorised.
