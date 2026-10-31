"""Tests for the flipt oracle plumbing (V3.2): generator + output parsing + oracle."""

from __future__ import annotations

from pathlib import Path

from dataforge_v3.semantic.executors import clauses_for_probe, parse_go_probe_output
from dataforge_v3.semantic.model import ProbeResult
from dataforge_v3.semantic.tasks.flipt import FliptOracle, generate_go_probes


def test_generated_probe_includes_core_clauses():
    src = generate_go_probes()
    assert "package auth" in src
    assert "TestDataForgeSemanticProbes" in src
    assert "WithServerSkipsAuthentication" in src
    # probes for the uncovered clauses must exist
    assert "cookie.multiple/second_value" in src
    assert "bearer.exact/double_space_rejected" in src
    assert "bypass.membership/non_matching_server_does_not_bypass" in src


def test_parse_go_probe_output_maps_subtests():
    out = (
        "=== RUN   TestDataForgeSemanticProbes\n"
        "=== RUN   TestDataForgeSemanticProbes/bearer.exact/valid\n"
        "--- PASS: TestDataForgeSemanticProbes/bearer.exact/valid (0.00s)\n"
        "--- FAIL: TestDataForgeSemanticProbes/cookie.multiple/second_value (0.00s)\n"
        "--- PASS: TestDataForgeSemanticProbes/bypass.membership/non_matching_server_does_not_bypass (0.00s)\n"
        "FAIL\n"
    )
    results = parse_go_probe_output(out)
    assert len(results) == 3
    by_name = {r.name: r for r in results}
    assert by_name["flipt:bearer.exact/valid"].passed is True
    assert by_name["flipt:cookie.multiple/second_value"].passed is False
    assert by_name["flipt:cookie.multiple/second_value"].clauses == ["cookie.multiple"]
    assert by_name["flipt:bearer.exact/valid"].clauses == ["bearer.exact"]


def test_clause_mapping():
    assert clauses_for_probe("header.malformed.no_fallback/x") == ["header.malformed.no_fallback"]
    assert clauses_for_probe("unknown/thing") == []


def test_flipt_oracle_with_fake_executor(tmp_path):
    captured = {}

    def fake_executor(payload):
        captured.update(payload)
        return ProbeResult(name="flipt:fake", kind="differential", passed=True)

    cand = tmp_path / "middleware.go"
    cand.write_text("package auth\n\n// candidate marker\nfunc UnaryInterceptor() {}\n", encoding="utf-8")

    oracle = FliptOracle(executor=fake_executor)
    results = oracle.run([], candidates=[("cand", cand)])
    assert len(results) == 1 and results[0].passed
    assert "package auth" in captured["probe_source"]
    assert "UnaryInterceptor" in captured["middleware_source"]
