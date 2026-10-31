"""Component C — strengths & weaknesses as capability observations (V3.3).

Design rule (the whole point of this component): the engine reports *counts of
verified observations tied to one task*, never a calibrated ability score. It
maps a finding or a demonstrated behaviour to a `CapabilityDimension`, and emits
a `CapabilityObservation` with `n_events` = number of independent evidence items.

Mapping is derived from the finding's category and the failed clause's kind —
generic, not task-specific. A passing task yields a STRENGTH observation for
every clause its independent probes *passed* (demonstrated, not assumed absent).
"""

from __future__ import annotations

from dataforge_v3.intelligence.attribution import SemanticInput
from dataforge_v3.intelligence.normalizer import TaskEvidence
from dataforge_v3.intelligence.schema import (
    CapabilityDimension as D,
    CapabilityObservation,
    ClaimKind,
    Confidence,
    EventType,
    FailureCategory,
    Finding,
    ObservationPolarity as P,
)

# Category -> the capability a failure evidences (weakness side).
_CATEGORY_TO_DIMENSION = {
    FailureCategory.REQUIREMENT_OMITTED: D.REQUIREMENTS_PRESERVATION,
    FailureCategory.EXISTING_BEHAVIOR_REMOVED: D.REGRESSION_AVOIDANCE,
    FailureCategory.REGRESSION: D.REGRESSION_AVOIDANCE,
    FailureCategory.INTERFACE_COMPATIBILITY_VIOLATION: D.API_COMPATIBILITY,
    FailureCategory.UNSUPPORTED_ASSUMPTION: D.CODEBASE_INVESTIGATION,
    FailureCategory.INCORRECT_ALGORITHM: D.CORRECT_IMPLEMENTATION,
    FailureCategory.EDGE_CASE_FAILURE: D.CORRECT_IMPLEMENTATION,
    FailureCategory.STATE_TRANSITION_ERROR: D.STATE_AND_CONCURRENCY,
    FailureCategory.CONCURRENCY_ORDERING_ERROR: D.STATE_AND_CONCURRENCY,
    FailureCategory.INCOMPLETE_IMPLEMENTATION: D.CORRECT_IMPLEMENTATION,
    FailureCategory.RELEVANT_TEST_NOT_EXECUTED: D.TESTING_DISCIPLINE,
    FailureCategory.FAILING_TEST_UNRESOLVED: D.DEBUGGING,
    FailureCategory.INSUFFICIENT_VALIDATION: D.TESTING_DISCIPLINE,
    FailureCategory.TEST_RESULT_MISREAD: D.DEBUGGING,
    FailureCategory.UNRESOLVED_TOOL_ERROR: D.ERROR_RECOVERY,
    FailureCategory.BUILD_OR_DEPENDENCY_SETUP_FAILED: D.ERROR_RECOVERY,
    FailureCategory.REPEATED_INEFFECTIVE_CHANGES: D.DEBUGGING,
}

# Infrastructure categories never become a capability weakness.
_INFRA_CATEGORIES = {
    FailureCategory.AGENT_STARTUP_FAILURE,
    FailureCategory.INVALID_PATCH_ARTIFACT,
    FailureCategory.REPLAY_FAILURE,
    FailureCategory.INVALID_VERIFIER_EVIDENCE,
    FailureCategory.BUDGET_EXHAUSTED,
}


def _dimension_for_finding(f: Finding) -> D | None:
    if f.category in _INFRA_CATEGORIES:
        return None
    return _CATEGORY_TO_DIMENSION.get(f.category)


def analyze_capabilities(
    evidence: TaskEvidence,
    findings: list[Finding],
    semantic: SemanticInput | None,
    strengths: list,
) -> list[CapabilityObservation]:
    obs: list[CapabilityObservation] = []

    # Weakness observations, one per non-infrastructure finding.
    for f in findings:
        dim = _dimension_for_finding(f)
        if dim is None:
            continue
        obs.append(
            CapabilityObservation(
                dimension=dim,
                polarity=P.WEAKNESS,
                statement=f"Observed on {evidence.task_id}: {f.symptom}",
                task_id=evidence.task_id,
                clause_ids=[f.violated_requirement] if f.violated_requirement else [],
                evidence=list(f.evidence),
                n_events=len(f.evidence),
                confidence=f.confidence,
                kind=f.kind,
            )
        )

    # Strength observations from passed independent probes: demonstrated capability.
    if semantic is not None:
        passed = [p for p in semantic.probes if p.passed]
        passed_clauses = {cid for p in passed for cid in p.clauses}
        if passed_clauses:
            obs.append(
                CapabilityObservation(
                    dimension=D.CORRECT_IMPLEMENTATION,
                    polarity=P.STRENGTH,
                    statement=(
                        f"On {evidence.task_id}, the submission satisfied "
                        f"{len(passed_clauses)} independently-probed contract clause(s) "
                        "that were checked (behaviour demonstrated, not assumed)."
                    ),
                    task_id=evidence.task_id,
                    clause_ids=sorted(passed_clauses),
                    evidence=[],
                    n_events=len(passed),
                    confidence=Confidence.MEDIUM,
                    kind=ClaimKind.REPRODUCED,
                )
            )

    # Testing-discipline strength: observed tests executed with a clean final result.
    if _executed_tests_cleanly(evidence):
        obs.append(
            CapabilityObservation(
                dimension=D.TESTING_DISCIPLINE,
                polarity=P.STRENGTH,
                statement=(
                    f"On {evidence.task_id}, the trajectory shows the agent ran the "
                    "project's tests (observed commands), i.e. testing was attempted."
                ),
                task_id=evidence.task_id,
                evidence=[],
                n_events=_count_test_events(evidence),
                confidence=Confidence.LOW,
                kind=ClaimKind.OBSERVED,
            )
        )

    return obs


def _count_test_events(evidence: TaskEvidence) -> int:
    t = evidence.trajectory
    if t is None:
        return 0
    return len([e for e in t.events if e.event_type is EventType.TEST_EXECUTION])


def _executed_tests_cleanly(evidence: TaskEvidence) -> bool:
    return _count_test_events(evidence) > 0


def aggregate_observations(
    observations: list[CapabilityObservation],
) -> list[dict]:
    """Group observations by dimension; report counts, NOT a score.

    Explicitly returns `n_tasks` and `sample_note` so a single-task observation
    can never be read as a general ability claim.
    """
    by_dim: dict[str, dict] = {}
    for o in observations:
        key = o.dimension.value
        entry = by_dim.setdefault(
            key,
            {
                "dimension": key,
                "strength_tasks": [],
                "weakness_tasks": [],
                "observations": 0,
            },
        )
        entry["observations"] += 1
        bucket = "strength_tasks" if o.polarity is P.STRENGTH else "weakness_tasks"
        if o.task_id not in entry[bucket]:
            entry[bucket].append(o.task_id)

    out = []
    for key, entry in sorted(by_dim.items()):
        n_tasks = len(set(entry["strength_tasks"]) | set(entry["weakness_tasks"]))
        out.append(
            {
                "dimension": key,
                "observations": entry["observations"],
                "n_tasks": n_tasks,
                "strength_tasks": sorted(entry["strength_tasks"]),
                "weakness_tasks": sorted(entry["weakness_tasks"]),
                "sample_note": (
                    "single-task observation; not a general ability claim"
                    if n_tasks <= 1
                    else f"observed across {n_tasks} tasks"
                ),
            }
        )
    return out
