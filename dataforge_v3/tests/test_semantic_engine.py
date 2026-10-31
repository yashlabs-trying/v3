"""Disagreement-analyzer and reporter tests (V3.2 modules D and E)."""

from __future__ import annotations

from dataforge_v3.semantic.contract import ContractAudit
from dataforge_v3.semantic.disagreement import DisagreementInput, analyze
from dataforge_v3.semantic.model import (
    ClauseEvidence,
    ContractClause,
    ClauseKind,
    ProbeOutcome,
    SemanticVerdict,
)


def _audit(uncovered=None, ambiguous=None):
    return ContractAudit(
        total_clauses=2,
        uncovered_clauses=uncovered or [],
        ambiguous_clauses=ambiguous or [],
    )


def _fail(clause_id, counterexample=True):
    return ClauseEvidence(
        clause_id=clause_id,
        probe="p",
        outcome=ProbeOutcome.FAIL,
        counterexample={"in": 1} if counterexample else None,
    )


def test_invalid_execution_short_circuits():
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=True,
            contract=_audit(),
            evidence=[],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=True,
        )
    )
    assert d.verdict is SemanticVerdict.INVALID_EXECUTION


def test_no_oracle_is_inconclusive():
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=False,
            contract=_audit(),
            evidence=[],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=False,
        )
    )
    assert d.verdict is SemanticVerdict.INCONCLUSIVE


def test_accepted_with_reproducible_counterexample_is_confirmed_incorrect():
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=False,
            contract=_audit(),
            evidence=[_fail("clause.a")],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=True,
        )
    )
    assert d.verdict is SemanticVerdict.CONFIRMED_INCORRECT
    assert d.confidence == "high"
    assert d.supported_failing_clauses == ["clause.a"]


def test_accepted_failure_without_counterexample_is_suspected_only():
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=False,
            contract=_audit(),
            evidence=[_fail("clause.a", counterexample=False)],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=True,
        )
    )
    assert d.verdict is SemanticVerdict.SUSPECTED_FALSE_PASS


def test_accepted_and_all_pass_is_confirmed_correct():
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=False,
            contract=_audit(),
            evidence=[],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=True,
        )
    )
    assert d.verdict is SemanticVerdict.CONFIRMED_CORRECT


def test_only_ambiguous_failures_is_ambiguous():
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=False,
            contract=_audit(ambiguous=["clause.amb"]),
            evidence=[_fail("clause.amb")],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=True,
        )
    )
    assert d.verdict is SemanticVerdict.SPECIFICATION_AMBIGUOUS


def test_rejected_with_rejected_alternative_is_suspected_false_fail():
    d = analyze(
        DisagreementInput(
            v2_accepted=False,
            v3_1_invalid=False,
            contract=_audit(),
            evidence=[],
            mutants_missed=[],
            alternatives_rejected=["alt1"],
            oracle_ran=True,
        )
    )
    assert d.verdict is SemanticVerdict.SUSPECTED_FALSE_FAIL


def test_unmapped_failure_is_inconclusive_not_correct():
    """A failing probe with no clause attribution must never read as correct."""
    d = analyze(
        DisagreementInput(
            v2_accepted=True,
            v3_1_invalid=False,
            contract=_audit(),
            evidence=[],
            mutants_missed=[],
            alternatives_rejected=[],
            oracle_ran=True,
            unmapped_failures=["deepseek:load"],
        )
    )
    assert d.verdict is SemanticVerdict.INCONCLUSIVE


def test_reporter_renders_counterexamples():
    from dataforge_v3.semantic.reporter import render_assessment
    from dataforge_v3.semantic.model import SemanticAssessment

    a = SemanticAssessment(
        task="t",
        task_id="id",
        submission="deepseek",
        v2_reward=1.0,
        v3_1_classification="PASS",
        verdict=SemanticVerdict.CONFIRMED_INCORRECT,
        confidence="high",
        clauses=[
            ContractClause(
                id="c1",
                kind=ClauseKind.POSTCONDITION,
                statement="s",
                source="instruction.md",
            )
        ],
        counterexamples=[{"in": 1, "out": 2}],
    )
    text = render_assessment(a, reproduce_command="python -m pytest")
    assert "CONFIRMED_INCORRECT" in text
    assert "Counterexample 1" in text
    assert "python -m pytest" in text
