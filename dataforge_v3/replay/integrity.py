"""Evidence hashing stored outside the untrusted agent workspace."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class IntegrityManifest:
    root: Path
    entries: dict[str, str] = field(default_factory=dict)

    def record_file(self, path: Path) -> str:
        digest = sha256_file(path)
        try:
            key = str(path.resolve().relative_to(self.root.resolve()))
        except ValueError:
            key = str(path.resolve())
        self.entries[key] = digest
        return digest

    def verify(self) -> list[str]:
        problems: list[str] = []
        for key, expected in self.entries.items():
            path = Path(key) if Path(key).is_absolute() else self.root / key
            if not path.exists():
                problems.append(f"missing: {key}")
                continue
            actual = sha256_file(path)
            if actual != expected:
                problems.append(f"hash mismatch: {key}")
        return problems

    def to_dict(self) -> dict:
        return {"root": str(self.root), "entries": dict(sorted(self.entries.items()))}

    def write(self, out: Path) -> None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def verify_manifest(manifest_path: Path) -> list[str]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = Path(payload["root"])
    manifest = IntegrityManifest(root=root, entries=dict(payload["entries"]))
    return manifest.verify()
