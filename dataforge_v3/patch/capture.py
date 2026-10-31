"""Patch capture with provenance-safe staging.

The upstream locked protocol uses ``git add -A; git diff --cached``. That stages
every untracked file in the image, including runtime state that existed before the
agent started. This module implements the two-phase capture that V3.1 requires:
snapshot the repository, run the agent, then capture only tracked deltas plus
newly created untracked files that were absent from the pre-agent snapshot.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        errors="replace",
    )


@dataclass
class RepoSnapshot:
    head: str
    tracked: set[str] = field(default_factory=set)
    untracked: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "head": self.head,
            "tracked": sorted(self.tracked),
            "untracked": sorted(self.untracked),
        }


def snapshot_repo(repo: Path) -> RepoSnapshot:
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    tracked = set(_git(repo, "ls-files").stdout.splitlines())
    raw = _git(repo, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return RepoSnapshot(head=head, tracked=tracked, untracked=set(raw))


def _status_paths(repo: Path) -> tuple[set[str], set[str]]:
    out = _git(repo, "status", "--porcelain", "--untracked-files=all").stdout
    modified: set[str] = set()
    untracked: set[str] = set()
    for line in out.splitlines():
        if not line.strip():
            continue
        code, path = line[:2], line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if code == "??":
            untracked.add(path)
        else:
            modified.add(path)
    return modified, untracked


def capture_patch(repo: Path, before: RepoSnapshot, patch_out: Path) -> dict:
    """Capture tracked modifications plus genuinely new files, never baseline untracked state."""
    modified, untracked = _status_paths(repo)
    created = sorted(untracked - before.untracked)
    paths = sorted(modified | set(created))
    if paths:
        _git(repo, "add", "-N", "--", *paths)
        diff = _git(repo, "diff", "--binary", "--", *paths).stdout
        _git(repo, "reset", "-q", "--", *paths)
    else:
        diff = ""
    patch_out.write_text(diff, encoding="utf-8", newline="\n")
    return {
        "head": before.head,
        "tracked_modified": sorted(modified),
        "new_files": created,
        "excluded_preexisting_untracked": sorted(untracked & before.untracked),
        "included_paths": paths,
        "patch_bytes": len(diff.encode("utf-8")),
    }
