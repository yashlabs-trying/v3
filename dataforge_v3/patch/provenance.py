"""Patch provenance: decide which diff entries are legitimate agent changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataforge_v3.model import PatchRecord, PatchVerdict
from dataforge_v3.patch.validation import PatchAnalysis, PatchEntry

SOURCE = "AGENT_CHANGE"
PREEXISTING = "PREEXISTING_UNTRACKED"
PREEXISTING_MODIFIED = "PREEXISTING_UNTRACKED_MODIFIED"
BINARY_REVIEW = "BINARY_ADDITION_REVIEW"
TEST_FILE = "TEST_FILE_CHANGE"

_TEST_DIRS = {"tests", "test", "__tests__", "spec", "specs"}
_DATA_DIRS = {"testdata", "test_data", "fixtures", "fixture", "mocks", "mock", "__snapshots__"}


@dataclass
class BaselineState:
    tracked: set[str] = field(default_factory=set)
    untracked: set[str] = field(default_factory=set)
    head: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"tracked_count": len(self.tracked), "untracked_count": len(self.untracked),
                "untracked_sample": sorted(self.untracked)[:50]}


def parse_git_status(porcelain: str) -> BaselineState:
    tracked: set[str] = set()
    untracked: set[str] = set()
    for line in porcelain.splitlines():
        if not line.strip():
            continue
        code, _, path = line[:2], line[2:], line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if code == "??":
            untracked.add(path)
        else:
            tracked.add(path)
    return BaselineState(tracked=tracked, untracked=untracked)


def is_test_code(path: str) -> bool:
    segs = path.split("/")
    parents, base = segs[:-1], segs[-1]
    if any(s in _DATA_DIRS for s in parents):
        return False
    if any(s in _TEST_DIRS for s in parents):
        return True
    if base == "conftest.py":
        return True
    if base.endswith(("_test.go", "_test.py", "_test.js", "_test.jsx", "_test.ts", "_test.tsx")):
        return True
    if base.startswith("test_") and base.endswith(".py"):
        return True
    if ".test." in base or ".spec." in base:
        return True
    return False


def _is_data_dir(path: str) -> bool:
    return any(seg in _DATA_DIRS for seg in path.split("/")[:-1])


def classify_entry(entry: PatchEntry, baseline: BaselineState) -> tuple[str, str | None]:
    path = entry.path
    if entry.is_new and path in baseline.untracked:
        return PREEXISTING, f"{path} is untracked in the pristine image before the agent starts"
    if not entry.is_new and path in baseline.untracked:
        return PREEXISTING_MODIFIED, f"{path} is a pre-existing untracked file modified by the patch"
    if entry.is_binary:
        return BINARY_REVIEW, f"{path} is a binary addition that cannot be provenance-checked"
    if is_test_code(path) and not _is_data_dir(path):
        return TEST_FILE, f"{path} is test code; the official verifier resets test files and reapplies test_patch"
    return SOURCE, None


def analyze_provenance(
    analysis: PatchAnalysis,
    baseline: BaselineState,
) -> tuple[PatchRecord, dict[str, Any], str, list[str]]:
    details: list[dict[str, Any]] = []
    accepted: list[str] = []
    review: list[str] = []
    test_touched: list[str] = []
    excluded: list[dict[str, Any]] = []
    raw_sections: list[str] = []

    for entry in analysis.entries:
        kind, reason = classify_entry(entry, baseline)
        record = {
            "index": entry.index,
            "path": entry.path,
            "old_path": entry.old_path,
            "new_path": entry.new_path,
            "kind": kind,
            "is_new": entry.is_new,
            "is_delete": entry.is_delete,
            "is_rename": entry.is_rename,
            "is_binary": entry.is_binary,
            "reason": reason,
            "decision": None,
        }
        if kind in (PREEXISTING, PREEXISTING_MODIFIED):
            record["decision"] = "excluded"
            excluded.append(record)
        elif kind == BINARY_REVIEW:
            record["decision"] = "excluded_review"
            review.append(entry.path)
            excluded.append(record)
        elif kind == TEST_FILE:
            record["decision"] = "accepted_test_touch"
            test_touched.append(entry.path)
            accepted.append(entry.path)
            raw_sections.append(entry.raw)
        else:
            record["decision"] = "accepted"
            accepted.append(entry.path)
            raw_sections.append(entry.raw)
        details.append(record)

    reasons: list[str] = []
    if analysis.issues:
        verdict = PatchVerdict.INVALID
        reasons.extend(analysis.issues)
    elif not analysis.entries:
        verdict = PatchVerdict.EMPTY
        reasons.append("patch contains no diff entries")
    elif review:
        verdict = PatchVerdict.REVIEW_REQUIRED
        reasons.append(f"review-required entries: {review}")
    elif not accepted and excluded:
        verdict = PatchVerdict.CONTAMINATED_ONLY
        reasons.append("every diff entry is pre-existing or unreviewable environment state")
    else:
        verdict = PatchVerdict.VALID

    record = PatchRecord(
        verdict=verdict,
        sha256=analysis.sha256,
        size_bytes=analysis.size_bytes,
        files_total=len(analysis.entries),
        files_accepted=len(accepted),
        files_excluded=excluded,
        entries=details,
        reasons=reasons,
    )
    provenance = {
        "baseline": baseline.to_dict(),
        "accepted": accepted,
        "review_required": review,
        "excluded": excluded,
        "test_files_touched": test_touched,
        "policy": "provenance-based: a path is an environment artifact only if it was already untracked in the pristine image; no extension allow-list is used",
    }
    filtered = "".join(raw_sections)
    return record, provenance, filtered, accepted
