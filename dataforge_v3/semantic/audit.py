"""Task-level semantic audit drivers (V3.2).

Assembles `EvaluationRequest`s for the two selected Phase 2 tasks and runs the
generic evaluation pipeline. Candidate sources are supplied by the caller so the
audit is reproducible from committed evidence rather than hardcoded paths.
"""

from __future__ import annotations

from pathlib import Path

from dataforge_v3.semantic.evaluate import EvaluationRequest, evaluate
from dataforge_v3.semantic.executors import run_flipt_probes
from dataforge_v3.semantic.generators import GeneratorSpec, generate_probes
from dataforge_v3.semantic.model import SemanticAssessment
from dataforge_v3.semantic.oracle import ProbeCase, ProbeResult
from dataforge_v3.semantic.tasks.flipt import Executor
from dataforge_v3.semantic.tasks import flipt as flipt_task
from dataforge_v3.semantic.tasks import openlibrary as ol_task


def _openlibrary_spec() -> GeneratorSpec:
    return GeneratorSpec(
        task="openlibrary",
        seed=20261,
        property_inputs=ol_task.property_inputs,
        boundary_inputs=ol_task.boundary_inputs,
        stateful_sequences=ol_task.stateful_sequences,
        clauses={c.id: c.statement for c in ol_task.CONTRACT},
    )


def audit_openlibrary(
    candidate_path: Path,
    submission: str,
    v2_reward: float | None,
    v3_1_classification: str | None = None,
    v3_1_invalid: bool = False,
    mutants_missed: list[str] | None = None,
    alternatives_rejected: list[str] | None = None,
) -> SemanticAssessment:
    oracle = ol_task.OpenLibraryOracle()
    req = EvaluationRequest(
        task="openlibrary",
        task_id="instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866",
        submission=submission,
        v2_reward=v2_reward,
        v3_1_classification=v3_1_classification,
        v3_1_invalid=v3_1_invalid,
        clauses=ol_task.CONTRACT,
        required_tests=ol_task.REQUIRED_TESTS,
        spec=_openlibrary_spec(),
        oracle=oracle,
        candidates=[(submission, candidate_path)],
        mutants_missed=mutants_missed,
        alternatives_rejected=alternatives_rejected,
    )
    return evaluate(req)


def audit_flipt(
    candidate_middleware_source: str,
    submission: str,
    v2_reward: float | None,
    v3_1_classification: str | None = None,
    v3_1_invalid: bool = False,
    executor: Executor | None = None,
    mutants_missed: list[str] | None = None,
    alternatives_rejected: list[str] | None = None,
) -> SemanticAssessment:
    if executor is None:

        def executor(payload: dict) -> ProbeResult:  # type: ignore[misc]
            results = run_flipt_probes(
                payload["middleware_source"],
                payload["probe_source"],
            )
            failed = [r for r in results if not r.passed and "harness" not in r.name]
            return ProbeResult(
                name=f"flipt:{submission}",
                kind="differential",
                passed=not failed,
                clauses=[c for r in failed for c in r.clauses],
                detail="" if not failed else f"{len(failed)} probe(s) failed",
                counterexample=None
                if not failed
                else {"failing": [r.name for r in failed]},
                observed=[r.name for r in failed],
            )

    oracle = flipt_task.FliptOracle(executor=executor)

    req = EvaluationRequest(
        task="flipt",
        task_id="instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f",
        submission=submission,
        v2_reward=v2_reward,
        v3_1_classification=v3_1_classification,
        v3_1_invalid=v3_1_invalid,
        clauses=flipt_task.CONTRACT,
        required_tests=flipt_task.REQUIRED_TESTS,
        spec=GeneratorSpec(
            task="flipt",
            seed=1,
            property_inputs=lambda rng: [],
            boundary_inputs=lambda: [],
            stateful_sequences=lambda rng: [],
            clauses={c.id: c.statement for c in flipt_task.CONTRACT},
        ),
        oracle=oracle,
        candidates=[(submission, _InlineSource(candidate_middleware_source))],
        mutants_missed=mutants_missed,
        alternatives_rejected=alternatives_rejected,
    )
    return evaluate(req)


class _InlineSource:
    """Adapts an in-memory source string to the `Path`-like oracle input."""

    def __init__(self, text: str) -> None:
        self._text = text

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._text
