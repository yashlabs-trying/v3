"""V3.3 — evidence resolution and verification.

A `DiagnosticClaim` or `Finding` may only be authoritative if every `EvidenceRef`
resolves to a preserved artifact. This module owns that rule:

  * `EvidenceResolver.resolve(ref)` -> a `ResolvedEvidence` with existence + hash.
  * `verify_claims(claims)` -> lists the claim indices whose evidence did not all
    resolve. Callers must downgrade those claims to HYPOTHESIS (or drop them).

The resolver never writes to the evidence tree; it only reads and hashes. Absolute
paths and repository-escaping paths are rejected, so an untrusted trajectory cannot
point a claim at `/etc/passwd` or `../../secret`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from dataforge_v3.intelligence.schema import EvidenceRef

# Artifacts whose content is mutable run output and therefore not authoritative
# for a verdict (see reports/EVIDENCE_INTEGRITY_NOTE.md). A claim may cite them as
# context, but the resolver flags them as non-authoritative.
NON_AUTHORITATIVE_SUFFIXES = ("job.log", "trial.log")

_CHUNK = 1 << 20


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(_CHUNK)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


@dataclass
class ResolvedEvidence:
    ref: EvidenceRef
    exists: bool
    sha256: str | None
    authoritative: bool
    error: str | None = None


def _is_within(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class EvidenceResolver:
    """Resolves evidence refs against a fixed repository root."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._hash_cache: dict[str, str] = {}

    def resolve(self, ref: EvidenceRef) -> ResolvedEvidence:
        raw = ref.artifact.replace("\\", "/")
        if not raw or raw.startswith("/") or raw.startswith("~") or ".." in raw.split("/"):
            return ResolvedEvidence(ref, False, None, False, "unsafe artifact path")
        path = (self.root / raw).resolve()
        if not _is_within(self.root, path):
            return ResolvedEvidence(ref, False, None, False, "path escapes repository root")
        if not path.exists() or not path.is_file():
            return ResolvedEvidence(ref, False, None, False, "artifact not found")
        authoritative = not raw.endswith(NON_AUTHORITATIVE_SUFFIXES)
        key = str(path)
        if key not in self._hash_cache:
            self._hash_cache[key] = sha256_file(path)
        return ResolvedEvidence(ref, True, self._hash_cache[key], authoritative)

    def all_resolve(self, refs: list[EvidenceRef]) -> tuple[bool, bool]:
        """Return (all_exist, all_authoritative)."""
        results = [self.resolve(r) for r in refs]
        return (
            bool(results) and all(r.exists for r in results),
            all(r.authoritative for r in results),
        )
