"""V3.3 diagnostic evidence contract: event schema, evidence refs, claim kinds.

This module is deliberately dependency-free data + validation. It defines *what
the evidence can support* before any report generator exists.

Separation of knowledge states (core principle: evidence first):
  * OBSERVED    - directly present in a recorded artifact (a command, a return code)
  * REPRODUCED  - re-executed and confirmed (e.g. an oracle counterexample)
  * SUPPORTED   - a causal hypothesis grounded in observed+reproduced evidence
  * HYPOTHESIS  - a plausible but unverified explanation
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any


class EventType(str, enum.Enum):
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    MODEL_RESPONSE = "model_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    COMMAND = "command"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    PATCH_SNAPSHOT = "patch_snapshot"
    TEST_EXECUTION = "test_execution"
    TEST_RESULT = "test_result"
    ERROR = "error"
    RETRY = "retry"
    INFRASTRUCTURE_ERROR = "infrastructure_error"
    UNKNOWN = "unknown"


class ClaimKind(str, enum.Enum):
    OBSERVED = "observed"
    REPRODUCED = "reproduced"
    SUPPORTED = "supported"
    HYPOTHESIS = "hypothesis"


class Confidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Severity(str, enum.Enum):
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    BLOCKER = "blocker"


class FailureCategory(str, enum.Enum):
    # Specification & requirements
    REQUIREMENT_OMITTED = "requirement_omitted"
    EXISTING_BEHAVIOR_REMOVED = "existing_behavior_removed"
    UNSUPPORTED_ASSUMPTION = "unsupported_assumption"
    INTERFACE_COMPATIBILITY_VIOLATION = "interface_compatibility_violation"
    # Implementation correctness
    INCORRECT_ALGORITHM = "incorrect_algorithm"
    EDGE_CASE_FAILURE = "edge_case_failure"
    STATE_TRANSITION_ERROR = "state_transition_error"
    CONCURRENCY_ORDERING_ERROR = "concurrency_ordering_error"
    INCOMPLETE_IMPLEMENTATION = "incomplete_implementation"
    REGRESSION = "regression"
    # Testing & validation
    RELEVANT_TEST_NOT_EXECUTED = "relevant_test_not_executed"
    FAILING_TEST_UNRESOLVED = "failing_test_unresolved"
    INSUFFICIENT_VALIDATION = "insufficient_validation"
    TEST_RESULT_MISREAD = "test_result_misread"
    # Execution process
    REPEATED_INEFFECTIVE_CHANGES = "repeated_ineffective_changes"
    UNRESOLVED_TOOL_ERROR = "unresolved_tool_error"
    BUILD_OR_DEPENDENCY_SETUP_FAILED = "build_or_dependency_setup_failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    # Infrastructure
    AGENT_STARTUP_FAILURE = "agent_startup_failure"
    INVALID_PATCH_ARTIFACT = "invalid_patch_artifact"
    REPLAY_FAILURE = "replay_failure"
    INVALID_VERIFIER_EVIDENCE = "invalid_verifier_evidence"
    # None
    NONE = "none"


class ValidityError(Exception):
    """Raised when an event or record violates the evidence contract."""


# Bounded input limits protect against adversarial or oversized trajectories.
MAX_EVENTS = 200_000
MAX_FIELD_CHARS = 20_000
MAX_RECORD_BYTES = 64 * 1024 * 1024


@dataclass
class EvidenceRef:
    """A resolvable pointer from a claim to a recorded artifact."""

    artifact: str  # path relative to the repository root
    locator: str  # e.g. "messages[42].extra.actions[0]", "L12", "sha256:..."
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Event:
    event_id: str
    task_id: str
    event_type: EventType
    timestamp: float | None = None
    command: str | None = None
    exit_code: int | None = None
    returncode: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    artifact_ref: str | None = None
    provenance: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Event":
        try:
            et = EventType(d["event_type"])
        except (KeyError, ValueError) as exc:
            raise ValidityError(f"invalid event: {exc}") from exc
        if not d.get("event_id"):
            raise ValidityError("event missing event_id")
        if not d.get("task_id"):
            raise ValidityError("event missing task_id")
        cmd = d.get("command")
        if cmd is not None and len(cmd) > MAX_FIELD_CHARS:
            cmd = cmd[:MAX_FIELD_CHARS]
        return cls(
            event_id=d["event_id"],
            task_id=d["task_id"],
            event_type=et,
            timestamp=d.get("timestamp"),
            command=cmd,
            exit_code=d.get("exit_code"),
            returncode=d.get("returncode"),
            payload=d.get("payload", {}),
            artifact_ref=d.get("artifact_ref"),
            provenance=d.get("provenance", ""),
        )


@dataclass
class DiagnosticClaim:
    """One statement with its knowledge state and evidence."""

    text: str
    kind: ClaimKind
    confidence: Confidence
    evidence: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "kind": self.kind.value,
            "confidence": self.confidence.value,
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class Finding:
    """A single evidence-backed diagnostic finding."""

    id: str
    category: FailureCategory
    severity: Severity
    symptom: str
    violated_requirement: str | None
    source_changes: list[str] = field(default_factory=list)
    trace_event_ids: list[str] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)
    confidence: Confidence = Confidence.MEDIUM
    competing_explanations: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    kind: ClaimKind = ClaimKind.SUPPORTED

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["severity"] = self.severity.value
        d["confidence"] = self.confidence.value
        d["kind"] = self.kind.value
        d["evidence"] = [e.to_dict() for e in self.evidence]
        return d


@dataclass
class TrajectoryRecord:
    """Normalized observable execution for one task/attempt."""

    task_id: str
    attempt: str
    model: str | None
    events: list[Event] = field(default_factory=list)
    exit_status: str | None = None
    api_calls: int | None = None
    cost_usd: float | None = None
    total_tokens: int | None = None
    source_artifact: str | None = None
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "attempt": self.attempt,
            "model": self.model,
            "exit_status": self.exit_status,
            "api_calls": self.api_calls,
            "cost_usd": self.cost_usd,
            "total_tokens": self.total_tokens,
            "source_artifact": self.source_artifact,
            "truncated": self.truncated,
            "warnings": self.warnings,
            "event_count": len(self.events),
            "events": [e.to_dict() for e in self.events],
        }

    def commands(self) -> list[Event]:
        return [e for e in self.events if e.event_type is EventType.COMMAND]

    def tests(self) -> list[Event]:
        return [e for e in self.events if e.event_type is EventType.TEST_EXECUTION]


class CapabilityDimension(str, enum.Enum):
    """Evidence-derived capability taxonomy (Component C).

    A dimension is a *label for a kind of demonstrated behaviour*, not a score.
    The engine only ever emits an observation when a finding/strength maps to it.
    """

    REQUIREMENTS_PRESERVATION = "requirements_preservation"
    CODEBASE_INVESTIGATION = "codebase_investigation"
    CORRECT_IMPLEMENTATION = "correct_implementation"
    TESTING_DISCIPLINE = "testing_discipline"
    REGRESSION_AVOIDANCE = "regression_avoidance"
    DEBUGGING = "debugging"
    TOOL_USAGE = "tool_usage"
    API_COMPATIBILITY = "api_compatibility"
    STATE_AND_CONCURRENCY = "state_and_concurrency"
    ERROR_RECOVERY = "error_recovery"


class ObservationPolarity(str, enum.Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"


@dataclass
class CapabilityObservation:
    """One capability observed on one task, with its evidence count.

    The engine reports *counts of verified observations*, never a calibrated
    ability score. `n_events` records how many independent evidence items fed it,
    so a reader can see the observation is not a universal claim.
    """

    dimension: CapabilityDimension
    polarity: ObservationPolarity
    statement: str
    task_id: str
    clause_ids: list[str] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)
    n_events: int = 0
    confidence: Confidence = Confidence.MEDIUM
    kind: ClaimKind = ClaimKind.OBSERVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "polarity": self.polarity.value,
            "statement": self.statement,
            "task_id": self.task_id,
            "clause_ids": self.clause_ids,
            "evidence": [e.to_dict() for e in self.evidence],
            "n_events": self.n_events,
            "confidence": self.confidence.value,
            "kind": self.kind.value,
        }


@dataclass
class ExperimentRecommendation:
    """Component D — a measurable engineering experiment, never a promise.

    `executed` is False unless a controlled run actually happened; an unexecuted
    recommendation is reported as NOT_EXECUTED, never as an improvement.
    """

    id: str
    finding_id: str
    task_id: str
    evidence: list[EvidenceRef] = field(default_factory=list)
    intervention: str = ""
    hypothesis: str = ""
    control: str = ""
    expected_outcome: str = ""
    metric: str = ""
    cost_estimate: str = ""
    confounders: list[str] = field(default_factory=list)
    executed: bool = False
    execution_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "task_id": self.task_id,
            "evidence": [e.to_dict() for e in self.evidence],
            "intervention": self.intervention,
            "hypothesis": self.hypothesis,
            "control": self.control,
            "expected_outcome": self.expected_outcome,
            "metric": self.metric,
            "cost_estimate": self.cost_estimate,
            "confounders": self.confounders,
            "executed": self.executed,
            "execution_note": self.execution_note,
        }


@dataclass
class Diagnosis:
    """Assembled per-task diagnosis (Components B..E output)."""

    task_id: str
    attempt: str
    execution_validity: str  # from V3.1
    semantic_verdict: str | None  # from V3.2
    original_score: float | None
    summary: str
    findings: list[Finding] = field(default_factory=list)
    strengths: list[DiagnosticClaim] = field(default_factory=list)
    weaknesses: list[DiagnosticClaim] = field(default_factory=list)
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    uncertainty: list[str] = field(default_factory=list)
    runtime_seconds: float | None = None
    cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "attempt": self.attempt,
            "execution_validity": self.execution_validity,
            "semantic_verdict": self.semantic_verdict,
            "original_score": self.original_score,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
            "strengths": [s.to_dict() for s in self.strengths],
            "weaknesses": [w.to_dict() for w in self.weaknesses],
            "capabilities": self.capabilities,
            "recommendations": self.recommendations,
            "uncertainty": self.uncertainty,
            "runtime_seconds": self.runtime_seconds,
            "cost_usd": self.cost_usd,
        }
