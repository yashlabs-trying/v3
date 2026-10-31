"""Component A (part 2) — evidence adapters that bind a task to its artifacts.

Given a repository root and a frozen task identifier, this locates the observable
evidence (trajectory, submitted patch, V3.1 classification, V3.2 semantic verdict)
and returns a `TaskEvidence` bundle. It performs no diagnosis.

The mapping is data, declared in `COHORT`, not inferred. It records *where* each
artifact lives; the diagnosis engine must still derive findings from content.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from dataforge_v3.intelligence.schema import TrajectoryRecord, ValidityError


@dataclass
class TaskEvidence:
    task_id: str
    short_name: str
    attempt: str
    execution_validity: str  # "VALID" | "INVALID" (V3.1)
    semantic_verdict: str | None  # V3.2 verdict string, or None
    original_score: float | None
    trajectory: TrajectoryRecord | None
    patch_path: Path | None
    patch_text: str | None
    replay_path: Path | None
    replay: dict | None
    notes: list[str] = field(default_factory=list)

    @property
    def has_trajectory(self) -> bool:
        return self.trajectory is not None


# Frozen cohort: (short_name, source_job_dir, attempt_label)
COHORT: list[tuple[str, str, str]] = [
    ("flipt", "final-flipt", "original"),
    ("openlibrary", "f3-openlibrary-a1", "original"),
    ("teleport", "f3-teleport-a1", "original"),
    ("ansible", "f3-ansible-a1", "original"),
    ("element-web", "f3-elementweb-a1", "original"),
    ("vuls", "f3-vuls-a1", "original"),
    ("NodeBB", "final-nodebb", "original"),
    ("NodeBB-recovery", "nodebb-recovery", "recovery"),
]

# V3.2 semantic verdicts from the frozen Phase 2 findings (read-only labels).
SEMANTIC_VERDICTS: dict[str, str] = {
    "flipt": "CONFIRMED_CORRECT",
    "openlibrary": "CONFIRMED_CORRECT",
    "teleport": "CONFIRMED_CORRECT",
    "ansible": "CONFIRMED_CORRECT",
    "element-web": "CONFIRMED_CORRECT",
    "vuls": "GENUINE_AGENT_FAILURE",
    "NodeBB": "INCONCLUSIVE",
    "NodeBB-recovery": "CONFIRMED_CORRECT",
}

# V3.1 execution-validity labels from the frozen Phase 1B findings (read-only).
# The original NodeBB run had no model responses and a contaminated patch, so
# V3.1 classified it INVALID; every other cohort run executed validly.
EXECUTION_VALIDITY: dict[str, str] = {
    "flipt": "VALID",
    "openlibrary": "VALID",
    "teleport": "VALID",
    "ansible": "VALID",
    "element-web": "VALID",
    "vuls": "VALID",
    "NodeBB": "INVALID",
    "NodeBB-recovery": "VALID",
}


def _first_instance_dir(job_dir: Path) -> Path | None:
    if not job_dir.exists():
        return None
    for child in sorted(job_dir.iterdir()):
        if child.is_dir() and child.name.startswith("instance_"):
            return child
    return None


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def load_task_evidence(
    root: Path,
    short_name: str,
    job_dir_name: str,
    attempt: str,
) -> TaskEvidence:
    job_dir = root / "jobs" / job_dir_name
    inst = _first_instance_dir(job_dir)
    notes: list[str] = []

    # Submitted patch.
    patch_path = None
    patch_text = None
    if inst is not None:
        cand = inst / "agent" / "model.patch"
        if cand.exists():
            patch_path = cand
            patch_text = cand.read_text(encoding="utf-8", errors="replace")

    # V3.1 classification: prefer an on-disk replay record; otherwise use the
    # frozen Phase 1B validity label. The label is evidence, not a diagnosis.
    execution_validity = EXECUTION_VALIDITY.get(short_name, "UNKNOWN")
    replay = None
    replay_path = None
    if inst is not None:
        rp = inst / "agent" / "dataforge_replay.json"
        if rp.exists():
            replay_path = rp
            replay = _read_json(rp)
        if replay and replay.get("replay_status"):
            execution_validity = "VALID" if replay["replay_status"] == "VALID" else "INVALID"

    # Original score and usage from the trial result.json (redaction-safe).
    original_score = None
    if inst is not None:
        res = _read_json(inst / "result.json")
        if res is not None:
            original_score = _score_from_result(res)

    # Trajectory (may be absent — that is itself evidence).
    trajectory = None
    traj_path = (inst / "agent" / "mini-swe-agent.trajectory.json") if inst else None
    if traj_path and traj_path.exists():
        from dataforge_v3.intelligence.trajectory import load_trajectory_file

        try:
            trajectory = load_trajectory_file(traj_path, task_id=short_name, attempt=attempt)
        except ValidityError as exc:
            notes.append(f"trajectory load failed: {exc}")
    else:
        notes.append("no trajectory artifact present (agent did not produce one)")

    return TaskEvidence(
        task_id=short_name,
        short_name=short_name,
        attempt=attempt,
        execution_validity=execution_validity,
        semantic_verdict=SEMANTIC_VERDICTS.get(short_name),
        original_score=original_score,
        trajectory=trajectory,
        patch_path=patch_path,
        patch_text=patch_text,
        replay_path=replay_path,
        replay=replay,
        notes=notes,
    )


def _score_from_result(res: dict) -> float | None:
    # Harbor records the reward at verifier_result.rewards.reward.
    vr = res.get("verifier_result")
    if isinstance(vr, dict):
        rewards = vr.get("rewards")
        if isinstance(rewards, dict):
            v = rewards.get("reward")
            if isinstance(v, (int, float)):
                return float(v)
    for key in ("reward", "score"):
        v = res.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    metrics = res.get("metrics")
    if isinstance(metrics, dict):
        for key in ("reward", "score"):
            v = metrics.get(key)
            if isinstance(v, (int, float)):
                return float(v)
    return None


def _usage_from_result(res: dict) -> tuple[float | None, int | None]:
    ar = res.get("agent_result") or {}
    cost = ar.get("cost_usd")
    cost = float(cost) if isinstance(cost, (int, float)) else None
    tokens = None
    if isinstance(ar.get("n_input_tokens"), int) and isinstance(ar.get("n_output_tokens"), int):
        tokens = ar["n_input_tokens"] + ar["n_output_tokens"]
    return cost, tokens


def load_cohort(root: Path) -> list[TaskEvidence]:
    return [load_task_evidence(root, name, job, attempt) for (name, job, attempt) in COHORT]


# --------------------------------------------------------------------------
# V3.2 semantic-evidence adapters (Component A part 3): bind a task to the V3.2
# frozen clause definitions and probe results. These are read-only labels; the
# attribution engine derives findings from them, it does not re-adjudicate.
# --------------------------------------------------------------------------

SEMANTIC_AUDIT_JSON = "findings/semantic_audit.json"
EXPANSION_EVIDENCE_JSON = "findings/expansion_semantic_evidence.json"
VULS_EVIDENCE_JSON = "findings/vuls_semantic_evidence.json"


def _contract_clauses(short_name: str):
    """Return the V3.2 ContractClause list for a task, or [] if none."""
    module_name = {
        "element-web": "elementweb",
        "NodeBB": None,
        "NodeBB-recovery": None,
    }.get(short_name, short_name.replace("-", "_"))
    if not module_name:
        return []
    try:
        import importlib

        mod = importlib.import_module(f"dataforge_v3.semantic.tasks.{module_name}")
    except ImportError:
        return []
    return list(getattr(mod, "CONTRACT", []))


def load_semantic_input(root: Path, short_name: str) -> "SemanticInput | None":
    """Assemble the V3.2 semantic input for a task from frozen findings.

    Sources, in priority order:
      1. `findings/vuls_semantic_evidence.json`   (probes carry clause ids)
      2. `findings/semantic_audit.json`           (probes + clauses verbatim)
      3. `findings/expansion_semantic_evidence.json` (per-candidate failing names)
    Returns None when the task has no independent semantic evidence (e.g. NodeBB).
    """
    from dataforge_v3.intelligence.attribution import Clause, ProbeFinding, SemanticInput

    clauses = [
        Clause(
            id=c.id,
            kind=c.kind.value,
            statement=c.statement,
            source=c.source,
            tested_by_original=list(c.tested_by_original),
        )
        for c in _contract_clauses(short_name)
    ]
    clause_ids = {c.id for c in clauses}

    # (1) vuls
    p = root / VULS_EVIDENCE_JSON
    if short_name == "vuls" and p.exists():
        data = _read_json(p) or {}
        sub = data.get("deepseek_score_only")
        if isinstance(sub, dict):
            probes = [
                ProbeFinding(
                    name=pr.get("name", "?"),
                    passed=bool(pr.get("passed")),
                    clauses=list(pr.get("clauses", [])),
                    detail=pr.get("detail", ""),
                    counterexample=pr.get("counterexample"),
                )
                for pr in sub.get("probes", [])
            ]
            return SemanticInput(
                verdict=SEMANTIC_VERDICTS.get(short_name),
                confidence="high",
                clauses=clauses,
                probes=probes,
                evidence_artifact=VULS_EVIDENCE_JSON,
            )

    # (2) semantic_audit.json (flipt, openlibrary): clauses + probes verbatim
    p = root / SEMANTIC_AUDIT_JSON
    if p.exists():
        data = _read_json(p) or {}
        entry = data.get(short_name)
        if isinstance(entry, dict):
            if not clauses and entry.get("clauses"):
                clauses = [
                    Clause(
                        id=c["id"],
                        kind=c.get("kind", "POSTCONDITION"),
                        statement=c.get("statement", ""),
                        source=c.get("source", ""),
                        tested_by_original=list(c.get("tested_by_original", [])),
                    )
                    for c in entry["clauses"]
                ]
            probes = [
                ProbeFinding(
                    name=pr.get("name", "?"),
                    passed=bool(pr.get("passed")),
                    clauses=list(pr.get("clauses", [])),
                    detail=pr.get("detail", ""),
                    counterexample=pr.get("counterexample"),
                )
                for pr in entry.get("probes", [])
            ]
            return SemanticInput(
                verdict=entry.get("verdict") or SEMANTIC_VERDICTS.get(short_name),
                confidence=entry.get("confidence"),
                clauses=clauses,
                probes=probes,
                evidence_artifact=SEMANTIC_AUDIT_JSON,
            )

    # (3) expansion_semantic_evidence.json: per-candidate failing probe names.
    p = root / EXPANSION_EVIDENCE_JSON
    if p.exists():
        data = _read_json(p) or {}
        entry = data.get(short_name)
        if isinstance(entry, dict) and "deepseek" in entry:
            ds = entry["deepseek"]
            probes = _probes_from_names(ds.get("failing", []), clause_ids)
            return SemanticInput(
                verdict=SEMANTIC_VERDICTS.get(short_name),
                confidence="medium" if short_name == "element-web" else "high",
                clauses=clauses,
                probes=probes,
                evidence_artifact=EXPANSION_EVIDENCE_JSON,
            )

    return None


def _probes_from_names(names: list[str], clause_ids: set[str]) -> list["ProbeFinding"]:
    """Map recorded failing probe names to clauses where the name is a clause id
    or a contraction of one (e.g. `test_df_gzip_decode` -> `gzip.decode`)."""
    from dataforge_v3.intelligence.attribution import ProbeFinding

    probes: list[ProbeFinding] = []
    for name in names:
        clauses = _match_clause(name, clause_ids)
        probes.append(
            ProbeFinding(name=name, passed=False, clauses=clauses, detail="recorded as failing")
        )
    return probes


def _match_clause(name: str, clause_ids: set[str]) -> list[str]:
    if name in clause_ids:
        return [name]
    compact = name.replace("test_df_", "").replace("test_", "")
    for cid in clause_ids:
        if compact == cid or compact.replace("_", ".") == cid:
            return [cid]
        if cid.split(".")[-1] in compact:
            return [cid]
    return []
