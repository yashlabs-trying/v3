"""Component E — evidence-backed reporting (V3.3).

Renders a `Diagnosis` to JSON and Markdown. Rules enforced here:

  * A claim is only rendered as authoritative if `EvidenceResolver` confirms its
    evidence resolves; otherwise it is downgraded to HYPOTHESIS in the text.
  * Infrastructure/invalid runs are never described as coding weaknesses.
  * No marketing language; the summary states what was and was not verified.
"""

from __future__ import annotations

import json
from pathlib import Path

from dataforge_v3.intelligence.evidence import EvidenceResolver
from dataforge_v3.intelligence.schema import ClaimKind, Diagnosis


def _claim_authoritative(claim, resolver: EvidenceResolver) -> tuple[bool, list[str]]:
    refs = getattr(claim, "evidence", [])
    if not refs:
        return False, ["no evidence reference"]
    ok, _auth = resolver.all_resolve(refs)
    missing = [r.artifact for r in refs if not resolver.resolve(r).exists]
    return ok, missing


def render_diagnosis_markdown(d: Diagnosis, resolver: EvidenceResolver) -> str:
    L: list[str] = []
    L.append(f"# DataForge V3.3 diagnosis — {d.task_id}")
    L.append("")
    L.append(f"- **Attempt:** `{d.attempt}`")
    L.append(f"- **Execution validity (V3.1):** {d.execution_validity}")
    L.append(f"- **Semantic verdict (V3.2):** {d.semantic_verdict}")
    L.append(f"- **Original V2 score:** {d.original_score}")
    if d.runtime_seconds is not None:
        L.append(f"- **Analysis runtime:** {d.runtime_seconds:.3f}s")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(d.summary)
    L.append("")

    L.append("## Verified strengths")
    L.append("")
    if d.strengths:
        for s in d.strengths:
            auth, missing = _claim_authoritative(s, resolver)
            tag = s.kind.value if auth or not s.evidence else "HYPOTHESIS"
            L.append(f"- **[{tag}]** {s.text}")
            _emit_refs(L, s.evidence, resolver)
    else:
        L.append("- None independently demonstrated for this attempt.")
    L.append("")

    L.append("## Verified failures")
    L.append("")
    if d.findings:
        for f in d.findings:
            auth, missing = _claim_authoritative(f, resolver)
            tag = f.kind.value if auth else "HYPOTHESIS"
            L.append(f"### {f.id}")
            L.append(f"- **Category:** {f.category.value} | **Severity:** {f.severity.value} | **Kind:** {tag}")
            L.append(f"- **Observed symptom:** {f.symptom}")
            if f.violated_requirement:
                L.append(f"- **Violated contract clause:** `{f.violated_requirement}`")
            if f.competing_explanations:
                L.append(f"- **Competing explanations:** {'; '.join(f.competing_explanations)}")
            if f.limitations:
                L.append(f"- **Limitations:** {'; '.join(f.limitations)}")
            _emit_refs(L, f.evidence, resolver)
            L.append("")
    else:
        L.append("- No verified failure finding for this attempt.")
    L.append("")

    L.append("## Capability observations")
    L.append("")
    if d.capabilities:
        for c in d.capabilities:
            L.append(
                f"- **{c['dimension']}** — observations={c['observations']}, "
                f"n_tasks={c['n_tasks']} "
                f"(strengths: {', '.join(c.get('strength_tasks', [])) or 'none'}; "
                f"weaknesses: {', '.join(c.get('weakness_tasks', [])) or 'none'}) — "
                f"{c['sample_note']}"
            )
    else:
        L.append("- None.")
    L.append("")

    L.append("## Recommended experiments")
    L.append("")
    if d.recommendations:
        for r in d.recommendations:
            L.append(f"### {r['id']}")
            L.append(f"- **Addresses finding:** `{r['finding_id']}`")
            L.append(f"- **Hypothesis:** {r['hypothesis']}")
            L.append(f"- **Intervention:** {r['intervention']}")
            L.append(f"- **Control:** {r['control']}")
            L.append(f"- **Metric:** {r['metric']}")
            L.append(f"- **Cost estimate:** {r['cost_estimate']}")
            status = "EXECUTED" if r["executed"] else "NOT_EXECUTED"
            if r.get("execution_note"):
                L.append(f"- **Status:** {status} — {r['execution_note']}")
            else:
                L.append(f"- **Status:** {status}")
            L.append("")
    else:
        L.append("- None.")
    L.append("")

    L.append("## Uncertainty and limitations")
    L.append("")
    for u in d.uncertainty:
        L.append(f"- {u}")
    L.append("")
    return "\n".join(L)


def _emit_refs(L: list[str], refs, resolver: EvidenceResolver) -> None:
    for r in refs:
        res = resolver.resolve(r)
        status = "resolved" if res.exists else f"UNRESOLVED ({res.error})"
        auth = "authoritative" if res.authoritative else "non-authoritative"
        L.append(f"  - evidence: `{r.artifact}` [{r.locator}] — {status}, {auth}")


def render_diagnosis_json(d: Diagnosis, resolver: EvidenceResolver) -> str:
    payload = d.to_dict()
    payload["evidence_resolution"] = _resolution_report(d, resolver)
    return json.dumps(payload, indent=2, sort_keys=True)


def _resolution_report(d: Diagnosis, resolver: EvidenceResolver) -> dict:
    seen: dict[str, dict] = {}
    all_refs = []
    for f in d.findings:
        all_refs.extend(f.evidence)
    for s in d.strengths:
        all_refs.extend(s.evidence)
    for r in d.recommendations:
        for e in r.get("evidence", []):
            from dataforge_v3.intelligence.schema import EvidenceRef

            all_refs.append(EvidenceRef(**e) if isinstance(e, dict) else e)
    unresolved = 0
    for ref in all_refs:
        res = resolver.resolve(ref)
        seen[ref.artifact] = {
            "exists": res.exists,
            "sha256": res.sha256,
            "authoritative": res.authoritative,
            "error": res.error,
        }
        if not res.exists:
            unresolved += 1
    return {
        "artifacts": seen,
        "n_references": len(all_refs),
        "n_unresolved": unresolved,
        "all_resolved": unresolved == 0,
    }


def write_diagnosis(d: Diagnosis, resolver: EvidenceResolver, out_dir: Path, stem: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(render_diagnosis_json(d, resolver), encoding="utf-8")
    md_path.write_text(render_diagnosis_markdown(d, resolver), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}
