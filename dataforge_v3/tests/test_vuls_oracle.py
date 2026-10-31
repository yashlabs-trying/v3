"""Offline tests for the vuls semantic oracle plumbing (V3.2 expansion)."""

from __future__ import annotations

from dataforge_v3.semantic.contract import audit_contract
from dataforge_v3.semantic.executors import parse_vuls_probe_output
from dataforge_v3.semantic.tasks.vuls import (
    CONTRACT,
    REQUIRED_TESTS,
    clauses_for_probe,
    generate_go_oracle,
)


def test_vuls_oracle_source_has_properties():
    src = generate_go_oracle()
    assert "TestDataForgeVulsOrdering" in src
    assert 't.Run("score.order"' in src
    assert 't.Run("tie.order"' in src
    assert "CpeVendorProductMatch" in src


def test_parse_vuls_output_maps_ordering_properties():
    out = (
        "=== RUN   TestDataForgeVulsOrdering\n"
        "=== RUN   TestDataForgeVulsOrdering/score.order\n"
        "--- PASS: TestDataForgeVulsOrdering/score.order (0.00s)\n"
        "--- FAIL: TestDataForgeVulsOrdering/tie.order (0.00s)\n"
        "FAIL\n"
    )
    results = parse_vuls_probe_output(out)
    by_name = {r.name: r for r in results}
    assert set(by_name) == {"vuls:score.order", "vuls:tie.order"}
    assert by_name["vuls:score.order"].passed is True
    assert by_name["vuls:score.order"].clauses == ["sort.by_score"]
    assert by_name["vuls:tie.order"].passed is False
    assert by_name["vuls:tie.order"].clauses == ["sort.equal_score_order"]
    assert by_name["vuls:tie.order"].counterexample is not None


def test_parse_vuls_output_ignores_parent_line():
    out = "--- PASS: TestDataForgeVulsOrdering (0.00s)\n"
    assert parse_vuls_probe_output(out) == []


def test_clause_mapping():
    assert clauses_for_probe("score.order") == ["sort.by_score"]
    assert clauses_for_probe("tie.order") == ["sort.equal_score_order"]


def test_contract_declares_tie_and_score_clauses():
    ids = {c.id for c in CONTRACT}
    assert {"sort.by_score", "sort.equal_score_order"} <= ids
    audit = audit_contract(CONTRACT, REQUIRED_TESTS)
    # both ordering clauses are pinned by the retained official test
    assert "sort.by_score" not in audit.uncovered_clauses
    assert "sort.equal_score_order" not in audit.uncovered_clauses
