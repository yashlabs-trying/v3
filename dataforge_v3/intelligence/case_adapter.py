"""V3.3 six-case validation adapter — bind an arbitrary controlled case to the
existing diagnostic engine, without changing the engine.

This is the *smallest* interface needed to run the V3.3 pipeline on cases that are
not part of the frozen `COHORT`. It is deliberately generic:

  * A case is described by a JSON manifest (`CaseManifest`) that records *where*
    the evidence lives (patch, trajectory, replay, semantic evidence) and the
    lower-layer labels (V3.1 validity, V3.2 verdict, original score).
  * Nothing here knows a task name. There is no `if task == ...` branch and no
    expected answer embedded. The engine still derives findings from content.
  * The manifest carries only evidence and labels that a lower layer already
    produced. Ground-truth answer keys live *outside* this adapter and are never
    passed in.

The adapter reuses the same code paths the frozen CLI uses:
`load_trajectory_file` -> `TaskEvidence` -> `diagnose_task_with_observations`
-> `EvidenceResolver` -> `render_diagnosis_*`. It never mutates V3.1/V3.2 output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from dataforge_v3.intelligence.attribution import Clause, ProbeFinding, SemanticInput
from dataforge_v3.intelligence.normalizer import TaskEvidence
from dataforge_v3.intelligence.schema import ValidityError


@dataclass
class CaseManifest:
    """A controlled case: evidence locations + lower-layer labels (no answers)."""

    case_id: str
    short_name: str
    attempt: str
    execution_validity: str
    semantic_verdict: str | None
    original_score: float | None
    patch: str | None = None
    trajectory: str | None = None
    replay: str | None = None
    semantic: dict | None = None
    semantic_specified: bool = False
    evidence_roots: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def load_case_manifest(path: Path) -> CaseManifest:
    data = _read_json(path)
    if data is None:
        raise ValueError(f"case manifest not found or malformed: {path}")
    return CaseManifest(
        case_id=data["case_id"],
        short_name=data["short_name"],
        attempt=data.get("attempt", "original"),
        execution_validity=data["execution_validity"],
        semantic_verdict=data.get("semantic_verdict"),
        original_score=data.get("original_score"),
        patch=data.get("patch"),
        trajectory=data.get("trajectory"),
        replay=data.get("replay"),
        semantic=data.get("semantic"),
        semantic_specified=("semantic" in data),
        evidence_roots=list(data.get("evidence_roots", [])),
        notes=list(data.get("notes", [])),
    )


def _build_semantic(spec: dict | None) -> SemanticInput | None:
    """Build a read-only SemanticInput from clause+probe data.

    The shape mirrors `findings/vuls_semantic_evidence.json` and
    `findings/semantic_audit.json`: clauses carry a kind and statement; probes
    carry pass/fail, the clause ids they apply to, a detail and optional
    counterexample. These are V3.2-produced facts, not diagnostics.
    """
    if not spec:
        return None
    clauses = [
        Clause(
            id=c["id"],
            kind=c.get("kind", "POSTCONDITION"),
            statement=c.get("statement", ""),
            source=c.get("source", ""),
            tested_by_original=list(c.get("tested_by_original", [])),
        )
        for c in spec.get("clauses", [])
    ]
    probes = [
        ProbeFinding(
            name=p.get("name", "?"),
            passed=bool(p.get("passed")),
            clauses=list(p.get("clauses", [])),
            detail=p.get("detail", ""),
            counterexample=p.get("counterexample"),
        )
        for p in spec.get("probes", [])
    ]
    return SemanticInput(
        verdict=spec.get("verdict"),
        confidence=spec.get("confidence"),
        clauses=clauses,
        probes=probes,
        evidence_artifact=spec.get("evidence_artifact"),
    )


def load_case_evidence(root: Path, manifest: CaseManifest) -> TaskEvidence:
    """Assemble a `TaskEvidence` for a controlled case from its manifest."""
    patch_path = None
    patch_text = None
    if manifest.patch:
        cand = root / manifest.patch
        if cand.exists():
            patch_path = cand
            patch_text = cand.read_text(encoding="utf-8", errors="replace")

    replay_path = None
    replay = None
    if manifest.replay:
        cand = root / manifest.replay
        if cand.exists():
            replay_path = cand
            replay = _read_json(cand)

    trajectory = None
    notes = list(manifest.notes)
    if manifest.trajectory:
        traj_path = root / manifest.trajectory
        if traj_path.exists():
            from dataforge_v3.intelligence.trajectory import load_trajectory_file

            try:
                trajectory = load_trajectory_file(
                    traj_path, task_id=manifest.short_name, attempt=manifest.attempt
                )
            except ValidityError as exc:
                notes.append(f"trajectory load failed: {exc}")
        else:
            notes.append("declared trajectory artifact is absent")

    return TaskEvidence(
        task_id=manifest.short_name,
        short_name=manifest.short_name,
        attempt=manifest.attempt,
        execution_validity=manifest.execution_validity,
        semantic_verdict=manifest.semantic_verdict,
        original_score=manifest.original_score,
        trajectory=trajectory,
        patch_path=patch_path,
        patch_text=patch_text,
        replay_path=replay_path,
        replay=replay,
        notes=notes,
    )


def _case_allowed_roots(root: Path, manifest_path: Path, manifest: CaseManifest) -> list[str]:
    """Approved evidence roots for a controlled case.

    Always the frozen roots (`jobs`, `findings`). The case may additionally
    declare its own roots through the manifest `evidence_roots` field; each is
    required to sit inside the repository root (the resolver drops any that
    escape). This keeps trust explicit: a case cannot silently reach outside the
    roots it declares.
    """
    roots = ["jobs", "findings"]
    for extra in manifest.evidence_roots:
        extra = str(extra).replace("\\", "/").strip("/")
        if extra and extra not in roots:
            roots.append(extra)
    return roots


def diagnose_manifest(root: Path, manifest_path: Path):
    """Run the existing diagnostic engine on one controlled case.

    Returns (diagnosis, semantic_input, observations).

    This performs the *same* assembly the frozen cohort driver performs
    (`attribution.attribute` -> unresolved-evidence downgrade -> strengths ->
    `capabilities.analyze_capabilities` -> `recommendations.recommend_for_findings`
    -> `Diagnosis`). The only difference is the source of `SemanticInput`: here it
    comes from the case manifest rather than the frozen `load_semantic_input` map.
    No attribution/reporting logic is reimplemented; the engine's own functions
    are called directly.
    """
    from dataforge_v3.intelligence.attribution import attribute
    from dataforge_v3.intelligence.capabilities import aggregate_observations, analyze_capabilities
    from dataforge_v3.intelligence.driver import (
        _downgrade_unresolved,
        _strengths_from_semantic,
        _summarize,
        _uncertainty,
    )
    from dataforge_v3.intelligence.evidence import EvidenceResolver
    from dataforge_v3.intelligence.normalizer import load_semantic_input
    from dataforge_v3.intelligence.recommendations import recommend_for_findings
    from dataforge_v3.intelligence.schema import Diagnosis

    manifest = load_case_manifest(manifest_path)
    evidence = load_case_evidence(root, manifest)
    resolver = EvidenceResolver(root, allowed_roots=_case_allowed_roots(root, manifest_path, manifest))

    semantic = _build_semantic(manifest.semantic)
    if semantic is None and not manifest.semantic_specified:
        # Fall back to the frozen semantic loader only when the manifest does not
        # mention semantic evidence at all (e.g. reuse of an already-registered
        # task). An explicit `"semantic": null` means "no semantic oracle" and is
        # respected, so a controlled case cannot silently inherit another task's
        # oracle through the short_name.
        semantic = load_semantic_input(root, manifest.short_name)

    attribution = attribute(evidence, semantic)
    findings = attribution.findings
    _downgrade_unresolved(findings, resolver)

    strengths = _strengths_from_semantic(evidence, semantic)
    observations = analyze_capabilities(evidence, findings, semantic, strengths)
    recommendations = recommend_for_findings(findings)

    diagnosis = Diagnosis(
        task_id=evidence.short_name,
        attempt=evidence.attempt,
        execution_validity=evidence.execution_validity,
        semantic_verdict=evidence.semantic_verdict,
        original_score=evidence.original_score,
        summary=_summarize(evidence, findings, strengths, semantic),
        findings=findings,
        strengths=strengths,
        weaknesses=[],
        capabilities=aggregate_observations(observations),
        recommendations=[r.to_dict() for r in recommendations],
        uncertainty=_uncertainty(evidence, findings, semantic),
        runtime_seconds=None,
        cost_usd=None,
    )
    return diagnosis, semantic, observations
