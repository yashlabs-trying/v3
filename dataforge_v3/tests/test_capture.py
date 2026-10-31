from __future__ import annotations

import subprocess
from pathlib import Path

from dataforge_v3.patch.capture import capture_patch, snapshot_repo
from dataforge_v3.patch.validation import parse_patch


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "df@example.invalid")
    _git(repo, "config", "user.name", "DataForge")
    (repo / "src").mkdir()
    (repo / "src" / "app.js").write_text("old\n")
    (repo / "appendonlydir").mkdir()
    (repo / "appendonlydir" / "state.aof").write_text("preexisting\n")
    _git(repo, "add", "src/app.js")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def test_safe_capture_excludes_preexisting_untracked_state(tmp_path):
    repo = _repo(tmp_path)
    before = snapshot_repo(repo)
    (repo / "src" / "app.js").write_text("new\n")
    (repo / "src" / "new.js").write_text("created by agent\n")
    out = tmp_path / "model.patch"
    report = capture_patch(repo, before, out)
    assert report["new_files"] == ["src/new.js"]
    assert report["excluded_preexisting_untracked"] == ["appendonlydir/state.aof"]
    text = out.read_text()
    assert "appendonlydir" not in text
    assert "src/app.js" in text and "src/new.js" in text


def test_legacy_git_add_all_contaminates_patch(tmp_path):
    repo = _repo(tmp_path)
    (repo / "src" / "app.js").write_text("new\n")
    _git(repo, "add", "-A")
    cached = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached"], capture_output=True, text=True, check=True
    ).stdout
    assert "appendonlydir/state.aof" in cached
    analysis = parse_patch(cached)
    assert any(e.path == "appendonlydir/state.aof" for e in analysis.entries)
