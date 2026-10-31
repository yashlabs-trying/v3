"""Generate evidence_manifest.json: hashes of every artifact each case cites."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COHORT = ROOT / "experiments" / "thirty_case_validation"
CASES = COHORT / "cases"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    man = {"note": "SHA-256 of every artifact referenced by the 30 case manifests.",
           "cases": {}}
    for cdir in sorted(p for p in CASES.iterdir() if p.is_dir()):
        m = json.loads((cdir / "manifest.json").read_text(encoding="utf-8"))
        entries = []
        for field in ("patch", "trajectory", "replay"):
            if m.get(field):
                p = ROOT / m[field]
                entries.append({"field": field, "path": m[field],
                                "sha256": sha256(p) if p.exists() else None})
        sem = m.get("semantic") or {}
        if sem.get("evidence_artifact"):
            p = ROOT / sem["evidence_artifact"]
            entries.append({"field": "semantic_evidence", "path": sem["evidence_artifact"],
                            "sha256": sha256(p) if p.exists() else None})
        for extra in ("source.py", "oracle.py", "probe_results.json", "trajectory.json",
                      "trusted_verifier.txt", "replay.json", "contradiction.txt", "run.log"):
            p = cdir / extra
            if p.exists():
                entries.append({"field": extra, "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                                "sha256": sha256(p)})
        man["cases"][cdir.name] = entries
    (COHORT / "evidence_manifest.json").write_text(json.dumps(man, indent=2, sort_keys=True), encoding="utf-8")
    n = sum(len(v) for v in man["cases"].values())
    print(f"evidence manifest: {len(man['cases'])} cases, {n} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
