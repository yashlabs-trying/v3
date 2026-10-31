"""Adapter: turn real Harbor job artifacts into DataForge verdicts."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dataforge_v3.evidence.parser import (
    Observation,
    load_required,
    parse_output,
    parse_reward,
    read_text,
)
from dataforge_v3.evidence.validation import validate_evidence
from dataforge_v3.lifecycle.failure_classifier import classify_execution, load_trajectory
from dataforge_v3.model import (
    DataForgeResult,
    PatchRecord,
    PatchVerdict,
    VerificationRecord,
    VerificationStatus,
)
from dataforge_v3.patch.validation import parse_patch
from dataforge_v3.reporting.schema import classify_final


@dataclass
class TrialEvidence:
    job_dir: Path
    trial_dir: Path
    result: dict[str, Any]
    task_name: str
    task_id: str
    transcript: str
    trajectory: dict[str, Any] | None
    patch_path: Path | None
    patch_text: str
    verifier_output: Path
    verifier_reward: Path
    raw_stdout: str
    raw_stderr: str
    df_replay: dict[str, Any] | None
    upstream_replay: dict[str, Any] | None
    extra: dict[str, Any] = field(default_factory=dict)


def discover_trials(job_dir: Path) -> list[Path]:
    out: list[Path] = []
    for child in sorted(job_dir.iterdir()):
        if child.is_dir() and (child / "result.json").exists() and child.name.startswith("instance_"):
            out.append(child)
    return out


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _find_optional(trial: Path, *rels: str) -> Path | None:
    for rel in rels:
        p = trial / rel
        if p.exists():
            return p
    return None


def localize_path(value: str) -> Path:
    """Resolve a WSL /mnt/<drive>/... path when auditing from Windows."""
    path = Path(value)
    if path.exists():
        return path
    if os.name == "nt" and value.startswith("/mnt/") and len(value) > 6:
        drive = value[5].upper()
        candidate = Path(f"{drive}:/{value[7:]}")
        if candidate.exists():
            return candidate
    return path


def load_trial(job_dir: Path, trial_dir: Path) -> TrialEvidence:
    result = _read_json(trial_dir / "result.json") or {}
    task_name = str(result.get("task_name") or "")
    task_id = task_name.split("/")[-1] if task_name else trial_dir.name
    transcript = read_text(trial_dir / "agent" / "mini-swe-agent.txt")
    traj_path = _find_optional(trial_dir, "agent/trajectory.json", "agent/mini-swe-agent.trajectory.json")
    trajectory = load_trajectory(traj_path)
    patch_path = _find_optional(trial_dir, "agent/model.patch")
    patch_text = read_text(patch_path) if patch_path else ""
    df_replay = _read_json(trial_dir / "agent" / "dataforge_replay.json")
    upstream_replay = _read_json(trial_dir / "agent" / "replay.json")
    return TrialEvidence(
        job_dir=job_dir,
        trial_dir=trial_dir,
        result=result,
        task_name=task_name,
        task_id=task_id,
        transcript=transcript,
        trajectory=trajectory,
        patch_path=patch_path,
        patch_text=patch_text,
        verifier_output=trial_dir / "verifier" / "output.json",
        verifier_reward=trial_dir / "verifier" / "reward.txt",
        raw_stdout=read_text(trial_dir / "verifier" / "run-script-stdout.txt"),
        raw_stderr=read_text(trial_dir / "verifier" / "run-script-stderr.txt"),
        df_replay=df_replay,
        upstream_replay=upstream_replay,
    )


def resolve_task_config(task_id: str, explicit: Path | None, audit_root: Path | None, upstream_root: Path | None) -> Path | None:
    if explicit and explicit.exists():
        return explicit
    if audit_root:
        candidate = audit_root / task_id / "tests" / "config.json"
        if candidate.exists():
            return candidate
    if upstream_root:
        candidate = upstream_root / "v2" / "tasks" / task_id / "tests" / "config.json"
        if candidate.exists():
            return candidate
    return None


def _patch_record_from_df(replay: dict[str, Any]) -> tuple[PatchRecord, dict[str, Any], str | None]:
    payload = replay.get("patch") or {}
    verdict = PatchVerdict(payload.get("verdict", "UNKNOWN")) if payload.get("verdict") in PatchVerdict._value2member_map_ else PatchVerdict.INVALID
    record = PatchRecord(
        verdict=verdict,
        sha256=payload.get("sha256"),
        size_bytes=payload.get("size_bytes"),
        files_total=int(payload.get("files_total") or 0),
        files_accepted=int(payload.get("files_accepted") or 0),
        files_excluded=list(payload.get("files_excluded") or []),
        entries=list(payload.get("entries") or []),
        reasons=list(payload.get("reasons") or []),
    )
    return record, dict(replay.get("provenance") or {}), replay.get("replay_status")


def _patch_record_structural(text: str, exists: bool = True) -> PatchRecord:
    if not exists:
        return PatchRecord(verdict=PatchVerdict.ABSENT, reasons=["patch artifact is missing"])
    if not text:
        return PatchRecord(verdict=PatchVerdict.EMPTY, size_bytes=0, reasons=["zero-byte patch"])
    analysis = parse_patch(text)
    if analysis.is_empty:
        return PatchRecord(verdict=PatchVerdict.EMPTY, sha256=analysis.sha256, size_bytes=0, reasons=["zero-byte patch"])
    if not analysis.valid_structure:
        return PatchRecord(
            verdict=PatchVerdict.INVALID,
            sha256=analysis.sha256,
            size_bytes=analysis.size_bytes,
            files_total=len(analysis.entries),
            reasons=analysis.issues,
        )
    return PatchRecord(
        verdict=PatchVerdict.VALID,
        sha256=analysis.sha256,
        size_bytes=analysis.size_bytes,
        files_total=len(analysis.entries),
        files_accepted=len(analysis.entries),
        reasons=["structural validation only; no pristine baseline available in this artifact set"],
    )


def upstream_replay_status(replay: dict[str, Any] | None) -> tuple[VerificationStatus, list[str], dict[str, Any]]:
    if not replay:
        return VerificationStatus.UNKNOWN, ["no replay evidence"], {}
    apply_rc = replay.get("apply_rc")
    diffstat = replay.get("post_apply_diffstat") or ""
    changed_lines = [line for line in diffstat.splitlines() if " | " in line]
    if apply_rc == 0 and changed_lines:
        return VerificationStatus.VALID, [], replay
    if apply_rc == 0 and not changed_lines:
        return VerificationStatus.PATCH_APPLICATION_ERROR, ["replay succeeded but changed nothing"], replay
    if apply_rc != 0 and changed_lines:
        return (
            VerificationStatus.PATCH_APPLICATION_ERROR,
            [f"replay rc={apply_rc} yet {len(changed_lines)} files changed (non-atomic fallback application)"],
            replay,
        )
    return (
        VerificationStatus.PATCH_APPLICATION_ERROR,
        [f"replay failed with rc={apply_rc} and changed nothing"],
        replay,
    )


def _resolve_source_trial(job_dir: Path, replay: dict[str, Any]) -> Path | None:
    source_trial = replay.get("source_trial")
    if source_trial:
        direct = localize_path(str(source_trial))
        if direct.exists():
            return direct
        source_job = replay.get("source_job")
        if source_job:
            candidate = job_dir.parent.parent / Path(str(source_job)).name / Path(str(source_trial)).name
            if candidate.exists():
                return candidate
    return None


def assess_trial(
    job_dir: Path,
    *,
    task_config: Path | None = None,
    audit_root: Path | None = None,
    upstream_root: Path | None = None,
) -> DataForgeResult:
    trials = discover_trials(job_dir)
    if not trials:
        raise FileNotFoundError(f"no Harbor trial directory under {job_dir}")
    evidence = load_trial(job_dir, trials[0])
    execution_evidence = evidence
    if evidence.df_replay:
        source_path = _resolve_source_trial(job_dir, evidence.df_replay)
        if source_path is not None:
            execution_evidence = load_trial(source_path.parent, source_path)
    execution = classify_execution(
        transcript=execution_evidence.transcript,
        trajectory=execution_evidence.trajectory,
        trial_result=execution_evidence.result,
    )
    reward = parse_reward(evidence.verifier_reward)
    if reward is None:
        vr = (evidence.result.get("verifier_result") or {}).get("rewards") or {}
        if isinstance(vr, dict) and vr.get("reward") is not None:
            try:
                reward = float(vr["reward"])
            except (TypeError, ValueError):
                reward = None
    if reward is None and execution_evidence is not evidence:
        reward = parse_reward(execution_evidence.verifier_reward)

    config = resolve_task_config(evidence.task_id, task_config, audit_root, upstream_root)
    output_issues: list[str] = []
    observations: list[Observation] = []
    required = None
    if config is None:
        output_issues.append("task test contract not found")
    else:
        required = load_required(config)
        observations, output_issues = parse_output(evidence.verifier_output)

    evidence_status = VerificationStatus.UNKNOWN
    ev = None
    if required is not None:
        ev = validate_evidence(
            reward=reward,
            observations=observations,
            required=required,
            output_issues=output_issues,
            raw_stdout=evidence.raw_stdout,
            raw_stderr=evidence.raw_stderr,
        )
        evidence_status = ev.status

    provenance: dict[str, Any] = {}
    if evidence.df_replay:
        patch_record, provenance, replay_status = _patch_record_from_df(evidence.df_replay)
        replay_dict = dict(evidence.df_replay)
        if replay_status in VerificationStatus._value2member_map_:
            replay_verification = VerificationStatus(replay_status)
        else:
            replay_verification = VerificationStatus.UNKNOWN
        replay_reasons = list(evidence.df_replay.get("replay_reasons") or [])
    else:
        patch_record = _patch_record_structural(evidence.patch_text, exists=evidence.patch_path is not None)
        replay_verification, replay_reasons, replay_dict = upstream_replay_status(evidence.upstream_replay)
        provenance = {"note": "no DataForge replay evidence; provenance baseline unavailable"}
        if evidence.upstream_replay is None and evidence_status is VerificationStatus.VALID:
            replay_verification = VerificationStatus.UNVERIFIED_ORIGINAL
            replay_reasons = [
                "original harness verdict only; no independent DataForge replay in this legacy artifact set"
            ]

    if replay_verification == VerificationStatus.VALID:
        verification = VerificationRecord(
            status=evidence_status,
            reward=reward,
            required_tests=len(required.all_required) if required else None,
            passed_required=ev.passed_required if ev else None,
            missing_required=ev.absent_required if ev else [],
            contradictory_tests=ev.contradictory if ev else [],
            reasons=(ev.reasons if ev else []) + replay_reasons,
            evidence=(ev.to_dict() if ev else {}),
        )
    else:
        verification = VerificationRecord(
            status=replay_verification,
            reward=reward,
            required_tests=len(required.all_required) if required else None,
            passed_required=ev.passed_required if ev else None,
            missing_required=ev.absent_required if ev else [],
            contradictory_tests=ev.contradictory if ev else [],
            reasons=replay_reasons + (ev.reasons if ev else []),
            evidence={"evidence_validation": ev.to_dict() if ev else {}, "replay": replay_dict},
        )

    classification, final_reasons = classify_final(execution, patch_record, verification)
    if final_reasons:
        verification.reasons.extend(final_reasons)

    return DataForgeResult(
        task=evidence.task_id.split("__")[0].replace("instance_", "") if "__" in evidence.task_id else job_dir.name,
        task_id=evidence.task_id,
        original_reward=reward,
        execution=execution,
        patch=patch_record,
        verification=verification,
        classification=classification,
        lifecycle=list(evidence.df_replay.get("lifecycle") or []) if evidence.df_replay else [],
        replay=replay_dict,
        provenance=provenance,
    )


def assess_job_fleet(
    job_map: dict[str, Path],
    *,
    audit_root: Path | None = None,
    upstream_root: Path | None = None,
) -> list[DataForgeResult]:
    return [assess_trial(job, audit_root=audit_root, upstream_root=upstream_root) for _, job in sorted(job_map.items())]
