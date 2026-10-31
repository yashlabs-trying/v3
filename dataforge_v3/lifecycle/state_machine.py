"""Explicit lifecycle states with evidence-gated transitions."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class LifecycleState(str, enum.Enum):
    SETUP_PENDING = "SETUP_PENDING"
    SETUP_COMPLETE = "SETUP_COMPLETE"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_EXECUTING = "AGENT_EXECUTING"
    AGENT_FINISHED = "AGENT_FINISHED"
    PATCH_CAPTURED = "PATCH_CAPTURED"
    PATCH_VALIDATED = "PATCH_VALIDATED"
    PATCH_APPLIED = "PATCH_APPLIED"
    VERIFICATION_EXECUTED = "VERIFICATION_EXECUTED"
    EVIDENCE_VALIDATED = "EVIDENCE_VALIDATED"
    FINALIZED = "FINALIZED"


_ORDER = [
    LifecycleState.SETUP_PENDING,
    LifecycleState.SETUP_COMPLETE,
    LifecycleState.AGENT_STARTED,
    LifecycleState.AGENT_EXECUTING,
    LifecycleState.AGENT_FINISHED,
    LifecycleState.PATCH_CAPTURED,
    LifecycleState.PATCH_VALIDATED,
    LifecycleState.PATCH_APPLIED,
    LifecycleState.VERIFICATION_EXECUTED,
    LifecycleState.EVIDENCE_VALIDATED,
    LifecycleState.FINALIZED,
]

REQUIRED_EVIDENCE: dict[LifecycleState, tuple[str, ...]] = {
    LifecycleState.SETUP_PENDING: (),
    LifecycleState.SETUP_COMPLETE: ("environment", "agent_config"),
    LifecycleState.AGENT_STARTED: ("agent_process_started",),
    LifecycleState.AGENT_EXECUTING: ("agent_process_started", "agent_execution_started_at"),
    LifecycleState.AGENT_FINISHED: ("agent_execution_finished_at",),
    LifecycleState.PATCH_CAPTURED: ("patch_sha256",),
    LifecycleState.PATCH_VALIDATED: ("patch_sha256", "patch_validation"),
    LifecycleState.PATCH_APPLIED: ("apply_rc", "post_apply_state"),
    LifecycleState.VERIFICATION_EXECUTED: ("verifier_artifacts",),
    LifecycleState.EVIDENCE_VALIDATED: ("required_tests", "observed_tests"),
    LifecycleState.FINALIZED: ("classification",),
}


class LifecycleError(RuntimeError):
    pass


@dataclass
class LifecycleTracker:
    """Tracks monotonic lifecycle progress and refuses evidence-free transitions."""

    transitions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def current(self) -> LifecycleState:
        if not self.transitions:
            return LifecycleState.SETUP_PENDING
        return LifecycleState(self.transitions[-1]["state"])

    def advance(self, state: LifecycleState, evidence: dict[str, Any]) -> None:
        if not isinstance(state, LifecycleState):
            state = LifecycleState(state)
        missing = [k for k in REQUIRED_EVIDENCE[state] if evidence.get(k) in (None, "", [], {})]
        if missing:
            raise LifecycleError(f"{state.value} requires evidence: {missing}")
        idx = _ORDER.index(state)
        cur = _ORDER.index(self.current)
        if idx < cur:
            raise LifecycleError(f"cannot move backwards from {self.current.value} to {state.value}")
        if idx == cur and self.transitions and self.transitions[-1]["state"] == state.value:
            raise LifecycleError(f"{state.value} already recorded")
        self.transitions.append(
            {
                "state": state.value,
                "at": datetime.now(timezone.utc).isoformat(),
                "evidence_keys": sorted(evidence.keys()),
            }
        )

    def can_finalize(self) -> bool:
        return self.current in (
            LifecycleState.EVIDENCE_VALIDATED,
            LifecycleState.VERIFICATION_EXECUTED,
            LifecycleState.PATCH_APPLIED,
        )

    def to_list(self) -> list[dict[str, Any]]:
        return list(self.transitions)


def describe_blockers(evidence: dict[str, Any], target: LifecycleState) -> list[str]:
    return [k for k in REQUIRED_EVIDENCE[target] if evidence.get(k) in (None, "", [], {})]
