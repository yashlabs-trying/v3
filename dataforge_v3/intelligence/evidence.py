"""V3.3 — evidence resolution and verification.

A `DiagnosticClaim` or `Finding` may only be authoritative if every `EvidenceRef`
resolves to a preserved artifact. This module owns that rule:

  * `EvidenceResolver.resolve(ref)` -> a `ResolvedEvidence` with existence + hash.
  * `verify_claims(claims)` -> lists the claim indices whose evidence did not all
    resolve. Callers must downgrade those claims to HYPOTHESIS (or drop them).

The resolver never writes to the evidence tree; it only reads and hashes. Absolute
paths, repository-escaping paths and paths outside the approved evidence roots are
rejected, so an untrusted trajectory cannot point a claim at `/etc/passwd`,
`../../secret`, `C:/Windows/...`, `.git/config` or a frozen answer key.

Containment model: resolution is limited to a set of **approved evidence roots**
under the repository root (default: `jobs/` and `findings/`, the two directories
that hold recorded runs and frozen research evidence). Symlinks are resolved before
the containment check, so a symlink that points outside an approved root is
rejected. Callers that carry evidence elsewhere (for example the controlled-case
adapter, whose synthetic inputs live under `experiments/`) pass an explicit
`allowed_roots` list; those roots are still required to sit inside the repository
root.
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

# Directories (relative to the repository root) that may hold authoritative
# evidence. Everything else in the repository is off-limits to a bare ref, so an
# untrusted trajectory cannot cite `.git/config`, another case's answer key, or an
# arbitrary repository file as verification evidence.
DEFAULT_ALLOWED_ROOTS: tuple[str, ...] = ("jobs", "findings")

_CHUNK = 1 << 20


def _looks_absolute(raw: str) -> bool:
    """True for POSIX, Windows drive-letter and UNC absolute paths."""
    if not raw:
        return False
    if raw.startswith("/") or raw.startswith("~"):
        return True
    if raw.startswith("//"):  # UNC \\server\share (after backslash->slash)
        return True
    if len(raw) >= 2 and raw[1] == ":" and raw[0].isalpha():  # C:/..., C:...
        return True
    return False


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
    """Resolves evidence refs against a fixed repository root and approved roots."""

    def __init__(
        self,
        root: Path,
        allowed_roots: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        if allowed_roots is None:
            allowed_roots = DEFAULT_ALLOWED_ROOTS
        # Resolve each approved root to an absolute path and require it to sit
        # inside the repository root; a misconfigured approved root is dropped
        # rather than widening trust.
        resolved_roots: list[Path] = []
        for name in allowed_roots:
            cand = (self.root / name).resolve()
            if _is_within(self.root, cand):
                resolved_roots.append(cand)
        self._allowed_roots = resolved_roots
        self._hash_cache: dict[str, str] = {}

    def _in_allowed_root(self, path: Path) -> bool:
        return any(_is_within(ar, path) for ar in self._allowed_roots)

    def resolve(self, ref: EvidenceRef) -> ResolvedEvidence:
        raw = ref.artifact.replace("\\", "/")
        if not raw or _looks_absolute(raw) or ".." in raw.split("/"):
            return ResolvedEvidence(ref, False, None, False, "unsafe artifact path")
        path = (self.root / raw).resolve()
        if not _is_within(self.root, path):
            return ResolvedEvidence(ref, False, None, False, "path escapes repository root")
        if not self._in_allowed_root(path):
            return ResolvedEvidence(
                ref, False, None, False, "path outside approved evidence roots"
            )
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
