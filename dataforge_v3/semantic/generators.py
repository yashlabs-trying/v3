"""B. Semantic Test Generator (V3.2).

Generates deterministic semantic probes from a declared contract:

  * property    - input/output invariants that must hold for all inputs
  * boundary    - edge values (empty, absent, just-over, just-under)
  * stateful    - sequences of calls where order matters
  * differential- a reference implementation vs the candidate on the same input

Determinism is enforced by deriving all choices from a fixed seed, so a finding
is reproducible by re-running the same task/seed. The generators carry no
knowledge of the candidate submission; they only read the contract.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable

from dataforge_v3.semantic.oracle import ProbeCase


@dataclass
class GeneratorSpec:
    """Declarative recipe a task provides so probes can be generated generically."""

    task: str
    seed: int
    property_inputs: Callable[[random.Random], list[dict[str, Any]]]
    boundary_inputs: Callable[[], list[dict[str, Any]]]
    stateful_sequences: Callable[[random.Random], list[list[dict[str, Any]]]]
    clauses: dict[str, str]


def generate_probes(spec: GeneratorSpec) -> list[ProbeCase]:
    """Expand a spec into a deterministic, ordered list of probe cases."""
    rng = random.Random(spec.seed)
    cases: list[ProbeCase] = []

    for i, payload in enumerate(spec.property_inputs(rng)):
        cases.append(
            ProbeCase(
                name=f"property[{i}]",
                kind="property",
                clauses=list(spec.clauses.keys()),
                payload=payload,
            )
        )

    for i, payload in enumerate(spec.boundary_inputs()):
        cases.append(
            ProbeCase(
                name=f"boundary[{i}]",
                kind="boundary",
                clauses=list(spec.clauses.keys()),
                payload=payload,
            )
        )

    for i, sequence in enumerate(spec.stateful_sequences(rng)):
        cases.append(
            ProbeCase(
                name=f"stateful[{i}]",
                kind="stateful",
                clauses=list(spec.clauses.keys()),
                payload={"sequence": sequence},
            )
        )

    return cases
