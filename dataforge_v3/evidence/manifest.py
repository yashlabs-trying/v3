"""Artifact manifests with hashes stored outside the untrusted workspace."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from dataforge_v3.replay.integrity import sha256_file

DEFAULT_ARTIFACTS = (
    "agent/model.patch",
    "agent/mini-swe-agent.txt",
    "agent/trajectory.json",
    "agent/dataforge_replay.json",
    "agent/replay.json",
    "verifier/output.json",
    "verifier/reward.txt",
    "verifier/run-script-stdout.txt",
    "verifier/run-script-stderr.txt",
    "exception.txt",
)


@dataclass
class ArtifactManifest:
    trial_dir: Path
    entries: dict[str, str]

    def to_dict(self) -> dict:
        return {"trial_dir": str(self.trial_dir), "entries": dict(sorted(self.entries.items()))}


def build_artifact_manifest(trial_dir: Path, extra: tuple[str, ...] = ()) -> ArtifactManifest:
    entries: dict[str, str] = {}
    for rel in tuple(DEFAULT_ARTIFACTS) + extra:
        path = trial_dir / rel
        if path.exists() and path.is_file():
            entries[rel] = sha256_file(path)
    return ArtifactManifest(trial_dir=trial_dir, entries=entries)


def write_artifact_manifest(trial_dir: Path, out_path: Path, extra: tuple[str, ...] = ()) -> ArtifactManifest:
    manifest = build_artifact_manifest(trial_dir, extra)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def verify_artifact_manifest(manifest_path: Path, trial_dir: Path | None = None) -> list[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = Path(trial_dir) if trial_dir else Path(payload["trial_dir"])
    problems: list[str] = []
    for rel, expected in payload["entries"].items():
        path = root / rel
        if not path.exists():
            problems.append(f"missing: {rel}")
        elif sha256_file(path) != expected:
            problems.append(f"hash mismatch: {rel}")
    return problems
