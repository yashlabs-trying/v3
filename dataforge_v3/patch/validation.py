"""Structural parsing and validation of unified git patches (fail-closed)."""

from __future__ import annotations

import hashlib
import posixpath
import re
from dataclasses import dataclass, field
from typing import Any

_DIFF_RE = re.compile(r"^diff --git (?P<rest>.+)$")
_SYMLINK_MODE = "120000"
_GITLINK_MODE = "160000"


@dataclass
class PatchEntry:
    index: int
    raw: str
    old_path: str | None
    new_path: str | None
    is_new: bool = False
    is_delete: bool = False
    is_rename: bool = False
    is_binary: bool = False
    mode: str | None = None
    header_issues: list[str] = field(default_factory=list)

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or ""


@dataclass
class PatchAnalysis:
    raw: str
    sha256: str
    size_bytes: int
    entries: list[PatchEntry]
    issues: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.size_bytes == 0

    @property
    def valid_structure(self) -> bool:
        return not self.issues


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def normalize_newlines(text: str) -> str:
    """Canonicalize patch line endings so CRLF checkouts hash and apply identically."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


@dataclass
class PatchIdentity:
    text: str
    raw_sha256: str
    lf_sha256: str
    canonical_sha256: str
    eol: str


def patch_identity(raw: bytes) -> PatchIdentity:
    """Canonical patch identity across LF sources and CRLF checkouts.

    A file whose newlines are *all* CRLF is a checkout-encoded LF patch, so its
    LF form is authoritative. Mixed content (for example Redis AOF lines that
    genuinely end in CRLF) must keep its raw bytes authoritative.
    """
    text = raw.decode("utf-8", errors="surrogateescape")
    lf_text = normalize_newlines(text)
    raw_sha = sha256_bytes(raw)
    lf_sha = sha256_text(lf_text)
    pure_crlf = b"\r\n" in raw and raw.count(b"\r\n") == raw.count(b"\n")
    if pure_crlf:
        eol = "crlf"
    elif b"\r\n" in raw:
        eol = "mixed"
    else:
        eol = "lf"
    return PatchIdentity(
        text=lf_text,
        raw_sha256=raw_sha,
        lf_sha256=lf_sha,
        canonical_sha256=lf_sha if pure_crlf else raw_sha,
        eol=eol,
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unquote_git_path(value: str) -> str:
    value = value.strip()
    if not (len(value) >= 2 and value[0] == '"' and value[-1] == '"'):
        return value
    body = value[1:-1]
    out = bytearray()
    i = 0
    while i < len(body):
        c = body[i]
        if c != "\\":
            out.extend(c.encode("utf-8"))
            i += 1
            continue
        if i + 1 >= len(body):
            out.extend(b"\\")
            break
        n = body[i + 1]
        simple = {"n": b"\n", "t": b"\t", "r": b"\r", '"': b'"', "\\": b"\\", "a": b"\a", "b": b"\b", "f": b"\f", "v": b"\v"}
        if n in simple:
            out.extend(simple[n])
            i += 2
        elif n in "01234567":
            j = i + 1
            digits = ""
            while j < len(body) and len(digits) < 3 and body[j] in "01234567":
                digits += body[j]
                j += 1
            out.append(int(digits, 8) & 0xFF)
            i = j
        else:
            out.extend(n.encode("utf-8"))
            i += 2
    return out.decode("utf-8", errors="replace")


def _strip_prefix(value: str) -> str | None:
    value = _unquote_git_path(value)
    if value == "/dev/null":
        return None
    if value.startswith("a/") or value.startswith("b/"):
        return value[2:]
    return value


def _parse_diff_header_paths(rest: str) -> tuple[str | None, str | None]:
    rest = rest.strip()
    if rest.startswith('"'):
        m = re.match(r'^("(?:\\.|[^"\\])*")\s+("(?:\\.|[^"\\])*")$', rest)
        if m:
            return _strip_prefix(m.group(1)), _strip_prefix(m.group(2))
    if " b/" in rest:
        idx = rest.rfind(" b/")
        left, right = rest[:idx], rest[idx + 1:]
        return _strip_prefix(left), _strip_prefix(right)
    parts = rest.split(" ")
    if len(parts) == 2:
        return _strip_prefix(parts[0]), _strip_prefix(parts[1])
    return None, None


def parse_patch(text: str) -> PatchAnalysis:
    text = normalize_newlines(text)
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith("diff --git ")]
    entries: list[PatchEntry] = []
    issues: list[str] = []
    preamble = "".join(lines[: starts[0]]) if starts else text
    if preamble.strip():
        issues.append("patch has content before the first diff header")

    bounds = starts + [len(lines)]
    for n, start in enumerate(starts):
        raw = "".join(lines[start : bounds[n + 1]])
        header = lines[start].rstrip("\r\n")
        m = _DIFF_RE.match(header)
        old_p, new_p = (None, None)
        if m:
            old_p, new_p = _parse_diff_header_paths(m.group("rest"))
        entry = PatchEntry(index=n, raw=raw, old_path=old_p, new_path=new_p)
        mode = None
        rename_from = rename_to = None
        has_minus = has_plus = False
        for line in raw.splitlines():
            if line.startswith("new file mode "):
                entry.is_new = True
                mode = line.split()[-1]
            elif line.startswith("deleted file mode "):
                entry.is_delete = True
                mode = line.split()[-1]
            elif line.startswith("rename from "):
                entry.is_rename = True
                rename_from = _unquote_git_path(line[len("rename from ") :])
            elif line.startswith("rename to "):
                entry.is_rename = True
                rename_to = _unquote_git_path(line[len("rename to ") :])
            elif line.startswith("--- "):
                has_minus = True
                minus = _strip_prefix(line[4:])
                if minus is None:
                    entry.is_new = True
                elif old_p is None:
                    old_p = minus
            elif line.startswith("+++ "):
                has_plus = True
                plus = _strip_prefix(line[4:])
                if plus is None:
                    entry.is_delete = True
                elif new_p is None:
                    new_p = plus
            elif line.startswith("Binary files ") and line.rstrip().endswith(" differ"):
                entry.is_binary = True
            elif line.startswith("GIT binary patch"):
                entry.is_binary = True
        if rename_from:
            old_p = rename_from
        if rename_to:
            new_p = rename_to
        entry.old_path, entry.new_path, entry.mode = old_p, new_p, mode
        if not entry.old_path and not entry.new_path:
            issues.append(f"entry {n}: cannot determine patch paths")
        if not (has_minus and has_plus) and not entry.is_rename and not entry.is_binary:
            issues.append(f"entry {n}: missing ---/+++ file headers")
        entries.append(entry)

    if starts and not entries:
        issues.append("no diff entries parsed")

    analysis = PatchAnalysis(
        raw=text,
        sha256=sha256_text(text),
        size_bytes=len(text.encode("utf-8", errors="surrogateescape")),
        entries=entries,
        issues=issues,
    )
    analysis.issues.extend(validate_entries(analysis.entries))
    return analysis


def _check_path(path: str) -> list[str]:
    problems: list[str] = []
    if not path:
        return ["empty path"]
    if "\x00" in path:
        problems.append("NUL byte in path")
    if "\n" in path or "\r" in path:
        problems.append("newline in path")
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        problems.append(f"absolute path: {path}")
    if "\\" in path:
        problems.append(f"backslash in path: {path}")
    segments = path.split("/")
    if any(seg == ".." for seg in segments):
        problems.append(f"path escapes repository: {path}")
    if any(seg == ".git" for seg in segments):
        problems.append(f"path targets git metadata: {path}")
    normalized = posixpath.normpath(path)
    if normalized != path:
        problems.append(f"non-canonical path: {path} -> {normalized}")
    return problems


def validate_entries(entries: list[PatchEntry]) -> list[str]:
    issues: list[str] = []
    seen: dict[str, int] = {}
    for e in entries:
        for p in (e.old_path, e.new_path):
            if p:
                for problem in _check_path(p):
                    issues.append(f"entry {e.index}: {problem}")
        if e.mode == _SYMLINK_MODE:
            issues.append(f"entry {e.index}: symlink entry rejected ({e.path})")
        if e.mode == _GITLINK_MODE:
            issues.append(f"entry {e.index}: submodule/gitlink entry rejected ({e.path})")
        key = e.path
        if key in seen:
            issues.append(f"entry {e.index}: duplicate path {key} (also entry {seen[key]})")
        else:
            seen[key] = e.index
    return issues


def validate_patch_text(text: str) -> tuple[bool, list[str]]:
    analysis = parse_patch(text)
    return analysis.valid_structure, analysis.issues


def patch_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
