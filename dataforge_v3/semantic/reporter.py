"""E. Independent Evidence Reporter (V3.2).

Renders a `SemanticAssessment` into a reviewer-facing artifact containing:
verdict, confidence, per-clause evidence, reproducible counterexamples, the
exact command to re-run the probe, and the unresolved limitations. The report
is intentionally conservative: it states what was executed and what remained
unproven.
"""

from __future__ import annotations

from dataforge_v3.semantic.model import (
    ProbeOutcome,
    SemanticAssessment,
    SemanticVerdict,
)


def render_assessment(a: SemanticAssessment, reproduce_command: str | None = None) -> str:
    lines: list[str] = []
    lines.append(f"# Semantic assessment — {a.task}")
    lines.append("")
    lines.append(f"- **Submission:** `{a.submission}`")
    lines.append(f"- **V2 reward:** {a.v2_reward}")
    lines.append(f"- **V3.1 classification:** {a.v3_1_classification}")
    lines.append(f"- **Semantic verdict:** **{a.verdict.value}**")
    lines.append(f"- **Confidence:** {a.confidence}")
    lines.append("")

    lines.append("## Contract coverage")
    lines.append("")
    lines.append("| Clause | Kind | Covered by official tests | Statement |")
    lines.append("|---|---|---|---|")
    covered = {e.clause_id for e in a.evidence}
    for c in a.clauses:
        cov = ", ".join(c.tested_by_original) if c.tested_by_original else "—"
        lines.append(f"| {c.id} | {c.kind.value} | {cov} | {c.statement} |")
    lines.append("")

    lines.append("## Probe evidence")
    lines.append("")
    if not a.probes:
        lines.append("_No executable probes were run._")
    else:
        lines.append("| Probe | Kind | Clauses | Result | Detail |")
        lines.append("|---|---|---|---|---|")
        for p in a.probes:
            result = "PASS" if p.passed else "FAIL"
            lines.append(
                f"| {p.name} | {p.kind} | {', '.join(p.clauses)} | {result} | {p.detail} |"
            )
    lines.append("")

    if a.counterexamples:
        lines.append("## Counterexamples")
        lines.append("")
        for i, ce in enumerate(a.counterexamples, 1):
            lines.append(f"### Counterexample {i}")
            lines.append("")
            for k, v in ce.items():
                lines.append(f"- **{k}:** `{v}`")
            lines.append("")

    if reproduce_command:
        lines.append("## Reproduce")
        lines.append("")
        lines.append("```bash")
        lines.append(reproduce_command)
        lines.append("```")
        lines.append("")

    if a.unresolved:
        lines.append("## Unresolved limitations")
        lines.append("")
        for u in a.unresolved:
            lines.append(f"- {u}")
        lines.append("")

    if a.notes:
        lines.append("## Notes")
        lines.append("")
        for n in a.notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines)


def failing_clauses(a: SemanticAssessment) -> list[str]:
    return sorted({e.clause_id for e in a.evidence if e.outcome is ProbeOutcome.FAIL})


def is_negative(verdict: SemanticVerdict) -> bool:
    return verdict in (
        SemanticVerdict.CONFIRMED_INCORRECT,
        SemanticVerdict.SUSPECTED_FALSE_PASS,
        SemanticVerdict.SUSPECTED_FALSE_FAIL,
    )
