"""Core result model: execution, verification integrity, and final classification."""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field, asdict
from typing import Any


class ExecutionStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    STARTUP_ERROR = "STARTUP_ERROR"
    MODEL_API_ERROR = "MODEL_API_ERROR"
    INFRASTRUCTURE_TIMEOUT = "INFRASTRUCTURE_TIMEOUT"
    INTERRUPTED = "INTERRUPTED"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    UNKNOWN = "UNKNOWN"


class VerificationStatus(str, enum.Enum):
    VALID = "VALID"
    PATCH_MISSING = "PATCH_MISSING"
    PATCH_EMPTY = "PATCH_EMPTY"
    PATCH_INVALID = "PATCH_INVALID"
    PATCH_APPLICATION_ERROR = "PATCH_APPLICATION_ERROR"
    TEST_EXECUTION_ERROR = "TEST_EXECUTION_ERROR"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_CONTRADICTORY = "EVIDENCE_CONTRADICTORY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNVERIFIED_ORIGINAL = "UNVERIFIED_ORIGINAL"
    UNKNOWN = "UNKNOWN"


class FinalClassification(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INVALID = "INVALID"


class PatchVerdict(str, enum.Enum):
    ABSENT = "ABSENT"
    EMPTY = "EMPTY"
    VALID = "VALID"
    CONTAMINATED_ONLY = "CONTAMINATED_ONLY"
    INVALID = "INVALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass
class ExecutionRecord:
    status: ExecutionStatus
    agent_process_started: bool | None = None
    model_responses: int | None = None
    exception_type: str | None = None
    cause: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class VerificationRecord:
    status: VerificationStatus
    reward: float | None = None
    required_tests: int | None = None
    passed_required: int | None = None
    missing_required: list[str] = field(default_factory=list)
    contradictory_tests: list[str] = field(default_factory=list)
    test_file_touched: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class PatchRecord:
    verdict: PatchVerdict
    sha256: str | None = None
    size_bytes: int | None = None
    files_total: int = 0
    files_accepted: int = 0
    files_excluded: list[dict[str, Any]] = field(default_factory=list)
    entries: list[dict[str, Any]] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


@dataclass
class DataForgeResult:
    task: str
    task_id: str
    original_reward: float | None
    execution: ExecutionRecord
    patch: PatchRecord
    verification: VerificationRecord
    classification: FinalClassification
    lifecycle: list[dict[str, Any]] = field(default_factory=list)
    replay: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "task_id": self.task_id,
            "original_reward": self.original_reward,
            "execution": self.execution.to_dict(),
            "patch": self.patch.to_dict(),
            "verification": self.verification.to_dict(),
            "classification": self.classification.value,
            "lifecycle": self.lifecycle,
            "replay": self.replay,
            "provenance": self.provenance,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
