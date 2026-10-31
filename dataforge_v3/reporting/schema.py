"""Per-task result assembly and fleet reporting."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from dataforge_v3.model import (
    DataForgeResult,
    ExecutionRecord,
    ExecutionStatus,
    FinalClassification,
    PatchRecord,
    PatchVerdict,
    VerificationRecord,
    VerificationStatus,
)


def _is_sufficient_execution(execution: ExecutionRecord) -> bool:
    if execution.model_responses is None:
        return False
    if execution.model_responses <= 0:
        return False
    if execution.status in (ExecutionStatus.COMPLETED, ExecutionStatus.INTERRUPTED, ExecutionStatus.EXECUTION_ERROR):
        return True
    return False


def classify_final(
    execution: ExecutionRecord,
    patch: PatchRecord,
    verification: VerificationRecord,
) -> tuple[FinalClassification, list[str]]:
    reasons: list[str] = []
    blocking_patch = {
        PatchVerdict.ABSENT,
        PatchVerdict.INVALID,
        PatchVerdict.CONTAMINATED_ONLY,
        PatchVerdict.REVIEW_REQUIRED,
    }
    blocking_verification = {
        VerificationStatus.PATCH_MISSING,
        VerificationStatus.PATCH_INVALID,
        VerificationStatus.PATCH_APPLICATION_ERROR,
        VerificationStatus.TEST_EXECUTION_ERROR,
        VerificationStatus.EVIDENCE_INCOMPLETE,
        VerificationStatus.EVIDENCE_CONTRADICTORY,
        VerificationStatus.REVIEW_REQUIRED,
        VerificationStatus.UNKNOWN,
    }

    if not _is_sufficient_execution(execution):
        reasons.append(
            f"execution evidence insufficient: status={execution.status.value}, "
            f"model_responses={execution.model_responses}"
        )
        return FinalClassification.INVALID, reasons

    if patch.verdict in blocking_patch:
        reasons.append(f"patch integrity is {patch.verdict.value}")
        return FinalClassification.INVALID, reasons

    if verification.status in blocking_verification:
        reasons.append(f"verification integrity is {verification.status.value}")
        return FinalClassification.INVALID, reasons

    if patch.verdict == PatchVerdict.EMPTY:
        reasons.append("agent ran and produced an explicitly empty submission")
        return FinalClassification.FAIL, reasons

    if verification.reward is None:
        reasons.append("no authoritative reward")
        return FinalClassification.INVALID, reasons

    if verification.status == VerificationStatus.UNVERIFIED_ORIGINAL:
        reasons.append("classified from original harness verdict; not independently replay-verified")

    if verification.reward >= 0.5:
        return FinalClassification.PASS, reasons
    return FinalClassification.FAIL, reasons


@dataclass
class FleetReport:
    results: list[DataForgeResult]

    def to_dict(self) -> dict[str, Any]:
        buckets: dict[str, int] = {}
        for r in self.results:
            buckets[r.classification.value] = buckets.get(r.classification.value, 0) + 1
        return {
            "count": len(self.results),
            "buckets": buckets,
            "results": [r.to_dict() for r in self.results],
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def write_comparison_csv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "task",
            "task_id",
            "original_reward",
            "original_verdict",
            "dataforge_classification",
            "execution_status",
            "verification_status",
            "patch_verdict",
            "patch_sha256",
            "files_accepted",
            "files_excluded",
            "reasons",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in self.results:
                original = "PASS" if (r.original_reward or 0) >= 0.5 else "FAIL"
                writer.writerow(
                    {
                        "task": r.task,
                        "task_id": r.task_id,
                        "original_reward": r.original_reward,
                        "original_verdict": original,
                        "dataforge_classification": r.classification.value,
                        "execution_status": r.execution.status.value,
                        "verification_status": r.verification.status.value,
                        "patch_verdict": r.patch.verdict.value,
                        "patch_sha256": r.patch.sha256 or "",
                        "files_accepted": r.patch.files_accepted,
                        "files_excluded": len(r.patch.files_excluded),
                        "reasons": " | ".join(r.verification.reasons + r.patch.reasons),
                    }
                )


def summarize_metrics(results: Iterable[DataForgeResult]) -> dict[str, Any]:
    results = list(results)
    preserved_pass = 0
    preserved_fail = 0
    incorrectly_invalidated = 0
    infrastructure_caught = 0
    contaminated_caught = 0
    replay_failures_caught = 0
    for r in results:
        original = r.original_reward
        if original is not None and original >= 0.5:
            if r.classification == FinalClassification.PASS:
                preserved_pass += 1
            elif r.classification == FinalClassification.INVALID:
                incorrectly_invalidated += 1
        elif original is not None:
            if r.classification == FinalClassification.FAIL:
                preserved_fail += 1
            elif r.classification == FinalClassification.INVALID:
                pass
        if r.classification == FinalClassification.INVALID and r.execution.model_responses == 0:
            infrastructure_caught += 1
        if r.patch.verdict == PatchVerdict.CONTAMINATED_ONLY:
            contaminated_caught += 1
        if r.verification.status == VerificationStatus.PATCH_APPLICATION_ERROR:
            replay_failures_caught += 1
    return {
        "tasks": len(results),
        "valid_pass_preserved": preserved_pass,
        "valid_fail_preserved": preserved_fail,
        "legitimate_verdicts_incorrectly_invalidated": incorrectly_invalidated,
        "infrastructure_nonexecution_flagged_invalid": infrastructure_caught,
        "contamination_only_patches_flagged": contaminated_caught,
        "replay_application_errors_flagged": replay_failures_caught,
    }
