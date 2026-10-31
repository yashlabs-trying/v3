"""V3.3 integration tests against the frozen seven-task cohort.

These assert the engine's behavior on the *real* evidence tree: vuls must be
attributed to its clause, NodeBB must stay infrastructure-only, and no passing
task may receive an invented weakness finding.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dataforge_v3.intelligence.driver import run_cohort
from dataforge_v3.intelligence.evidence import EvidenceResolver
from dataforge_v3.intelligence.normalizer import COHORT, load_semantic_input, load_task_evidence
from dataforge_v3.intelligence.reporting import render_diagnosis_json, render_diagnosis_markdown
from dataforge_v3.intelligence.schema import ClaimKind, FailureCategory

ROOT = Path(__file__).resolve().parents[2]


def _cohort_available() -> bool:
    return (ROOT / "jobs" / "f3-vuls-a1").exists() and (ROOT / "findings" / "vuls_semantic_evidence.json").exists()


pytestmark = pytest.mark.skipif(not _cohort_available(), reason="frozen cohort evidence not present")


@pytest.fixture(scope="module")
def fleet():
    return run_cohort(ROOT)


def test_fleet_covers_all_tasks(fleet):
    assert len(fleet.diagnoses) == len(COHORT)


def test_vuls_attributed_generically(fleet):
    vuls = next(d for d in fleet.diagnoses if d.task_id == "vuls")
    assert vuls.execution_validity == "VALID"
    clause_findings = [f for f in vuls.findings if f.violated_requirement]
    assert clause_findings, "vuls must yield a clause-attributed finding"
    f = clause_findings[0]
    assert f.category is FailureCategory.EXISTING_BEHAVIOR_REMOVED
    # every finding cites resolvable evidence
    resolver = EvidenceResolver(ROOT)
    for finding in vuls.findings:
        ok, _ = resolver.all_resolve(finding.evidence)
        assert ok, f"unresolved evidence on {finding.id}"


def test_vuls_diagnosis_is_not_hardcoded():
    """The engine must derive vuls from generic evidence, not a task special-case.

    Checked on compiled code values (string literals + identifiers used), not on
    docstrings: docstrings may *mention* the task when explaining that it is not
    special-cased.
    """
    import ast
    import inspect
    from dataforge_v3.intelligence import attribution, driver, capabilities, recommendations

    forbidden = {"SortOrder", "TestSortByConfident", "CpeVersionMatch"}
    for mod in (attribution, driver, capabilities, recommendations):
        source = inspect.getsource(mod)
        tree = ast.parse(source)
        # Collect every string literal value EXCEPT module/function/class docstrings.
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc:
                    docstrings.add(doc)
        literals = {
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value not in docstrings
        }
        for token in forbidden:
            assert not any(token in lit for lit in literals), (
                f"{mod.__name__} hardcodes {token} in a code string literal"
            )


def test_nodebb_original_is_infrastructure_only(fleet):
    nodebb = next(d for d in fleet.diagnoses if d.task_id == "NodeBB")
    assert nodebb.execution_validity == "INVALID"
    assert all(f.category is FailureCategory.AGENT_STARTUP_FAILURE for f in nodebb.findings)
    # no coding-capability weakness may be inferred
    for row in nodebb.capabilities:
        assert not row["weakness_tasks"]
    md = render_diagnosis_markdown(nodebb, EvidenceResolver(ROOT))
    lowered = md.lower()
    for forbidden in ("weak javascript", "cannot fix", "failed to understand", "weak redis"):
        assert forbidden not in lowered


def test_passing_tasks_get_no_invented_weakness(fleet):
    for d in fleet.diagnoses:
        if d.execution_validity != "VALID":
            continue
        if d.semantic_verdict == "CONFIRMED_CORRECT":
            assert d.findings == [], f"{d.task_id} has invented findings: {d.findings}"


def test_vuls_recommendation_is_measurable(fleet):
    vuls = next(d for d in fleet.diagnoses if d.task_id == "vuls")
    assert vuls.recommendations
    r = vuls.recommendations[0]
    assert r["hypothesis"] and r["intervention"] and r["control"] and r["metric"]
    assert r["executed"] is False
    assert "authorized" in r["execution_note"]


def test_reports_are_stable(fleet):
    resolver = EvidenceResolver(ROOT)
    vuls = next(d for d in fleet.diagnoses if d.task_id == "vuls")
    a = render_diagnosis_json(vuls, resolver)
    b = render_diagnosis_json(vuls, resolver)
    assert a == b


def test_semantic_loader_shapes():
    for name, _job, _att in COHORT:
        si = load_semantic_input(ROOT, name)
        if si is None:
            continue
        assert all(isinstance(c.id, str) for c in si.clauses)


def test_element_web_coverage_limitation_is_declared():
    si = load_semantic_input(ROOT, "element-web")
    # element-web's semantic verdict is CONFIRMED_CORRECT but only on the LruCache
    # surface; the engine records medium confidence and no failure finding.
    assert si is not None
    assert si.failing_probes() == []
