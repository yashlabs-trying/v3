"""Score the six-case diagnostic outputs against the frozen answer key.

Reads ground_truth.json (frozen before diagnosis) and raw_outputs/run_summary.json
(engine output) and produces comparison.json + metrics.json. It does not modify
either input and never re-runs the engine.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "six_case_validation"


def main() -> int:
    gt = json.loads((EXP / "ground_truth.json").read_text(encoding="utf-8"))["cases"]
    run = json.loads((EXP / "raw_outputs" / "run_summary.json").read_text(encoding="utf-8"))

    rows = []
    for case_id, key in gt.items():
        r = run[case_id]
        authored = r["authored_findings"]
        coding_authored = [
            f for f in authored
            if f["violated_requirement"] is not None
        ]
        infra_only = all(f["category"] == "agent_startup_failure" for f in authored) and bool(authored)

        if key["expected_attribution"] == "coding_failure":
            expected_set = set(key.get("expected_violated_clauses_all") or [key["expected_violated_clause"]])
            matched = [
                f for f in authored
                if f["violated_requirement"] in expected_set
                and f["category"] == key["expected_category"]
            ]
            # contradiction = an authoritative coding finding on a clause the
            # independent evidence did NOT record as failing.
            contradictory = [
                f for f in coding_authored
                if f["violated_requirement"] not in expected_set
            ]
            # The engine must surface every independently-failing clause.
            surfaced = {f["violated_requirement"] for f in matched}
            attribution_correct = bool(matched) and not contradictory and surfaced == expected_set
        elif key["expected_attribution"] == "infrastructure_only":
            attribution_correct = infra_only and key["expected_no_coding_accusation"] and not coding_authored
        elif key["expected_attribution"] == "none":
            attribution_correct = len(coding_authored) == 0 and not r["weakness_dims"]
        else:
            attribution_correct = False

        evidence_valid = len(r["unresolved_evidence_findings"]) == 0
        rows.append({
            "case_id": case_id,
            "origin": key["origin"],
            "expected_attribution": key["expected_attribution"],
            "expected_clause": key["expected_violated_clause"],
            "engine_validity": r["execution_validity"],
            "engine_semantic_verdict": r["semantic_verdict"],
            "engine_authored_findings": [
                {"clause": f["violated_requirement"], "category": f["category"]} for f in authored
            ],
            "engine_strengths": r["strengths"],
            "engine_recommendations": r["n_recommendations"],
            "attribution_correct": bool(attribution_correct),
            "evidence_valid": bool(evidence_valid),
            "unresolved_evidence": r["unresolved_evidence_findings"],
            "median_latency_ms": round(r["warm_median_seconds"] * 1000, 2),
            "cold_latency_ms": round(r["cold_seconds"] * 1000, 2),
            "cold_peak_bytes": r["cold_peak_bytes"],
        })

    scoring = {
        "attribution_correct": sum(1 for r in rows if r["attribution_correct"]),
        "attribution_total": len(rows),
        "evidence_valid": sum(1 for r in rows if r["evidence_valid"]),
        "evidence_total": len(rows),
        "coding_failure_cases": sum(1 for r in rows if r["expected_attribution"] == "coding_failure"),
        "coding_failure_correct": sum(
            1 for r in rows
            if r["expected_attribution"] == "coding_failure" and r["attribution_correct"]
        ),
        "infra_correct": sum(
            1 for r in rows
            if r["expected_attribution"] == "infrastructure_only" and r["attribution_correct"]
        ),
        "correct_solution_no_fabrication": sum(
            1 for r in rows
            if r["expected_attribution"] == "none" and r["attribution_correct"]
        ),
    }

    comparison = {"answer_key_frozen": True, "rows": rows, "scoring": scoring}
    (EXP / "comparison.json").write_text(json.dumps(comparison, indent=2, sort_keys=True), encoding="utf-8")

    lat = sorted(r["median_latency_ms"] for r in rows)
    peak = sorted(r["cold_peak_bytes"] for r in rows)

    def _by(origin, pred):
        sel = [r for r in rows if r["origin"] == origin and pred(r)]
        return f"{sum(1 for r in sel if r['attribution_correct'])}/{len(sel)}"

    metrics = {
        "n_cases": len(rows),
        "attribution_accuracy": {
            "correct": scoring["attribution_correct"],
            "total": scoring["attribution_total"],
            "coding_failure_cases_correct": f"{scoring['coding_failure_correct']}/{scoring['coding_failure_cases']}",
            "failures_by_origin": {
                "REUSED": _by("REUSED", lambda r: r["expected_attribution"] == "coding_failure"),
                "SYNTHETIC": _by("SYNTHETIC", lambda r: r["expected_attribution"] == "coding_failure"),
            },
            "authentic_reused_coding_failures_correct": _by(
                "REUSED", lambda r: r["expected_attribution"] == "coding_failure"
            ),
            "synthetic_controlled_defects_correct": _by(
                "SYNTHETIC", lambda r: r["expected_attribution"] == "coding_failure"
            ),
        },
        "evidence_integrity": {
            "all_refs_resolved": scoring["evidence_valid"] == scoring["evidence_total"],
            "unresolved_total": sum(len(r["unresolved_evidence"]) for r in rows),
        },
        "latency_ms": {
            "method": "warm median of 5 runs after 1 cold run per case; offline, no model calls",
            "samples": lat,
            "min": lat[0],
            "median": lat[len(lat) // 2],
            "max": lat[-1],
        },
        "memory": {
            "method": "tracemalloc peak during a cold diagnosis per case (diagnosis-only, excludes interpreter baseline)",
            "cold_peak_bytes_samples": peak,
            "max_cold_peak_bytes": peak[-1],
        },
    }
    (EXP / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")

    for r in rows:
        print(
            f"{r['case_id']:26s} origin={r['origin']:9s} correct={str(r['attribution_correct']):5s} "
            f"evidence_ok={str(r['evidence_valid']):5s} median={r['median_latency_ms']:.1f}ms"
        )
    print(f"\nattribution {scoring['attribution_correct']}/{scoring['attribution_total']} | "
          f"coding-failure {scoring['coding_failure_correct']}/{scoring['coding_failure_cases']} | "
          f"evidence {scoring['evidence_valid']}/{scoring['evidence_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
