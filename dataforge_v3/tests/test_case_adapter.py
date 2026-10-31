"""Tests for the six-case validation adapter (V3.3).

These assert the adapter's *generic* contract: it loads a case from a manifest as
data, it never hardcodes a task, it respects an explicit "no semantic oracle"
declaration, and it reuses the engine's own attribution so findings are derived
from content. They run entirely offline on a temp fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

from dataforge_v3.intelligence.case_adapter import (
    diagnose_manifest,
    load_case_evidence,
    load_case_manifest,
)


def _write_case(tmp_path: Path, *, semantic, patch_text="diff --git a/x b/x\n--- a/f.go\n+++ b/f.go\n"):
    case = tmp_path / "case"
    case.mkdir()
    (case / "model.patch").write_text(patch_text, encoding="utf-8")
    manifest = {
        "case_id": "x",
        "short_name": "some-task",
        "attempt": "original",
        "execution_validity": "VALID",
        "semantic_verdict": "GENUINE_AGENT_FAILURE",
        "original_score": 0.0,
        "patch": "case/model.patch",
        "semantic": semantic,
    }
    path = case / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_manifest_loads_as_data(tmp_path):
    path = _write_case(tmp_path, semantic=None)
    m = load_case_manifest(path)
    assert m.short_name == "some-task"
    assert m.semantic_specified is True  # key present (even if null)


def test_explicit_null_semantic_is_not_overridden_by_frozen_loader(tmp_path):
    # "vuls" is a registered frozen task; an explicit null semantic must NOT pull
    # in the vuls oracle through the short_name.
    path = _write_case(tmp_path, semantic=None)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["short_name"] = "vuls"
    path.write_text(json.dumps(data), encoding="utf-8")
    diag, semantic, _obs = diagnose_manifest(tmp_path, path)
    assert semantic is None
    assert diag.task_id == "vuls"


def test_failing_probe_maps_to_clause_finding(tmp_path):
    semantic = {
        "clauses": [{"id": "c.bound", "kind": "POSTCONDITION", "statement": "enforce limit"}],
        "probes": [{"name": "p", "passed": False, "clauses": ["c.bound"]}],
        "evidence_artifact": "case/model.patch",
    }
    path = _write_case(tmp_path, semantic=semantic)
    diag, _semantic, _obs = diagnose_manifest(tmp_path, path)
    clause_findings = [f for f in diag.findings if f.violated_requirement == "c.bound"]
    assert clause_findings
    assert clause_findings[0].category.value == "requirement_omitted"


def test_passing_probes_produce_no_failure_finding(tmp_path):
    semantic = {
        "verdict": "CONFIRMED_CORRECT",
        "clauses": [{"id": "c", "kind": "POSTCONDITION", "statement": "ok"}],
        "probes": [{"name": "p", "passed": True, "clauses": ["c"]}],
    }
    path = _write_case(tmp_path, semantic=semantic)
    diag, _semantic, _obs = diagnose_manifest(tmp_path, path)
    assert diag.findings == []


def test_invalid_validity_never_becomes_coding_finding(tmp_path):
    path = _write_case(tmp_path, semantic=None)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["execution_validity"] = "INVALID"
    path.write_text(json.dumps(data), encoding="utf-8")
    diag, _semantic, _obs = diagnose_manifest(tmp_path, path)
    assert diag.findings
    assert all(f.category.value == "agent_startup_failure" for f in diag.findings)


def test_adapter_source_has_no_task_special_cases():
    import ast
    import inspect

    from dataforge_v3.intelligence import case_adapter

    tree = ast.parse(inspect.getsource(case_adapter))
    literals = {
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }
    for token in ("vuls", "teleport", "element-web", "openlibrary", "NodeBB"):
        assert not any(token == lit for lit in literals), f"adapter hardcodes {token}"


def test_load_case_evidence_reports_missing_trajectory(tmp_path):
    path = _write_case(tmp_path, semantic=None)
    m = load_case_manifest(path)
    m.trajectory = "case/does-not-exist.json"
    ev = load_case_evidence(tmp_path, m)
    assert ev.trajectory is None
    assert any("absent" in n for n in ev.notes)
