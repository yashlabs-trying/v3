"""Fail-closed replay decisions and post-application state checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataforge_v3.model import PatchVerdict, VerificationStatus


@dataclass
class AcceptedChange:
    path: str
    is_new: bool = False
    is_delete: bool = False
    is_rename: bool = False
    old_path: str | None = None


@dataclass
class PostStateReport:
    touched: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unexpected and not self.missing and not self.reasons


def strict_apply_command(patch_target: str, repo_candidates: tuple[str, ...] = ("/app", "/testbed")) -> str:
    cd = "cd /app 2>/dev/null || cd /testbed 2>/dev/null || exit 90"
    return (
        f"set -u; {cd}; "
        f"git apply --check --whitespace=nowarn {patch_target}; rc=$?; "
        f"if [ $rc -ne 0 ]; then echo DATAFORGE_APPLY_CHECK_RC=$rc; exit $rc; fi; "
        f"git apply --whitespace=nowarn {patch_target}; rc=$?; "
        f"echo DATAFORGE_APPLY_RC=$rc; exit $rc"
    )


def parse_porcelain(porcelain: str) -> list[str]:
    paths: list[str] = []
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        rest = line[3:].strip()
        if " -> " in rest:
            old, new = rest.split(" -> ", 1)
            paths.extend([old.strip(), new.strip()])
        else:
            paths.append(rest.strip('"'))
    return paths


def assess_post_state(
    accepted: list[AcceptedChange],
    porcelain_after: str,
    baseline_untracked: set[str],
) -> PostStateReport:
    touched = parse_porcelain(porcelain_after)
    touched_set = set(touched)
    accepted_paths = {a.path for a in accepted}
    accepted_old = {a.old_path for a in accepted if a.old_path}
    report = PostStateReport(touched=sorted(touched_set))

    for a in accepted:
        targets = {a.path}
        if a.old_path:
            targets.add(a.old_path)
        if not (targets & touched_set):
            report.missing.append(a.path)

    for path in touched_set:
        if path in accepted_paths or path in accepted_old:
            continue
        if path in baseline_untracked:
            continue
        report.unexpected.append(path)

    if report.missing:
        report.reasons.append(f"expected changes absent after apply: {sorted(report.missing)}")
    if report.unexpected:
        report.reasons.append(f"unexpected paths changed after apply: {sorted(report.unexpected)}")
    return report


def decide_replay(
    *,
    patch_verdict: PatchVerdict,
    apply_rc: int | None,
    accepted_count: int,
    post_state: PostStateReport | None,
) -> tuple[VerificationStatus, list[str]]:
    reasons: list[str] = []
    if patch_verdict == PatchVerdict.ABSENT:
        return VerificationStatus.PATCH_MISSING, ["patch artifact is missing"]
    if patch_verdict == PatchVerdict.EMPTY:
        return VerificationStatus.PATCH_EMPTY, ["patch artifact is a valid empty submission"]
    if patch_verdict == PatchVerdict.INVALID:
        return VerificationStatus.PATCH_INVALID, ["patch failed structural validation"]
    if patch_verdict == PatchVerdict.CONTAMINATED_ONLY:
        return VerificationStatus.PATCH_INVALID, ["patch contains only pre-existing environment artifacts"]
    if patch_verdict == PatchVerdict.REVIEW_REQUIRED:
        return VerificationStatus.REVIEW_REQUIRED, ["patch needs human review before an authoritative verdict"]
    if accepted_count == 0:
        return VerificationStatus.PATCH_APPLICATION_ERROR, ["no accepted changes to apply"]
    if apply_rc is None:
        return VerificationStatus.PATCH_APPLICATION_ERROR, ["patch application was never executed"]
    if apply_rc != 0:
        return VerificationStatus.PATCH_APPLICATION_ERROR, [f"git apply failed with rc={apply_rc}"]
    if post_state is None:
        return VerificationStatus.PATCH_APPLICATION_ERROR, ["post-application state was not captured"]
    if not post_state.ok:
        reasons.extend(post_state.reasons)
        return VerificationStatus.PATCH_APPLICATION_ERROR, reasons
    return VerificationStatus.VALID, []


def coerce_accepted(entries: list[dict[str, Any]]) -> list[AcceptedChange]:
    out: list[AcceptedChange] = []
    for e in entries:
        if e.get("decision") not in ("accepted", "accepted_test_touch"):
            continue
        out.append(
            AcceptedChange(
                path=e.get("path") or "",
                is_new=bool(e.get("is_new")),
                is_delete=bool(e.get("is_delete")),
                is_rename=bool(e.get("is_rename")),
                old_path=e.get("old_path"),
            )
        )
    return out
