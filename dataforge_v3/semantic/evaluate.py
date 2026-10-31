"""Evaluation driver: contract audit -> probes -> disagreement -> assessment (V3.2).

This is the single entry point that produces a `SemanticAssessment`. It is
task-agnostic: a task supplies its contract, generator spec and oracle, and the
driver assembles the independent verdict. It never mutates the V2 reward.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dataforge_v3.semantic.contract import audit_contract
from dataforge_v3.semantic.disagreement import DisagreementInput, analyze
from dataforge_v3.semantic.generators import GeneratorSpec, generate_probes
from dataforge_v3.semantic.model import (
    ContractClause,
    ProbeResult,
    SemanticAssessment,
)
from dataforge_v3.semantic.oracle import ReferenceOracle, to_evidence


@dataclass
class EvaluationRequest:
    task: str
    task_id: str
    submission: str
    v2_reward: float | None
    v3_1_classification: str | None
    v3_1_invalid: bool
    clauses: list[ContractClause]
    required_tests: set[str]
    spec: GeneratorSpec
    oracle: ReferenceOracle
    candidates: list[tuple[str, Any]]
    mutants_missed: list[str] | None = None
    alternatives_rejected: list[str] | None = None


def evaluate(req: EvaluationRequest) -> SemanticAssessment:
    contract = audit_contract(req.clauses, req.required_tests)
    cases = generate_probes(req.spec)
    probes: list[ProbeResult] = req.oracle.run(cases, candidates=req.candidates)

    evidence = to_evidence(probes)
    unmapped_failures = [p.name for p in probes if not p.passed and not p.clauses]
    disagreement = analyze(
        DisagreementInput(
            v2_accepted=(None if req.v2_reward is None else req.v2_reward >= 0.5),
            v3_1_invalid=req.v3_1_invalid,
            contract=contract,
            evidence=evidence,
            mutants_missed=req.mutants_missed or [],
            alternatives_rejected=req.alternatives_rejected or [],
            oracle_ran=len(probes) > 0,
            unmapped_failures=unmapped_failures,
        )
    )

    counterexamples = [r.counterexample for r in probes if r.counterexample]

    return SemanticAssessment(
        task=req.task,
        task_id=req.task_id,
        submission=req.submission,
        v2_reward=req.v2_reward,
        v3_1_classification=req.v3_1_classification,
        verdict=disagreement.verdict,
        confidence=disagreement.confidence,
        clauses=req.clauses,
        evidence=evidence,
        probes=probes,
        counterexamples=counterexamples,
        unresolved=[],
        notes=disagreement.reasons,
    )
