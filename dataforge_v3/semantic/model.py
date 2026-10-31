"""Core semantic-verification data model (V3.2).

Deliberately separate from `dataforge_v3.model`: the reliability layer answers
"was the evaluation valid?", the semantic layer answers "was the decision
correct?". Keeping the two vote spaces disjoint prevents a semantic finding from
silently re-scoring the benchmark.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field, asdict
from typing import Any


class SemanticVerdict(str, enum.Enum):
    """The independent semantic judgement. Never replaces the V2 reward."""

    CONFIRMED_CORRECT = "CONFIRMED_CORRECT"
    CONFIRMED_INCORRECT = "CONFIRMED_INCORRECT"
    SUSPECTED_FALSE_PASS = "SUSPECTED_FALSE_PASS"
    SUSPECTED_FALSE_FAIL = "SUSPECTED_FALSE_FAIL"
    SPECIFICATION_AMBIGUOUS = "SPECIFICATION_AMBIGUOUS"
    INCONCLUSIVE = "INCONCLUSIVE"
    INVALID_EXECUTION = "INVALID_EXECUTION"


class ClauseKind(str, enum.Enum):
    PRECONDITION = "PRECONDITION"
    POSTCONDITION = "POSTCONDITION"
    INVARIANT = "INVARIANT"
    ERROR_BEHAVIOR = "ERROR_BEHAVIOR"
    EDGE_CASE = "EDGE_CASE"


class ProbeOutcome(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class ContractClause:
    """One independently-stated requirement extracted from the task text.

    `source` records where the requirement comes from so a reviewer can audit the
    extraction. `tested_by_original` lists the official test names (if any) that
    already pin the clause; clauses with an empty list are the false-PASS surface.
    """

    id: str
    kind: ClauseKind
    statement: str
    source: str
    tested_by_original: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass
class ClauseEvidence:
    """Evidence for or against a clause from an executable probe."""

    clause_id: str
    probe: str
    outcome: ProbeOutcome
    counterexample: dict[str, Any] | None = None
    observed: Any = None
    expected: Any = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d


@dataclass
class ProbeResult:
    """A single executable semantic probe (property, boundary, mutation, differential)."""

    name: str
    kind: str
    passed: bool
    clauses: list[str] = field(default_factory=list)
    detail: str = ""
    counterexample: dict[str, Any] | None = None
    observed: Any = None
    expected: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticAssessment:
    """Independent semantic judgement for one submission."""

    task: str
    task_id: str
    submission: str
    v2_reward: float | None
    v3_1_classification: str | None
    verdict: SemanticVerdict
    confidence: str
    clauses: list[ContractClause] = field(default_factory=list)
    evidence: list[ClauseEvidence] = field(default_factory=list)
    probes: list[ProbeResult] = field(default_factory=list)
    counterexamples: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "task_id": self.task_id,
            "submission": self.submission,
            "v2_reward": self.v2_reward,
            "v3_1_classification": self.v3_1_classification,
            "verdict": self.verdict.value,
            "confidence": self.confidence,
            "clauses": [c.to_dict() for c in self.clauses],
            "evidence": [e.to_dict() for e in self.evidence],
            "probes": [p.to_dict() for p in self.probes],
            "counterexamples": self.counterexamples,
            "unresolved": self.unresolved,
            "notes": self.notes,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


@dataclass
class SemanticReport:
    """Fleet-level semantic comparison across submissions."""

    assessments: list[SemanticAssessment] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for a in self.assessments:
            out[a.verdict.value] = out.get(a.verdict.value, 0) + 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.assessments),
            "verdicts": self.counts(),
            "assessments": [a.to_dict() for a in self.assessments],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
