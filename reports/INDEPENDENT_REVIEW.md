# INDEPENDENT_REVIEW — DataForge V3.2 (Phase 2)

Purpose: challenge the Phase 2 method and results, and record what is and is not
independently established. Written adversarially.

## Rule compliance

| Requirement | Status |
|---|---|
| A second LLM must never be the sole ground truth | **complied** — no LLM is on the decision path; oracles are code |
| A suspected issue must not auto-become confirmed | **complied** — `disagreement.py` requires a reproducible counterexample on a supported, non-ambiguous clause |
| Original V2 score unchanged | **complied** — V3.2 emits a separate `SemanticAssessment`; it imports nothing that mutates rewards |
| V3.1 protections intact | **complied** — `dataforge_v3/semantic/*` is additive; no file under `model.py`, `reporting/`, `replay/`, `lifecycle/` was modified |
| Missing execution / parser / infra defects not reclassified as semantic | **complied** — analyzer returns INVALID_EXECUTION when V3.1 says invalid |

## Challenges to the findings

1. **"CONFIRMED_CORRECT" may be too strong.** The probes cover the declared
   contract, not all behaviour. The verdict means "no supported clause was
   falsified", not "correct in general". The naming is kept because it is scoped
   and the confidence field is `high` only for *contract* coverage, but a future
   revision should rename it or tie confidence to clause coverage explicitly.
   *(Accepted limitation; documented in FALSE_PASS_FINDINGS.md.)*

2. **Contract extraction is human-authored, hence fallible.** A missed clause
   shrinks the probe space and can hide a false PASS. Mitigation: clauses are
   data with a `source` and are individually reviewable; ambiguous clauses cannot
   produce a confirmed verdict. A reviewer should re-derive the flipt and
   openlibrary clauses from the instructions independently.

3. **The flipt oracle re-implements the instruction, not the real product.**
   Probes assert the exported interceptor's behaviour matching the contract. If
   the instruction is itself wrong about Flipt's intent, the oracle inherits that.
   Acknowledge: this measures conformance to the stated contract, which is the
   benchmark's statement of intent.

4. **A false alarm was found in the oracle.** An early version rejected a correct
   submission (removal-set ordering). This is disclosed, fixed, and guarded by a
   regression test. It shows the method can err; it also shows the mutation /
   alternative discipline catches it.

5. **The gold patch does not apply to the task image base.** `solution/gold_patch.diff`
   fails `git apply` and `--3way` at `middleware.go:2`. This does not affect the
   audit (gold was never used as authority) but is a benchmark-consistency issue
   worth reporting upstream.

6. **Selection bias.** Two tasks were chosen for oracle feasibility and risk,
   before observing outcomes. Findings do not generalize to the fleet.

## Security and regression review

- **No untrusted code on the host.** Candidate code is executed either in-process
  with all dangerous imports stubbed (`openlibrary`) or inside the task's Docker
  image (`flipt`). The loader execs the candidate module; it does not call its
  `main`/`__main__` guard (the module has no side effects at import because all
  heavy imports are stubbed). Sandbox boundary: the Go execution runs in the
  SWE-bench container, not the host.
- **No secrets introduced.** The engine reads candidate files and emits JSON;
  it writes no credentials. Grep of the new tree for key/token patterns is clean.
- **Determinism.** Probe generation is seeded; the openlibrary oracle is
  deterministic. The flipt oracle is deterministic given the same image. Set
  iteration order inside the *candidate* is now explicitly not constrained, so
  `PYTHONHASHSEED` does not affect the verdict.
- **Regression surface.** 90 tests pass on Windows and in a clean checkout
  (host independent). V3.1's 67 tests are unchanged and still pass.

## Verdict of this review

The Phase 2 method is sound enough to accept as a *methodology demonstration*
with the limitations above. The specific negative finding (no false PASS/FAIL in
the two tasks) is credible but narrow. The strongest defensible claims are:
correct alternatives are accepted, genuine mutants are rejected, and one real
oracle false alarm was caught and fixed.
