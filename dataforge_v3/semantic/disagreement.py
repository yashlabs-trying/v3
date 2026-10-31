"""D. Verdict Disagreement Analyzer (V3.2).

Compares the official V2 verdict (and the V3.1 reliability classification)
against independent semantic evidence and explains any disagreement.

Decision policy (deliberately conservative; a *suspected* issue never becomes a
*confirmed* one automatically):

  * INVALID_EXECUTION      - V3.1 says the run was not valid; semantics moot.
  * CONFIRMED_INCORRECT    - V2 accepted, and a reproducible counterexample
                             falsifies a clause that the contract supports.
  * SUSPECTED_FALSE_PASS   - V2 accepted, probes failed a supported clause, but
                             the evidence is not yet independently reviewed /
                             reproducible (e.g. mutant-only signal).
  * SUSPECTED_FALSE_FAIL   - V2 rejected, but a verified-correct alternative is
                             rejected by the supplemental verifier.
  * SPECIFICATION_AMBIGUOUS- the only failing clauses are marked ambiguous.
  * CONFIRMED_CORRECT      - V2 accepted and every supported clause passes.
  * INCONCLUSIVE           - anything else (no executable evidence, oracle
                             could not run, mixed signals).
"""

from __future__ import annotations

from dataclasses import dataclass

from dataforge_v3.semantic.contract import ContractAudit
from dataforge_v3.semantic.model import (
    ClauseEvidence,
    ProbeOutcome,
    SemanticVerdict,
)


@dataclass
class DisagreementInput:
    v2_accepted: bool | None
    v3_1_invalid: bool
    contract: ContractAudit
    evidence: list[ClauseEvidence]
    mutants_missed: list[str]
    alternatives_rejected: list[str]
    oracle_ran: bool
    unmapped_failures: list[str] | None = None


@dataclass
class Disagreement:
    verdict: SemanticVerdict
    confidence: str
    failing_clauses: list[str]
    supported_failing_clauses: list[str]
    ambiguous_failing_clauses: list[str]
    reasons: list[str]


def analyze(inp: DisagreementInput) -> Disagreement:
    reasons: list[str] = []

    if inp.v3_1_invalid:
        return Disagreement(
            verdict=SemanticVerdict.INVALID_EXECUTION,
            confidence="high",
            failing_clauses=[],
            supported_failing_clauses=[],
            ambiguous_failing_clauses=[],
            reasons=["V3.1 classified the execution as invalid; semantics are not applicable"],
        )

    if not inp.oracle_ran:
        return Disagreement(
            verdict=SemanticVerdict.INCONCLUSIVE,
            confidence="low",
            failing_clauses=[],
            supported_failing_clauses=[],
            ambiguous_failing_clauses=[],
            reasons=["no executable semantic oracle ran for this submission"],
        )

    if inp.unmapped_failures:
        # A probe failed but could not be attributed to a clause (e.g. the
        # candidate failed to load or the harness did not run). This must never
        # be read as "everything passed".
        return Disagreement(
            verdict=SemanticVerdict.INCONCLUSIVE,
            confidence="low",
            failing_clauses=[],
            supported_failing_clauses=[],
            ambiguous_failing_clauses=[],
            reasons=[
                "probe failures could not be mapped to contract clauses",
                f"unmapped: {inp.unmapped_failures}",
            ],
        )

    failing = sorted({e.clause_id for e in inp.evidence if e.outcome is ProbeOutcome.FAIL})
    ambiguous_ids = set(inp.contract.ambiguous_clauses)

    # A clause is "supported" if the contract states it and it is not marked
    # ambiguous. Uncovered clauses are supported statements that the official
    # tests do not pin - exactly the false-PASS surface.
    supported_failing = [c for c in failing if c not in ambiguous_ids]
    ambiguous_failing = [c for c in failing if c in ambiguous_ids]

    if failing and not supported_failing and ambiguous_failing:
        return Disagreement(
            verdict=SemanticVerdict.SPECIFICATION_AMBIGUOUS,
            confidence="medium",
            failing_clauses=failing,
            supported_failing_clauses=[],
            ambiguous_failing_clauses=ambiguous_failing,
            reasons=["only ambiguous clauses failed"],
        )

    if inp.v2_accepted is True:
        if supported_failing and inp.alternatives_rejected == []:
            # Reproducible counterexample on a supported clause.
            reproducible = all(
                e.counterexample is not None
                for e in inp.evidence
                if e.outcome is ProbeOutcome.FAIL and e.clause_id in supported_failing
            )
            if reproducible:
                reasons = [
                    f"accepted submission falsifies supported clause(s) {supported_failing}",
                    "each failing clause has a concrete counterexample",
                ]
                if inp.mutants_missed:
                    reasons.append(f"additionally missed mutants: {inp.mutants_missed}")
                return Disagreement(
                    verdict=SemanticVerdict.CONFIRMED_INCORRECT,
                    confidence="high",
                    failing_clauses=failing,
                    supported_failing_clauses=supported_failing,
                    ambiguous_failing_clauses=ambiguous_failing,
                    reasons=reasons,
                )
            reasons = [
                f"accepted submission failed supported clause(s) {supported_failing} without a concrete counterexample",
            ]
            return Disagreement(
                verdict=SemanticVerdict.SUSPECTED_FALSE_PASS,
                confidence="medium",
                failing_clauses=failing,
                supported_failing_clauses=supported_failing,
                ambiguous_failing_clauses=ambiguous_failing,
                reasons=reasons,
            )
        if not failing:
            return Disagreement(
                verdict=SemanticVerdict.CONFIRMED_CORRECT,
                confidence="high",
                failing_clauses=[],
                supported_failing_clauses=[],
                ambiguous_failing_clauses=[],
                reasons=["accepted submission satisfies every supported clause"],
            )

    if inp.v2_accepted is False:
        if inp.alternatives_rejected:
            return Disagreement(
                verdict=SemanticVerdict.SUSPECTED_FALSE_FAIL,
                confidence="medium",
                failing_clauses=failing,
                supported_failing_clauses=supported_failing,
                ambiguous_failing_clauses=ambiguous_failing,
                reasons=[
                    "rejected submission includes alternative(s) the supplemental verifier also rejects",
                    f"rejected alternatives: {inp.alternatives_rejected}",
                ],
            )

    return Disagreement(
        verdict=SemanticVerdict.INCONCLUSIVE,
        confidence="low",
        failing_clauses=failing,
        supported_failing_clauses=supported_failing,
        ambiguous_failing_clauses=ambiguous_failing,
        reasons=reasons or ["no decisive semantic signal"],
    )
