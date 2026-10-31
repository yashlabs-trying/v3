"""V3.3 driver — assemble per-task diagnoses and the fleet profile.

Pipeline per task:
  TaskEvidence (V3.1 + V3.2 labels + trajectory + patch)
    -> load_semantic_input (V3.2 contracts/probes)
    -> attribute (Component B findings)
    -> strengths from passed probes
    -> analyze_capabilities (Component C)
    -> recommend_for_findings (Component D)
    -> EvidenceResolver audit: any finding/claim whose evidence is unresolved is
       downgraded to HYPOTHESIS (never emitted as authoritative).
    -> Diagnosis (Component E reports)

The driver never mutates evidence and never changes a V2/V3.1/V3.2 verdict.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from dataforge_v3.intelligence.attribution import attribute
from dataforge_v3.intelligence.capabilities import aggregate_observations, analyze_capabilities
from dataforge_v3.intelligence.evidence import EvidenceResolver
from dataforge_v3.intelligence.normalizer import (
    load_cohort,
    load_semantic_input,
    load_task_evidence,
)
from dataforge_v3.intelligence.recommendations import recommend_for_findings
from dataforge_v3.intelligence.schema import (
    ClaimKind,
    Confidence,
    DiagnosticClaim,
    Diagnosis,
    Finding,
)


@dataclass
class FleetDiagnosis:
    diagnoses: list[Diagnosis] = field(default_factory=list)
    observations: list = field(default_factory=list)
    runtime_seconds: float | None = None

    def to_dict(self) -> dict:
        return {
            "n_tasks": len(self.diagnoses),
            "runtime_seconds": self.runtime_seconds,
            "tasks": [d.to_dict() for d in self.diagnoses],
            "capability_profile": aggregate_observations(self.observations),
        }


def _strengths_from_semantic(evidence, semantic) -> list[DiagnosticClaim]:
    """Demonstrated strengths: clauses the independent probes PASSED."""
    out: list[DiagnosticClaim] = []
    if semantic is None:
        return out
    passed = [p for p in semantic.probes if p.passed]
    passed_clauses = sorted({cid for p in passed for cid in p.clauses})
    if passed_clauses:
        out.append(
            DiagnosticClaim(
                text=(
                    f"Satisfied {len(passed_clauses)} independently-probed contract "
                    f"clause(s): {', '.join(passed_clauses)}."
                ),
                kind=ClaimKind.REPRODUCED,
                confidence=Confidence.HIGH,
                evidence=[],
            )
        )
    return out


def _downgrade_unresolved(findings: list[Finding], resolver: EvidenceResolver) -> None:
    for f in findings:
        if not f.evidence:
            if f.kind is not ClaimKind.OBSERVED:
                f.kind = ClaimKind.HYPOTHESIS
                f.limitations.append("no evidence reference; downgraded to hypothesis")
            continue
        ok, _auth = resolver.all_resolve(f.evidence)
        if not ok:
            f.kind = ClaimKind.HYPOTHESIS
            f.limitations.append("evidence did not resolve; downgraded to hypothesis")


def diagnose_task(root: Path, evidence, resolver: EvidenceResolver) -> Diagnosis:
    diagnosis, _obs = diagnose_task_with_observations(root, evidence, resolver)
    return diagnosis


def diagnose_task_with_observations(root: Path, evidence, resolver: EvidenceResolver):
    semantic = load_semantic_input(root, evidence.short_name)
    attribution = attribute(evidence, semantic)
    findings = attribution.findings
    _downgrade_unresolved(findings, resolver)

    strengths = _strengths_from_semantic(evidence, semantic)
    observations = analyze_capabilities(evidence, findings, semantic, strengths)
    recommendations = recommend_for_findings(findings)

    summary = _summarize(evidence, findings, strengths, semantic)
    uncertainty = _uncertainty(evidence, findings, semantic)

    return Diagnosis(
        task_id=evidence.short_name,
        attempt=evidence.attempt,
        execution_validity=evidence.execution_validity,
        semantic_verdict=evidence.semantic_verdict,
        original_score=evidence.original_score,
        summary=summary,
        findings=findings,
        strengths=strengths,
        weaknesses=[],
        capabilities=aggregate_observations(observations),
        recommendations=[r.to_dict() for r in recommendations],
        uncertainty=uncertainty,
        runtime_seconds=None,
        cost_usd=None,
    ), observations


def _summarize(evidence, findings, strengths, semantic) -> str:
    if evidence.execution_validity != "VALID":
        return (
            "Execution was classified "
            f"{evidence.execution_validity} by V3.1. This is an infrastructure "
            "outcome: no authoritative statement about coding ability is possible, "
            "and none is made."
        )
    if findings and any(f.kind is not ClaimKind.HYPOTHESIS for f in findings):
        cats = sorted({f.category.value for f in findings if f.kind is not ClaimKind.HYPOTHESIS})
        return (
            f"Verified {len([f for f in findings if f.kind is not ClaimKind.HYPOTHESIS])} "
            f"failure finding(s) ({', '.join(cats)}) supported by independent probe "
            "evidence and the submitted patch. Demonstrated strengths are listed "
            "separately; they do not offset the failure."
        )
    if semantic is not None and not semantic.failing_probes():
        return (
            "No verified failure finding: every independent probe on the audited "
            "surface passed. This states what was demonstrated on the audited "
            "surface only; it is not proof of whole-application correctness."
        )
    return "No authoritative diagnostic finding was derivable from the available evidence."


def _uncertainty(evidence, findings, semantic) -> list[str]:
    out: list[str] = []
    if evidence.execution_validity != "VALID":
        out.append(
            "Cannot attribute any coding outcome: the attempt did not validly execute."
        )
    if evidence.trajectory is None:
        out.append("No trajectory artifact; observable process actions are unavailable.")
    elif evidence.trajectory.truncated:
        out.append("Trajectory was truncated at the event cap; later actions are unobserved.")
    if semantic is None:
        out.append("No independent V3.2 semantic oracle for this task; correctness unverified.")
    for f in findings:
        if f.kind is ClaimKind.HYPOTHESIS:
            out.append(f"Finding {f.id} downgraded to hypothesis (evidence unresolved).")
    out.append("The defect (if any) may be verified; the model's internal reason is not observable.")
    return out


def run_cohort(root: Path) -> FleetDiagnosis:
    start = time.perf_counter()
    resolver = EvidenceResolver(root)
    diagnoses: list[Diagnosis] = []
    observations: list = []
    for evidence in load_cohort(root):
        t0 = time.perf_counter()
        d, obs = diagnose_task_with_observations(root, evidence, resolver)
        d.runtime_seconds = time.perf_counter() - t0
        diagnoses.append(d)
        observations.extend(obs)
    fleet = FleetDiagnosis(
        diagnoses=diagnoses,
        observations=observations,
        runtime_seconds=time.perf_counter() - start,
    )
    return fleet
