"""Contract-audit tests (V3.2 module A)."""

from __future__ import annotations

from dataforge_v3.semantic.contract import (
    audit_contract,
    flag_unsupported_restrictions,
)
from dataforge_v3.semantic.model import ClauseKind, ContractClause


def _clause(id, tests):
    return ContractClause(
        id=id,
        kind=ClauseKind.POSTCONDITION,
        statement=f"behavior {id}",
        source="instruction.md",
        tested_by_original=tests,
    )


def test_contract_audit_separates_covered_and_uncovered():
    clauses = [
        _clause("a", ["T::x"]),
        _clause("b", []),
        _clause("c", ["T::y"]),
    ]
    audit = audit_contract(clauses, required_tests={"T::x"})
    assert audit.total_clauses == 3
    assert audit.uncovered_clauses == ["b", "c"]
    assert audit.evidence_strength["a"] == "official-tests:1"
    assert audit.evidence_strength["b"] == "uncovered"


def test_ambiguous_source_is_flagged():
    clauses = [
        ContractClause(
            id="x",
            kind=ClauseKind.EDGE_CASE,
            statement="unclear",
            source="AMBIGUOUS",
        )
    ]
    audit = audit_contract(clauses, required_tests=set())
    assert audit.ambiguous_clauses == ["x"]
    assert audit.uncovered_fraction == 1.0


def test_unsupported_restriction_detection():
    clauses = [
        ContractClause(
            id="c1",
            kind=ClauseKind.ERROR_BEHAVIOR,
            statement="must reject with errUnauthenticated",
            source="instruction.md",
        )
    ]
    unsupported = flag_unsupported_restrictions(
        ["asserts the exact panic message string"],
        clauses,
    )
    assert unsupported == ["asserts the exact panic message string"]
    supported = flag_unsupported_restrictions(["reject with errunauthenticated"], clauses)
    assert supported == []
