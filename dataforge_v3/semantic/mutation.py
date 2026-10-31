"""C. Mutation & Alternative-Solution Validator (V3.2).

Two responsibilities:

1. **Mutants** — deliberately defective implementations (incomplete fix,
   boundary error, regression, wrong state transition, hardcoded shortcut).
   A sound semantic verifier must reject every mutant.

2. **Alternatives** — independently written, genuinely different but correct
   implementations. A sound verifier must accept every alternative. This is the
   false-FAIL guard: it checks the *supplemental* verifier does not overfit to
   one implementation shape.

The validator itself is a small driver: each task supplies a `Verifier` callback
that returns whether a candidate passed the supplemental semantic suite. The
catalogue entries are declarative so results are reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from dataforge_v3.semantic.model import ProbeOutcome, ProbeResult


@dataclass
class Candidate:
    """A concrete implementation to evaluate."""

    name: str
    category: str  # "correct_alternative" | "mutant"
    defect: str | None
    source: str
    expectation: str  # "accept" | "reject"


@dataclass
class ValidationOutcome:
    candidate: Candidate
    actual: str  # "accept" | "reject"
    probe_results: list[ProbeResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.actual == self.candidate.expectation


Verifier = Callable[[Candidate], tuple[str, list[ProbeResult]]]


def validate_catalogue(candidates: list[Candidate], verifier: Verifier) -> list[ValidationOutcome]:
    outcomes: list[ValidationOutcome] = []
    for candidate in candidates:
        actual, results = verifier(candidate)
        outcomes.append(ValidationOutcome(candidate=candidate, actual=actual, probe_results=results))
    return outcomes


def summarize(outcomes: list[ValidationOutcome]) -> dict[str, object]:
    mutants = [o for o in outcomes if o.candidate.category == "mutant"]
    alternatives = [o for o in outcomes if o.candidate.category == "correct_alternative"]
    return {
        "mutants_total": len(mutants),
        "mutants_rejected": sum(1 for o in mutants if o.actual == "reject"),
        "mutants_missed": [o.candidate.name for o in mutants if o.actual != "reject"],
        "alternatives_total": len(alternatives),
        "alternatives_accepted": sum(1 for o in alternatives if o.actual == "accept"),
        "alternatives_rejected": [o.candidate.name for o in alternatives if o.actual != "accept"],
        "false_alarms": [o.candidate.name for o in alternatives if o.actual != "accept"],
    }
