"""Run the DataForge V3.3 engine over the frozen 30-case cohort.

Offline only: no model calls, no Docker. Captures the structured diagnosis,
resolves evidence, and records latency and peak memory per case. The results are
written under `raw_outputs/` and summarised in the requested score file
(`original_scores.json` on the first labelled run, etc.).

Usage:
    python experiments/thirty_case_validation/run_cases.py --label original
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dataforge_v3.intelligence.case_adapter import (  # noqa: E402
    _case_allowed_roots,
    diagnose_manifest,
    load_case_manifest,
)
from dataforge_v3.intelligence.evidence import EvidenceResolver  # noqa: E402
from dataforge_v3.intelligence.reporting import (  # noqa: E402
    render_diagnosis_json,
    render_diagnosis_markdown,
)

COHORT = ROOT / "experiments" / "thirty_case_validation"
CASES_DIR = COHORT / "cases"


def case_ids() -> list[str]:
    return sorted(p.name for p in CASES_DIR.iterdir() if p.is_dir())


def run_once(manifest_path: Path):
    tracemalloc.start()
    t0 = time.perf_counter()
    diagnosis, _semantic, _obs = diagnose_manifest(ROOT, manifest_path)
    elapsed = time.perf_counter() - t0
    _cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return diagnosis, elapsed, peak


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="original")
    args = ap.parse_args()

    out_dir = COHORT / "raw_outputs" / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    scores = {}
    for case_id in case_ids():
        manifest_path = CASES_DIR / case_id / "manifest.json"
        m = load_case_manifest(manifest_path)
        resolver = EvidenceResolver(ROOT, allowed_roots=_case_allowed_roots(ROOT, manifest_path, m))

        diag, cold_s, cold_peak = run_once(manifest_path)
        warm = sorted(run_once(manifest_path)[1] for _ in range(5))
        median_warm = warm[len(warm) // 2]

        payload = render_diagnosis_json(diag, resolver)
        (out_dir / f"{case_id}.diagnosis.json").write_text(payload, encoding="utf-8")
        (out_dir / f"{case_id}.diagnosis.md").write_text(
            render_diagnosis_markdown(diag, resolver), encoding="utf-8")

        authored = [f for f in diag.findings if f.kind.value != "hypothesis"]
        unresolved = [f.id for f in diag.findings if not resolver.all_resolve(f.evidence)[0]]
        scores[case_id] = {
            "execution_validity": diag.execution_validity,
            "semantic_verdict": diag.semantic_verdict,
            "original_score": diag.original_score,
            "n_findings": len(diag.findings),
            "authored_findings": [
                {"id": f.id, "category": f.category.value,
                 "violated_requirement": f.violated_requirement,
                 "severity": f.severity.value, "kind": f.kind.value,
                 "n_evidence": len(f.evidence)} for f in authored],
            "hypothesis_findings": [f.id for f in diag.findings if f.kind.value == "hypothesis"],
            "n_strengths": len(diag.strengths),
            "strengths": [s.text for s in diag.strengths],
            "weakness_dims": sorted({c["dimension"] for c in diag.capabilities if c.get("weakness_tasks")}),
            "n_recommendations": len(diag.recommendations),
            "unresolved_evidence_findings": unresolved,
            "cold_seconds": cold_s,
            "warm_seconds_samples": warm,
            "warm_median_seconds": median_warm,
            "cold_peak_bytes": cold_peak,
        }

    (COHORT / f"{args.label}_scores.json").write_text(
        json.dumps(scores, indent=2, sort_keys=True), encoding="utf-8")
    n_find = sum(v["n_findings"] for v in scores.values())
    print(f"{args.label}: {len(scores)} cases, {n_find} total findings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
