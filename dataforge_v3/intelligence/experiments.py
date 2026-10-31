"""Component D-2 — experiment execution tracking (V3.3).

A recommendation is only ever marked `executed` here, with a recorded outcome.
Without an authorized run, the record states NOT_EXECUTED. This module never
fabricates an improvement.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ExperimentOutcome:
    recommendation_id: str
    task_id: str
    executed: bool
    executed_at: str | None = None
    control_metric: dict | None = None
    treatment_metric: dict | None = None
    delta: dict | None = None
    tokens_added: int | None = None
    time_added_seconds: float | None = None
    note: str = ""
    limitations: list[str] = field(default_factory=list)


def not_executed(recommendation: dict, reason: str) -> ExperimentOutcome:
    return ExperimentOutcome(
        recommendation_id=recommendation["id"],
        task_id=recommendation.get("task_id", ""),
        executed=False,
        note=f"NOT_EXECUTED: {reason}",
        limitations=[
            "No improvement is claimed because no run occurred.",
            "Would require the same frozen task, model and verifier as the control.",
        ],
    )


def write_outcomes(outcomes: list[ExperimentOutcome], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(o) for o in outcomes], indent=2, sort_keys=True),
        encoding="utf-8",
    )
