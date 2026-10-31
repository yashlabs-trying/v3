"""Oracle tests for the openlibrary task (V3.2 modules B and C, task oracle)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dataforge_v3.semantic.generators import GeneratorSpec, generate_probes
from dataforge_v3.semantic.tasks.openlibrary import (
    CONTRACT,
    OpenLibraryOracle,
    REQUIRED_TESTS,
    boundary_inputs,
    property_inputs,
    reference_parse_log,
    stateful_sequences,
)

REFERENCE = '''
def find_keys(d):
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "key" and isinstance(v, str):
                yield v
            if isinstance(v, (dict, list)):
                yield from find_keys(v)
    elif isinstance(d, list):
        for item in d:
            yield from find_keys(item)

def parse_log(records, load_ia_scans):
    out = []
    for rec in records:
        if rec.get("action") not in ("save", "save_many"):
            continue
        cs = rec["data"].get("changeset", {})
        docs = cs.get("docs", [])
        old_docs = cs.get("old_docs", [])
        for i, doc in enumerate(docs):
            out.append(doc["key"])
            before = old_docs[i] if i < len(old_docs) else None
            if before is not None:
                out.extend(sorted(set(find_keys(before)) - set(find_keys(doc))))
    return out
'''

MUTANT_INCOMPLETE = REFERENCE.replace(
    "            if before is not None:\n                out.extend(sorted(set(find_keys(before)) - set(find_keys(doc))))\n",
    "",
)
MUTANT_TYPES = REFERENCE.replace('if k == "key" and isinstance(v, str):', 'if k == "key":')
MUTANT_OVERYIELD = REFERENCE.replace(
    '            out.append(doc["key"])',
    '            out.append(doc["key"]); out.extend(sorted(set(find_keys(doc))))',
)


def _spec():
    return GeneratorSpec(
        task="openlibrary",
        seed=1234,
        property_inputs=property_inputs,
        boundary_inputs=boundary_inputs,
        stateful_sequences=stateful_sequences,
        clauses={c.id: c.statement for c in CONTRACT},
    )


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / f"{name}.py"
    p.write_text(src, encoding="utf-8")
    return p


def test_reference_matches_oracle(tmp_path):
    cases = generate_probes(_spec())
    oracle = OpenLibraryOracle()
    res = oracle.run(cases, candidates=[("ref", _write(tmp_path, "ref", REFERENCE))])
    assert all(r.passed for r in res), [r for r in res if not r.passed]


@pytest.mark.parametrize(
    "name,src,min_failures",
    [
        ("incomplete", MUTANT_INCOMPLETE, 1),
        ("types", MUTANT_TYPES, 1),
        ("overyield", MUTANT_OVERYIELD, 1),
    ],
)
def test_mutants_are_detected(tmp_path, name, src, min_failures):
    cases = generate_probes(_spec())
    oracle = OpenLibraryOracle()
    res = oracle.run(cases, candidates=[(name, _write(tmp_path, name, src))])
    failed = [r for r in res if not r.passed]
    assert len(failed) >= min_failures
    assert all(r.counterexample is not None for r in failed)


def test_reference_helper_behavior():
    rec = {
        "action": "save",
        "data": {
            "changeset": {
                "docs": [{"key": "/b", "w": [{"key": "/w2"}]}],
                "old_docs": [{"key": "/b", "w": [{"key": "/w1"}]}],
            }
        },
    }
    assert reference_parse_log([rec]) == ["/b", "/w1"]


def test_removed_set_order_is_not_constrained(tmp_path):
    """The contract defines the removal as a set difference; emission order of
    the removed keys must not cause a false rejection."""
    unordered = REFERENCE.replace(
        'out.extend(sorted(set(find_keys(before)) - set(find_keys(doc))))',
        'removed = list(set(find_keys(before)) - set(find_keys(doc))); out.extend(removed)',
    )
    assert unordered != REFERENCE
    cases = generate_probes(_spec())
    oracle = OpenLibraryOracle()
    res = oracle.run(cases, candidates=[("unordered", _write(tmp_path, "unordered", unordered))])
    assert all(r.passed for r in res), [r for r in res if not r.passed]


def test_required_tests_are_declared():
    assert len(REQUIRED_TESTS) == 3
