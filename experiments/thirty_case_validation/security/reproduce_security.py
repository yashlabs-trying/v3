"""Evidence-path containment: reproduce the pre-fix weakness and verify the fix.

This script is intentionally independent of the fix's implementation details:
it exercises `EvidenceResolver.resolve` over a fixed battery of refs and prints
an EXISTS/AUTHORITATIVE/ERROR row for each. Run before the fix to capture the
pre-fix behaviour and after the fix to capture the post-fix behaviour.

Usage:
    python experiments/thirty_case_validation/security/reproduce_security.py [--root .]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from dataforge_v3.intelligence.evidence import EvidenceResolver  # noqa: E402
from dataforge_v3.intelligence.schema import EvidenceRef  # noqa: E402


def battery(repo_root: Path) -> list[tuple[str, str, str]]:
    """(name, artifact, expectation) — expectation is 'trusted' or 'rejected'."""
    r = repo_root
    return [
        # Absolute paths are rejected by the documented contract (see module
        # docstring). A caller must cite evidence by a root-relative path.
        ("absolute inside root (real file)", str(r / "findings" / "vuls_semantic_evidence.json"), "rejected"),
        ("absolute outside root", "C:/Windows/System32/drivers/etc/hosts", "rejected"),
        ("dotdot traversal", "findings/../../Windows/System32/drivers/etc/hosts", "rejected"),
        ("dotdot in middle", "jobs/../../secret.txt", "rejected"),
        ("posix absolute", "/etc/passwd", "rejected"),
        ("tilde", "~/secret.txt", "rejected"),
        ("relative inside approved evidence root", "findings/vuls_semantic_evidence.json", "trusted"),
        ("repo file outside evidence roots (.git)", ".git/config", "rejected"),
        ("answer key inside repo", "experiments/six_case_validation/ground_truth.json", "rejected"),
        ("nonexistent inside root", "findings/does_not_exist.json", "rejected"),
        ("empty path", "", "rejected"),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo_root = Path(args.root).resolve()
    resolver = EvidenceResolver(repo_root)
    rows = []
    for name, art, expectation in battery(repo_root):
        res = resolver.resolve(EvidenceRef(art, "probe", name))
        passed = (res.exists and res.authoritative) if expectation == "trusted" else not res.exists
        rows.append({
            "name": name,
            "artifact": art,
            "expectation": expectation,
            "exists": res.exists,
            "authoritative": res.authoritative,
            "error": res.error,
            "ok": passed,
        })
        print(f"[{'OK ' if passed else 'XX '}] {name:42s} exists={res.exists!s:5s} auth={res.authoritative!s:5s} err={res.error}")

    n_ok = sum(1 for r in rows if r["ok"])
    print(f"\n{args.label}: {n_ok}/{len(rows)} expectations met")
    if args.out:
        Path(args.out).write_text(json.dumps({"label": args.label, "rows": rows}, indent=2), encoding="utf-8")
    return 0 if n_ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
