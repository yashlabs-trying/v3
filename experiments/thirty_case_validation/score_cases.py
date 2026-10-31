"""Score a 30-case run against the frozen answer key.

Usage:
    python experiments/thirty_case_validation/score_cases.py --label original
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COHORT = ROOT / "experiments" / "thirty_case_validation"


def score(label: str) -> dict:
    gt = json.loads((COHORT / "ground_truth.json").read_text(encoding="utf-8"))["cases"]
    run = json.loads((COHORT / f"{label}_scores.json").read_text(encoding="utf-8"))

    rows = []
    for cid, key in gt.items():
        r = run[cid]
        authored = r["authored_findings"]
        coding = [f for f in authored if f["violated_requirement"] is not None]
        infra_only = bool(authored) and all(f["category"] == "agent_startup_failure" for f in authored)

        exp = key["expected_attribution"]
        if exp == "coding_failure":
            expected_by_clause = key.get("expected_category_by_clause") or {}
            expected_clauses = set(key.get("expected_clauses") or key.get("expected_clauses_any_failing") or [])
            matched = {f["violated_requirement"]: f["category"] for f in coding}
            clause_match = expected_clauses <= set(matched)
            if expected_by_clause:
                if key.get("category_refinement_depends_on_patch"):
                    # An INVARIANT-regression clause may be reported as
                    # existing_behavior_removed (diff corroborated) or, by the
                    # engine's documented conservative fallback, as
                    # requirement_omitted. Both are accepted; the clause is the
                    # independently established fact.
                    def _ok(c):
                        exp = expected_by_clause.get(c)
                        got = matched.get(c)
                        return got == exp or (exp == "existing_behavior_removed"
                                              and got == "requirement_omitted")
                    category_match = all(_ok(c) for c in expected_clauses)
                else:
                    category_match = all(matched.get(c) == expected_by_clause.get(c)
                                         for c in expected_clauses)
            else:
                category_match = True
            extra = [c for c in matched if c not in expected_clauses]
            forged_ok = True
            if key.get("expected_forged_log_rejected"):
                forged_ok = (r["n_strengths"] == 0)
            correct = clause_match and category_match and not extra and forged_ok
        elif exp == "infrastructure_only":
            correct = infra_only and not coding
        elif exp == "none":
            correct = len(coding) == 0 and not r["weakness_dims"]
        elif exp == "abstain_or_downgrade":
            # correct if the engine did not emit an authoritative coding finding
            # on this ambiguous case (downgrade/hypothesis/abstain all acceptable)
            correct = len(coding) == 0
        else:
            correct = False

        rows.append({
            "case_id": cid,
            "category": key["category"],
            "origin": key["origin"],
            "expected": exp,
            "engine_authored": [{"clause": f["violated_requirement"], "category": f["category"]} for f in authored],
            "engine_hypothesis": r["hypothesis_findings"],
            "engine_validity": r["execution_validity"],
            "correct": bool(correct),
            "evidence_valid": len(r["unresolved_evidence_findings"]) == 0,
            "unresolved": r["unresolved_evidence_findings"],
            "median_latency_ms": round(r["warm_median_seconds"] * 1000, 3),
            "cold_latency_ms": round(r["cold_seconds"] * 1000, 3),
            "cold_peak_bytes": r["cold_peak_bytes"],
            "n_recommendations": r["n_recommendations"],
        })

    by_cat = Counter(r["category"] for r in rows)
    cat_correct = Counter(r["category"] for r in rows if r["correct"])
    summary = {
        "total": len(rows),
        "correct": sum(1 for r in rows if r["correct"]),
        "evidence_valid": sum(1 for r in rows if r["evidence_valid"]),
        "unresolved_refs_total": sum(len(r["unresolved"]) for r in rows),
        "by_category": {c: {"total": by_cat[c], "correct": cat_correct[c]} for c in sorted(by_cat)},
        "false_accusations_on_correct": sum(
            1 for r in rows if r["category"] == "correct_solution" and not r["correct"]),
        "infra_to_model_confusions": sum(
            1 for r in rows if r["category"] == "infrastructure_invalid" and not r["correct"]),
    }
    return {"label": label, "rows": rows, "summary": summary}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="original")
    args = ap.parse_args()
    result = score(args.label)
    (COHORT / f"{args.label}_comparison.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    s = result["summary"]
    for r in result["rows"]:
        mark = "OK " if r["correct"] else "XX "
        print(f"[{mark}] {r['case_id']:28s} {r['category']:22s} {r['origin']:9s} "
              f"authored={len(r['engine_authored'])} hyp={len(r['engine_hypothesis'])} "
              f"ev_ok={r['evidence_valid']}")
    print(f"\n{args.label}: correct {s['correct']}/{s['total']} | evidence {s['evidence_valid']}/{s['total']} "
          f"| unresolved {s['unresolved_refs_total']} | false-acc on correct {s['false_accusations_on_correct']} "
          f"| infra->model {s['infra_to_model_confusions']}")
    print("by category:", json.dumps(s["by_category"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
