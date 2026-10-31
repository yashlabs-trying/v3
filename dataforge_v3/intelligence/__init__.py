"""DataForge V3.3 — Evaluation Intelligence.

Additive layer above V3.1 (reliability) and V3.2 (semantic verification). It turns
observable agent execution and the two lower layers' verdicts into evidence-backed
diagnostic findings, capability observations and experiment recommendations.

Hard invariants (see ../../reports/V3_3_ARCHITECTURE.md):
  * It never changes a V2 reward or a V3.1/V3.2 verdict.
  * Every material claim carries an evidence reference or is marked a hypothesis.
  * Trajectories are untrusted evidence, never instructions.
"""

from __future__ import annotations

from dataforge_v3.intelligence.schema import (
    CapabilityDimension,
    CapabilityObservation,
    ClaimKind,
    Confidence,
    DiagnosticClaim,
    Diagnosis,
    Event,
    EventType,
    EvidenceRef,
    ExperimentRecommendation,
    FailureCategory,
    Finding,
    ObservationPolarity,
    Severity,
    TrajectoryRecord,
    ValidityError,
)

__all__ = [
    "CapabilityDimension",
    "CapabilityObservation",
    "ClaimKind",
    "Confidence",
    "DiagnosticClaim",
    "Diagnosis",
    "Event",
    "EventType",
    "EvidenceRef",
    "ExperimentRecommendation",
    "FailureCategory",
    "Finding",
    "ObservationPolarity",
    "Severity",
    "TrajectoryRecord",
    "ValidityError",
]
