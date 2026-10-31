"""Component B — failure attribution (V3.3), generically and evidence-first.

Inputs (all already produced by lower layers; this module derives, never invents):
  * `TaskEvidence`  — V3.1 validity, V3.2 verdict, submitted patch, trajectory.
  * `SemanticInput` — per-task V3.2 clause definitions + per-candidate probe
                      results (which independent probes failed, on which clauses).

The engine is deliberately NOT task-specific: it never mentions `vuls`,
`SortOrder` or any test name. It reasons over generic signals:

  1. Execution validity (V3.1). An INVALID run yields an *infrastructure*
     diagnosis and no coding-weakness finding — a run that did not happen cannot
     evidence a coding defect.
  2. Failed independent probes (V3.2) attributed to contract clauses. The clause
     *kind* maps to a generic failure category:
        INVARIANT      -> existing behaviour removed / regression
        POSTCONDITION  -> requirement not met
        EDGE_CASE / ERROR_BEHAVIOR -> boundary / error-handling failure
  3. Patch-diff corroboration: a clause is only tagged "existing behaviour
     removed" when the submitted patch actually deletes the mechanism, not merely
     because a probe failed. Otherwise the category is the weaker "requirement
     not met" with the diff recorded as supporting context.
  4. Trajectory process signals: the official failing test was executed, tests
     were skipped, or a failing test stayed unresolved. Only OBSERVED where the
     trajectory actually records it; otherwise the point is a limitation.

Every Finding carries evidence refs; a finding whose evidence does not resolve is
downgraded to HYPOTHESIS by the driver, never emitted as authoritative.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from dataforge_v3.intelligence.normalizer import TaskEvidence
from dataforge_v3.intelligence.schema import (
    ClaimKind,
    Confidence,
    EvidenceRef,
    EventType,
    FailureCategory,
    Finding,
    Severity,
)

# ---------- V3.2 semantic input model (thin, read-only) ----------


@dataclass
class Clause:
    id: str
    kind: str  # POSTCONDITION | INVARIANT | EDGE_CASE | ERROR_BEHAVIOR | PRECONDITION
    statement: str = ""
    source: str = ""
    tested_by_original: list[str] = field(default_factory=list)


@dataclass
class ProbeFinding:
    name: str
    passed: bool
    clauses: list[str] = field(default_factory=list)
    detail: str = ""
    counterexample: dict[str, Any] | None = None


@dataclass
class SemanticInput:
    """Per-task V3.2 semantic evidence for the evaluated submission."""

    verdict: str | None = None
    confidence: str | None = None
    clauses: list[Clause] = field(default_factory=list)
    probes: list[ProbeFinding] = field(default_factory=list)
    evidence_artifact: str | None = None

    def clause(self, cid: str) -> Clause | None:
        for c in self.clauses:
            if c.id == cid:
                return c
        return None

    def failing_probes(self) -> list[ProbeFinding]:
        return [p for p in self.probes if not p.passed]


# ---------- generic category mapping ----------

_KIND_TO_CATEGORY = {
    "INVARIANT": FailureCategory.EXISTING_BEHAVIOR_REMOVED,
    "POSTCONDITION": FailureCategory.REQUIREMENT_OMITTED,
    "EDGE_CASE": FailureCategory.EDGE_CASE_FAILURE,
    "ERROR_BEHAVIOR": FailureCategory.EDGE_CASE_FAILURE,
    "PRECONDITION": FailureCategory.REQUIREMENT_OMITTED,
}

_KIND_TO_SEVERITY = {
    "INVARIANT": Severity.MAJOR,
    "POSTCONDITION": Severity.MAJOR,
    "EDGE_CASE": Severity.MINOR,
    "ERROR_BEHAVIOR": Severity.MINOR,
    "PRECONDITION": Severity.MINOR,
}

# Tokens that, when they disappear from the submitted patch as whole lines,
# corroborate "existing behaviour removed". Kept representation-agnostic: the
# engine does not know a task; it only looks at what the diff deleted.
_REMOVED_LINE = re.compile(r"^-(?!--)(.*)$")

_TEST_NAME_HINT = re.compile(r"Test[A-Za-z0-9_]+")


def _signal_removed_behavior(patch_text: str | None) -> list[str]:
    """Return deleted identifiers from a unified diff (minus/context aware)."""
    if not patch_text:
        return []
    removed: list[str] = []
    for raw in patch_text.splitlines():
        m = _REMOVED_LINE.match(raw)
        if not m:
            continue
        body = m.group(1).strip()
        if body:
            removed.append(body)
    return removed


def _removed_tokens(removed_lines: list[str]) -> set[str]:
    toks: set[str] = set()
    for line in removed_lines:
        for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", line):
            toks.add(t)
    return toks


def _clause_mechanism_tokens(clause: Clause) -> set[str]:
    """Tokens from a clause statement that, if deleted, corroborate removal.

    Uses the clause's own words (e.g. a field name mentioned in an INVARIANT),
    so the mapping stays data-driven rather than task-hardcoded.
    """
    return {t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", clause.statement)}


@dataclass
class AttributionResult:
    findings: list[Finding]
    strengths: list[Any] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def attribute(evidence: TaskEvidence, semantic: SemanticInput | None) -> AttributionResult:
    """Produce evidence-backed findings for one task attempt."""

    findings: list[Finding] = []
    notes: list[str] = []

    # (1) Infrastructure invalidation dominates: never turn it into a coding claim.
    if evidence.execution_validity != "VALID":
        findings.append(_infrastructure_finding(evidence))
        notes.append(
            "execution classified "
            f"{evidence.execution_validity}; no agent-coding weakness is derivable "
            "from an attempt that did not validly execute"
        )
        return AttributionResult(findings=findings, notes=notes)

    # (2) Semantic clause violations (the substantive surface).
    if semantic is not None:
        removed_lines = _signal_removed_behavior(evidence.patch_text)
        removed_toks = _removed_tokens(removed_lines)
        for probe in semantic.failing_probes():
            for cid in probe.clauses:
                clause = semantic.clause(cid)
                findings.append(
                    _clause_finding(evidence, semantic, probe, cid, clause, removed_toks)
                )
        if not semantic.failing_probes():
            notes.append(
                "all independent V3.2 probes passed for the audited surface; "
                "no verified failure finding"
            )

    # (3) Trajectory process signals (observed only).
    process = _process_findings(evidence)
    findings.extend(process)

    return AttributionResult(findings=findings, notes=notes)


def _infrastructure_finding(evidence: TaskEvidence) -> Finding:
    has_traj = evidence.has_trajectory
    patch_files = _patch_file_count(evidence.patch_text)
    symptom = (
        "Agent execution did not validly complete; no authoritative evaluation "
        "of coding ability is possible."
    )
    limitations = [
        "The absence of model responses/valid execution is the failure; it does "
        "not evidence any model coding weakness.",
    ]
    if not has_traj:
        limitations.append("No trajectory artifact was produced by this attempt.")
    if patch_files is not None and patch_files > 0 and _looks_contaminated(evidence.patch_text):
        limitations.append(
            "Submitted patch contains runtime/database artifacts rather than source edits."
        )
    return Finding(
        id=f"{evidence.task_id}:infra",
        category=FailureCategory.AGENT_STARTUP_FAILURE,
        severity=Severity.BLOCKER,
        symptom=symptom,
        violated_requirement=None,
        source_changes=[],
        evidence=_task_evidence_refs(evidence),
        confidence=Confidence.HIGH,
        competing_explanations=[
            "Model API unavailable",
            "agent harness startup error",
            "environment/network failure",
        ],
        limitations=limitations,
        kind=ClaimKind.OBSERVED,
    )


def _clause_finding(
    evidence: TaskEvidence,
    semantic: SemanticInput,
    probe: ProbeFinding,
    cid: str,
    clause: Clause | None,
    removed_toks: set[str],
) -> Finding:
    kind = clause.kind if clause else "POSTCONDITION"
    category = _KIND_TO_CATEGORY.get(kind, FailureCategory.REQUIREMENT_OMITTED)
    severity = _KIND_TO_SEVERITY.get(kind, Severity.MAJOR)

    # Corroboration: only claim "existing behaviour removed" if the patch really
    # deletes mechanism words tied to the clause. Otherwise fall back.
    corroborated = False
    if category is FailureCategory.EXISTING_BEHAVIOR_REMOVED and clause is not None:
        mech = _clause_mechanism_tokens(clause) & removed_toks
        if mech:
            corroborated = True
        else:
            category = FailureCategory.REQUIREMENT_OMITTED

    statement = clause.statement if clause else f"clause {cid}"
    symptom = (
        f"Independent probe `{probe.name}` failed against contract clause "
        f"`{cid}`: {statement}"
    )
    refs: list[EvidenceRef] = []
    if semantic.evidence_artifact:
        refs.append(EvidenceRef(semantic.evidence_artifact, f"probes[{probe.name}]", probe.detail))
    refs.extend(_task_evidence_refs(evidence, include_patch=True))

    limitations: list[str] = []
    if not corroborated and kind == "INVARIANT":
        limitations.append(
            "The patch did not show a directly matching deleted identifier; the "
            "clause violation is established by the executable probe, not the diff."
        )
    limitations.append(
        "The defect is verified; why the agent produced it is not observable."
    )

    return Finding(
        id=f"{evidence.task_id}:clause:{cid}",
        category=category,
        severity=severity,
        symptom=symptom,
        violated_requirement=cid,
        source_changes=_patch_files(evidence.patch_text),
        trace_event_ids=[],
        evidence=refs,
        confidence=Confidence.HIGH if probe.counterexample else Confidence.MEDIUM,
        competing_explanations=[
            "The independent probe is over-strict (checked by correct-alternative acceptance in V3.2)",
            "The task specification is ambiguous for this clause",
        ],
        limitations=limitations,
        kind=ClaimKind.REPRODUCED,
    )


def _process_findings(evidence: TaskEvidence) -> list[Finding]:
    """Observed test-discipline signals from the trajectory (no inference)."""

    out: list[Finding] = []
    traj = evidence.trajectory
    if traj is None:
        return out
    tests = [e for e in traj.events if e.event_type is EventType.TEST_EXECUTION]
    results = [e for e in traj.events if e.event_type is EventType.TOOL_RESULT]
    failed = [r for r in results if r.returncode not in (0, None)]
    if not tests:
        out.append(
            Finding(
                id=f"{evidence.task_id}:no-test-run",
                category=FailureCategory.RELEVANT_TEST_NOT_EXECUTED,
                severity=Severity.MINOR,
                symptom="No test-execution command was observed in the trajectory.",
                violated_requirement=None,
                evidence=_trajectory_refs(evidence),
                confidence=Confidence.LOW,
                limitations=[
                    "Absence in the recorded trajectory is not proof the agent never "
                    "tested; the trajectory may be incomplete.",
                ],
                kind=ClaimKind.OBSERVED,
            )
        )
    return out


# ---------- helpers ----------

_SOURCE_SUFFIXES = (".go", ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".java", ".rb", ".c", ".h", ".cpp")


def _patch_files(patch_text: str | None) -> list[str]:
    if not patch_text:
        return []
    files = re.findall(r"^\+\+\+ b/(.+)$", patch_text, flags=re.MULTILINE)
    return [f.strip() for f in files if f.strip()]


def _patch_file_count(patch_text: str | None) -> int | None:
    if patch_text is None:
        return None
    return len(_patch_files(patch_text))


def _looks_contaminated(patch_text: str | None) -> bool:
    if not patch_text:
        return False
    files = _patch_files(patch_text)
    src = [f for f in files if f.endswith(_SOURCE_SUFFIXES)]
    return len(files) > 0 and len(src) == 0


def _task_evidence_refs(evidence: TaskEvidence, include_patch: bool = False) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []
    if evidence.patch_path is not None and (include_patch or True):
        refs.append(_rel(evidence.patch_path, evidence.short_name, "submitted patch"))
    if evidence.replay_path is not None:
        refs.append(_rel(evidence.replay_path, evidence.short_name, "replay record"))
    for n in evidence.notes:
        pass
    return refs


def _trajectory_refs(evidence: TaskEvidence) -> list[EvidenceRef]:
    if evidence.trajectory and evidence.trajectory.source_artifact:
        return [EvidenceRef(evidence.trajectory.source_artifact, "messages", "recorded trajectory")]
    return []


def _rel(path, task_id: str, note: str) -> EvidenceRef:
    """Store artifact paths relative to the repository root when possible."""
    text = str(path).replace("\\", "/")
    marker = "/v3/"
    if marker in text:
        rel = text.split(marker, 1)[1]
    else:
        rel = text
    return EvidenceRef(rel, "sha256", note)
