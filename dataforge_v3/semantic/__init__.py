"""Semantic Verification & Fairness Engine (DataForge V3.2, Phase 2).

This package sits *above* the V3.1 reliability layer. It never changes the
official SWE-bench Pro V2 pass/fail score and never weakens V3.1's lifecycle,
patch-integrity or execution checks. Instead it produces a separate, independent
`SemanticAssessment` for each submission.
"""

from __future__ import annotations

from dataforge_v3.semantic.model import (
    SemanticAssessment,
    SemanticVerdict,
    ContractClause,
    ClauseEvidence,
    ProbeResult,
    ProbeOutcome,
    SemanticReport,
)

__all__ = [
    "SemanticAssessment",
    "SemanticVerdict",
    "ContractClause",
    "ClauseEvidence",
    "ProbeResult",
    "ProbeOutcome",
    "SemanticReport",
]
