"""Six-case validation runner (offline, no model calls, no Docker).

For each case manifest it runs the existing DataForge V3.3 engine via the
`diagnose_manifest` adapter, captures the structured output, validates every
evidence reference, and records latency + peak memory. Nothing here changes the
engine; it only drives it and records what it produced.

Usage: python experiments/six_case_validation/run_cases.py
"""

from __future__ import annotations

import json
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys

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

CASES = [
    "c1_vuls",
    "c2_teleport_synthetic",
    "c3_elementweb_synthetic",
    "c4_openlibrary",
    "c5_infra",
    "c6_adversarial",
]


def run_once(manifest_path: Path):
    tracemalloc.start()
    t0 = time.perf_counter()
    diagnosis, _semantic, _obs = diagnose_manifest(ROOT, manifest_path)
    elapsed = time.perf_counter() - t0
    _cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return diagnosis, elapsed, peak


def main() -> int:
    out_dir = ROOT / "experiments" / "six_case_validation" / "raw_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}

    for case in CASES:
        manifest = ROOT / "experiments" / "six_case_validation" / "cases" / case / "manifest.json"
        _m = load_case_manifest(manifest)
        resolver = EvidenceResolver(ROOT, allowed_roots=_case_allowed_roots(ROOT, manifest, _m))

        # 1 cold run (fresh reads) + 5 warm runs for latency
        diag_cold, cold_s, cold_peak = run_once(manifest)
        warm = []
        for _ in range(5):
            d, s, _p = run_once(manifest)
            warm.append(s)
        warm.sort()
        median_warm = warm[len(warm) // 2]

        # structured output
        payload = render_diagnosis_json(diag_cold, resolver)
        (out_dir / f"{case}.diagnosis.json").write_text(payload, encoding="utf-8")
        (out_dir / f"{case}.diagnosis.md").write_text(
            render_diagnosis_markdown(diag_cold, resolver), encoding="utf-8"
        )

        d = diag_cold
        authored = [f for f in d.findings if f.kind.value != "hypothesis"]
        hyp = [f for f in d.findings if f.kind.value == "hypothesis"]
        unresolved = []
        for f in d.findings:
            ok, _ = resolver.all_resolve(f.evidence)
            if not ok:
                unresolved.append(f.id)
        summary[case] = {
            "task_id": d.task_id,
            "execution_validity": d.execution_validity,
            "semantic_verdict": d.semantic_verdict,
            "original_score": d.original_score,
            "n_findings": len(d.findings),
            "authored_findings": [
                {
                    "id": f.id,
                    "category": f.category.value,
                    "violated_requirement": f.violated_requirement,
                    "severity": f.severity.value,
                    "kind": f.kind.value,
                    "n_evidence": len(f.evidence),
                }
                for f in authored
            ],
            "hypothesis_findings": [f.id for f in hyp],
            "n_strengths": len(d.strengths),
            "strengths": [s.text for s in d.strengths],
            "n_capabilities": len(d.capabilities),
            "weakness_dims": sorted(
                {c["dimension"] for c in d.capabilities if c.get("weakness_tasks")}
            ),
            "n_recommendations": len(d.recommendations),
            "unresolved_evidence_findings": unresolved,
            "cold_seconds": cold_s,
            "warm_seconds_samples": warm,
            "warm_median_seconds": median_warm,
            "cold_peak_bytes": cold_peak,
        }
        print(
            f"{case:26s} validity={d.execution_validity:8s} findings={len(d.findings)} "
            f"authored={len(authored)} strengths={len(d.strengths)} "
            f"cold={cold_s*1000:.1f}ms warm_med={median_warm*1000:.1f}ms"
        )

    (out_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
