"""Validate that grading evidence is complete, consistent, and non-contradictory."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from dataforge_v3.evidence.parser import Observation, RequiredTests
from dataforge_v3.model import VerificationStatus


@dataclass
class EvidenceValidation:
    status: VerificationStatus
    reward: float | None
    required_count: int
    observed_count: int
    passed_required: int
    absent_required: list[str] = field(default_factory=list)
    not_passed_required: list[str] = field(default_factory=list)
    contradictory: list[str] = field(default_factory=list)
    parser_dropped: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "reward": self.reward,
            "required_count": self.required_count,
            "observed_count": self.observed_count,
            "passed_required": self.passed_required,
            "absent_required": self.absent_required,
            "not_passed_required": self.not_passed_required,
            "contradictory": self.contradictory,
            "parser_dropped": self.parser_dropped,
            "reasons": self.reasons,
        }


def _appears_verbatim(name: str, raw: str) -> bool:
    if name in raw:
        return True
    tail = name.rsplit("/", 1)[-1]
    if "::" in name:
        tail = name.rsplit("::", 1)[-1]
    if tail and re.search(r"(?<![\w/.-])" + re.escape(tail) + r"(?![\w/.-])", raw):
        return True
    return False


def validate_evidence(
    *,
    reward: float | None,
    observations: list[Observation],
    required: RequiredTests,
    output_issues: list[str],
    raw_stdout: str = "",
    raw_stderr: str = "",
    runner_exit_code: int | None = None,
    runner_timed_out: bool = False,
) -> EvidenceValidation:
    required_all = required.all_required
    required_set = set(required_all)
    reasons: list[str] = list(output_issues)

    by_name: dict[str, set[str]] = {}
    passed: set[str] = set()
    for o in observations:
        by_name.setdefault(o.name, set()).add(o.status)
        if o.status == "PASSED":
            passed.add(o.name)

    contradictory = sorted(
        name
        for name, statuses in by_name.items()
        if len({s for s in statuses if s in ("PASSED", "FAILED", "ERROR")}) > 1
    )
    absent = sorted(required_set - set(by_name))
    not_passed = sorted(required_set - passed)

    raw = (raw_stdout or "") + "\n" + (raw_stderr or "")
    parser_dropped = [n for n in absent if raw and _appears_verbatim(n, raw)]

    if runner_timed_out:
        return EvidenceValidation(
            VerificationStatus.TEST_EXECUTION_ERROR,
            reward, len(required_all), len(observations), len(required_set & passed),
            absent, not_passed, contradictory, parser_dropped,
            reasons + ["test runner timed out"],
        )
    if runner_exit_code is not None and runner_exit_code != 0:
        if reward == 1.0:
            return EvidenceValidation(
                VerificationStatus.EVIDENCE_CONTRADICTORY,
                reward, len(required_all), len(observations), len(required_set & passed),
                absent, not_passed, contradictory, parser_dropped,
                reasons + [f"test runner exited {runner_exit_code} but reward is 1.0"],
            )
        if not observations:
            return EvidenceValidation(
                VerificationStatus.TEST_EXECUTION_ERROR,
                reward, len(required_all), len(observations), len(required_set & passed),
                absent, not_passed, contradictory, parser_dropped,
                reasons + [f"test runner exited {runner_exit_code} with no parsed results"],
            )

    if output_issues:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_INCOMPLETE,
            reward, len(required_all), len(observations), len(required_set & passed),
            absent, not_passed, contradictory, parser_dropped, reasons,
        )
    if reward is None:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_INCOMPLETE,
            reward, len(required_all), len(observations), len(required_set & passed),
            absent, not_passed, contradictory, parser_dropped,
            reasons + ["verifier did not produce a reward"],
        )
    if not required_all:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_INCOMPLETE,
            reward, 0, len(observations), 0, absent, not_passed, contradictory, parser_dropped,
            reasons + ["task contract declares no required tests"],
        )
    if not observations:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_INCOMPLETE,
            reward, len(required_all), 0, 0, absent, not_passed, contradictory, parser_dropped,
            reasons + ["verifier produced zero test observations"],
        )
    if contradictory:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_CONTRADICTORY,
            reward, len(required_all), len(observations), len(required_set & passed),
            absent, not_passed, contradictory, parser_dropped,
            reasons + [f"contradictory statuses for: {contradictory}"],
        )
    if parser_dropped:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_INCOMPLETE,
            reward, len(required_all), len(observations), len(required_set & passed),
            absent, not_passed, contradictory, parser_dropped,
            reasons + [f"required tests present in raw output but absent from parser output: {parser_dropped}"],
        )

    expected_pass = not not_passed
    reward_pass = reward >= 0.5
    if reward_pass != expected_pass:
        return EvidenceValidation(
            VerificationStatus.EVIDENCE_CONTRADICTORY,
            reward, len(required_all), len(observations), len(required_set & passed),
            absent, not_passed, contradictory, parser_dropped,
            reasons + [f"reward {reward} disagrees with required-test result (expected_pass={expected_pass})"],
        )
    return EvidenceValidation(
        VerificationStatus.VALID,
        reward, len(required_all), len(observations), len(required_set & passed),
        absent, not_passed, contradictory, parser_dropped,
        reasons,
    )


def required_status_summary(observations: list[Observation], required: RequiredTests) -> dict[str, str]:
    wanted = set(required.all_required)
    summary: dict[str, str] = {}
    for o in observations:
        if o.name in wanted:
            if o.name in summary and summary[o.name] != o.status:
                summary[o.name] = "CONTRADICTORY"
            else:
                summary[o.name] = o.status
    return summary
