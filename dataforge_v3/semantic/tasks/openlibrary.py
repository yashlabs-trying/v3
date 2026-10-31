"""Independent contract + oracle for the openlibrary Solr-reindex task (V3.2).

Contains:
  * CONTRACT         - clauses extracted from the task instruction, with the
                       official tests that pin each (if any).
  * reference_find_keys / reference_parse_log
                     - an independent implementation written from the contract
                       alone, used as the differential oracle. It is deliberately
                       a *different* implementation shape from the gold patch.
  * generators       - deterministic property/boundary/stateful probe payloads.
  * OpenLibraryOracle- executes probes against a candidate module loaded from a
                       file, with heavy imports stubbed so `find_keys`/`parse_log`
                       can be tested in isolation.

Nothing here reads the gold patch; the reference is derived from prose only.
"""

from __future__ import annotations

import importlib.util
import random
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from dataforge_v3.semantic.model import ClauseKind, ContractClause, ProbeResult
from dataforge_v3.semantic.oracle import ProbeCase

TASK = "openlibrary"

# --- Contract (independently reviewable data) -------------------------------

CONTRACT: list[ContractClause] = [
    ContractClause(
        id="find_keys.depth",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "find_keys(d) yields, in traversal order, every string value stored "
            "under a 'key' field at any nesting depth within a dict or list."
        ),
        source="instruction.md Requirements bullet 1",
        tested_by_original=[
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save",
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition",
        ],
    ),
    ContractClause(
        id="find_keys.types",
        kind=ClauseKind.INVARIANT,
        statement="find_keys must not recurse into or emit values for non-dict/list types.",
        source="instruction.md Requirements bullet 1",
        tested_by_original=[],
    ),
    ContractClause(
        id="parse_log.one_key_per_doc",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "For 'save' and 'save_many', parse_log yields exactly one key per doc "
            "in changeset['docs']: that doc's own top-level 'key'."
        ),
        source="instruction.md Requirements bullet 2",
        tested_by_original=[
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save",
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition",
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_new_account",
        ],
    ),
    ContractClause(
        id="parse_log.difference",
        kind=ClauseKind.POSTCONDITION,
        statement=(
            "When old_docs[i] is not None, additionally yield every key in "
            "find_keys(old_docs[i]) not in find_keys(docs[i])."
        ),
        source="instruction.md Requirements bullet 3",
        tested_by_original=[
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save",
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition",
        ],
    ),
    ContractClause(
        id="parse_log.none_old_doc",
        kind=ClauseKind.EDGE_CASE,
        statement=(
            "If old_docs[i] is None, skip the set-difference for that pair and "
            "yield only the doc's top-level key."
        ),
        source="instruction.md Requirements bullet 4",
        tested_by_original=[
            "scripts/tests/test_new_solr_updater.py::TestParseLog::test_new_account",
        ],
    ),
    ContractClause(
        id="parse_log.old_docs_length",
        kind=ClauseKind.EDGE_CASE,
        statement=(
            "documents and old_docs are paired by index; a doc with no matching "
            "old_docs entry must be treated as having no previous version "
            "(top-level key only), and must not error."
        ),
        source="AMBIGUOUS",
        tested_by_original=[],
    ),
]

REQUIRED_TESTS = {
    "scripts/tests/test_new_solr_updater.py::TestParseLog::test_action_save",
    "scripts/tests/test_new_solr_updater.py::TestParseLog::test_move_edition",
    "scripts/tests/test_new_solr_updater.py::TestParseLog::test_new_account",
}

# --- Independent reference implementation (from prose only) -----------------


def reference_find_keys(d: Any) -> Iterator[str]:
    """Reference: depth-first traversal in insertion order, emit str 'key' values."""
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "key" and isinstance(v, str):
                yield v
            if isinstance(v, (dict, list)):
                yield from reference_find_keys(v)
    elif isinstance(d, list):
        for item in d:
            yield from reference_find_keys(item)


def reference_parse_log(records: list[dict], load_ia_scans: bool = False) -> list[str]:
    out: list[str] = []
    for rec in records:
        action = rec.get("action")
        if action not in ("save", "save_many"):
            continue
        changeset = rec["data"].get("changeset", {})
        docs = changeset.get("docs", [])
        old_docs = changeset.get("old_docs", [])
        for i, doc in enumerate(docs):
            out.append(doc["key"])
            before = old_docs[i] if i < len(old_docs) else None
            if before is not None:
                removed = set(reference_find_keys(before)) - set(reference_find_keys(doc))
                out.extend(sorted(removed))
    return out


@dataclass
class RecordSpec:
    """Per-record expectation: doc keys (ordered) and removed keys (a set)."""

    doc_keys: list[str]
    removed: set[str]


def reference_structure(records: list[dict]) -> list[RecordSpec]:
    """Contract-faithful per-record expectation.

    Order is meaningful only for the per-document top-level keys (bullet 2).
    The removed keys (bullet 3) are defined as a *set difference*, so their
    emission order is not part of the contract and must not be constrained.
    """
    specs: list[RecordSpec] = []
    for rec in records:
        if rec.get("action") not in ("save", "save_many"):
            continue
        changeset = rec["data"].get("changeset", {})
        docs = changeset.get("docs", [])
        old_docs = changeset.get("old_docs", [])
        for i, doc in enumerate(docs):
            before = old_docs[i] if i < len(old_docs) else None
            removed: set[str] = set()
            if before is not None:
                removed = set(reference_find_keys(before)) - set(reference_find_keys(doc))
            specs.append(RecordSpec(doc_keys=[doc["key"]], removed=removed))
    return specs


def compare_parse_log(observed: list[str], specs: list[RecordSpec]) -> tuple[bool, str]:
    """Compare candidate output to the contract structure, order-agnostic on sets.

    Returns (ok, reason). The candidate must, per record, emit the doc key first,
    then exactly the removed keys (in any order).
    """
    idx = 0
    for n, spec in enumerate(specs):
        for dk in spec.doc_keys:
            if idx >= len(observed) or observed[idx] != dk:
                got = observed[idx] if idx < len(observed) else "<missing>"
                return False, f"record {n}: expected doc key {dk!r}, got {got!r}"
            idx += 1
        remaining = len(spec.removed)
        chunk = observed[idx : idx + remaining]
        if len(chunk) != remaining or set(chunk) != spec.removed:
            return False, (
                f"record {n}: removed set mismatch; "
                f"expected {sorted(spec.removed)}, got {sorted(chunk)}"
            )
        idx += remaining
    if idx != len(observed):
        return False, f"extra output beyond contract: {observed[idx:]}"
    return True, "matches contract structure"



# --- Module loader with stubbed heavy imports -------------------------------


def load_candidate_module(path: Path) -> types.ModuleType:
    """Import a candidate `new-solr-updater.py` with its heavy deps stubbed.

    The real module imports `web`, `openlibrary.*`, `infogami.*`, `six`, and
    expects `_init_path` to exist. We replace all of these with inert,
    attribute-permissive stubs so that only the pure functions under test are
    exercised. This is sound for `find_keys`/`parse_log`, which use no external
    state.
    """

    class _PermissiveModule(types.ModuleType):
        def __getattr__(self, name: str):
            if name.startswith("__"):
                raise AttributeError(name)
            child = _PermissiveModule(f"{self.__name__}.{name}")
            setattr(self, name, child)
            return child

    stub_names = [
        "_init_path",
        "six",
        "six.moves",
        "six.moves.urllib",
        "web",
        "openlibrary",
        "openlibrary.solr",
        "openlibrary.solr.update_work",
        "openlibrary.config",
        "openlibrary.core",
        "openlibrary.core.utils",
        "infogami",
        "infogami.config",
        "infogami.infobase",
        "infogami.infobase.client",
    ]
    for name in stub_names:
        sys.modules.setdefault(name, _PermissiveModule(name))
    sys.modules["openlibrary.solr"].update_work = lambda *a, **k: None
    sys.modules["openlibrary.config"].load_config = lambda *a, **k: None

    spec = importlib.util.spec_from_file_location(f"candidate_{TASK}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load candidate module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Generators -------------------------------------------------------------


def _rnd_key(rng: random.Random) -> str:
    return f"/works/OL{rng.randint(1, 999999)}W"


def property_inputs(rng: random.Random) -> list[dict[str, Any]]:
    records = []
    for _ in range(6):
        before_works = [_rnd_key(rng) for _ in range(rng.randint(0, 3))]
        after_works = before_works[: rng.randint(0, len(before_works))]
        if rng.random() < 0.5:
            after_works = after_works + [_rnd_key(rng)]
        doc = {
            "key": "/books/OL1M",
            "type": {"key": "/type/edition"},
            "works": [{"key": k} for k in after_works],
            "authors": [{"key": "/authors/OL1A"}],
        }
        old = {
            "key": "/books/OL1M",
            "type": {"key": "/type/edition"},
            "works": [{"key": k} for k in before_works],
            "authors": [{"key": "/authors/OL1A"}],
        }
        records.append(
            {
                "action": rng.choice(["save", "save_many"]),
                "data": {"changeset": {"docs": [doc], "old_docs": [old]}},
            }
        )
    return [{"records": records} for _ in [0]]


def boundary_inputs() -> list[dict[str, Any]]:
    return [
        {"records": []},
        {"records": [{"action": "save", "data": {"changeset": {"docs": [], "old_docs": []}}}]},
        {  # non-string key values must not be emitted
            "records": [
                {
                    "action": "save_many",
                    "data": {
                        "changeset": {
                            "docs": [{"key": "/books/OL2M", "weird": {"key": 12345}}],
                            "old_docs": [None],
                        }
                    },
                }
            ]
        },
        {  # non-string key inside a BEFORE doc, so find_keys is exercised
            "records": [
                {
                    "action": "save_many",
                    "data": {
                        "changeset": {
                            "docs": [{"key": "/books/OL2M", "weird": {"key": 12345}}],
                            "old_docs": [{"key": "/books/OL2M", "removed": {"key": 999}}],
                        }
                    },
                }
            ]
        },
        {  # old_docs shorter than docs -> extra doc treated as no previous version
            "records": [
                {
                    "action": "save_many",
                    "data": {
                        "changeset": {
                            "docs": [{"key": "/books/OL3M"}, {"key": "/books/OL4M"}],
                            "old_docs": [None],
                        }
                    },
                }
            ]
        },
        {  # deeply nested key
            "records": [
                {
                    "action": "save_many",
                    "data": {
                        "changeset": {
                            "docs": [
                                {
                                    "key": "/books/OL5M",
                                    "a": [{"b": {"c": {"key": "/deep/1"}}}],
                                }
                            ],
                            "old_docs": [None],
                        }
                    },
                }
            ]
        },
    ]


def stateful_sequences(rng: random.Random) -> list[list[dict[str, Any]]]:
    seq1 = [
        {"action": "save", "data": {"changeset": {"docs": [{"key": "/a"}], "old_docs": [{"key": "/a", "w": [{"key": "/w1"}]}]}}},
        {"action": "save", "data": {"changeset": {"docs": [{"key": "/a"}], "old_docs": [{"key": "/a", "w": [{"key": "/w2"}]}]}}},
    ]
    return [seq1]


# --- Oracle -----------------------------------------------------------------


@dataclass
class OpenLibraryOracle:
    task: str = TASK

    def run(self, cases: list[ProbeCase], candidates: list[tuple[str, Path]] | None = None) -> list[ProbeResult]:
        """Differential probe: compare candidate output to the reference.

        `candidates` is a list of (name, path) pairs. When empty, this oracle
        records a single SKIPPED result so the caller knows no candidate ran.
        """
        if not candidates:
            return [
                ProbeResult(
                    name="oracle:no-candidate",
                    kind="differential",
                    passed=False,
                    detail="no candidate module supplied",
                )
            ]
        results: list[ProbeResult] = []
        for cand_name, path in candidates:
            try:
                module = load_candidate_module(path)
            except Exception as exc:  # noqa: BLE001 - report load failures as probes
                results.append(
                    ProbeResult(
                        name=f"{cand_name}:load",
                        kind="differential",
                        passed=False,
                        detail=f"failed to load candidate: {exc!r}",
                    )
                )
                continue
            for case in cases:
                results.append(self._run_case(cand_name, module, case))
        return results

    def _run_case(self, cand_name: str, module: types.ModuleType, case: ProbeCase) -> ProbeResult:
        clauses = case.clauses
        try:
            if case.kind == "stateful":
                records = [rec for step in case.payload["sequence"] for rec in [step]]
            else:
                records = case.payload.get("records", [])
            specs = reference_structure(records)
            observed = list(module.parse_log(records, False))
            ok, reason = compare_parse_log(observed, specs)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                name=f"{cand_name}:{case.name}",
                kind=case.kind,
                passed=False,
                clauses=clauses,
                detail=f"candidate raised {exc!r}",
                counterexample={"records": case.payload, "exception": repr(exc)},
            )
        return ProbeResult(
            name=f"{cand_name}:{case.name}",
            kind=case.kind,
            passed=ok,
            clauses=clauses,
            detail=reason,
            observed=observed,
            counterexample=None if ok else {"records": case.payload, "observed": observed, "reason": reason},
        )
