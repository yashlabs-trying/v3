"""Phase G — diagnostic baseline comparison (V3.3).

Compares four approaches on the frozen cohort against an independently-reviewed
answer key:

  A  raw             — the conventional benchmark report (V2 verdict + test line).
  A+ semantic-aware  — raw PLUS the V3.2 independent semantic findings.
  B  generic LLM     — a frozen prompt over the same permitted evidence.
  DF DataForge V3.3  — the structured engine.

The point (Section 11): isolate the advantage of *additional semantic evidence*
(A+) from the advantage of the *diagnostic engine itself* (DF). Baseline B is
recorded as INCOMPLETE unless a model is authorized and its inputs/outputs are
captured; it is never fabricated.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dataforge_v3.intelligence.driver import run_cohort
from dataforge_v3.intelligence.normalizer import COHORT, load_task_evidence
from dataforge_v3.intelligence.schema import FailureCategory

# Independently-reviewed answer key: what a correct diagnosis must state.
# `expected_defect`: the verified defect clause or None; `forbids`: phrases that
# would be an UNSUPPORTED accusation (a false claim against a passing/invalid
# run), NOT neutral confirmations such as "weaknesses: none". Kept precise so the
# contrast does not punish correct negative statements.
ANSWER_KEY: dict[str, dict] = {
    "flipt": {"validity": "VALID", "verdict": "CONFIRMED_CORRECT", "expected_defect": None,
              "forbids": ["weak at", "failed to understand", "is incorrect", "has a bug"]},
    "openlibrary": {"validity": "VALID", "verdict": "CONFIRMED_CORRECT", "expected_defect": None,
                    "forbids": ["weak at", "failed to understand", "is incorrect", "has a bug"]},
    "teleport": {"validity": "VALID", "verdict": "CONFIRMED_CORRECT", "expected_defect": None,
                 "forbids": ["weak at", "failed to understand", "is incorrect", "has a bug"]},
    "ansible": {"validity": "VALID", "verdict": "CONFIRMED_CORRECT", "expected_defect": None,
                "forbids": ["weak at", "failed to understand", "is incorrect", "has a bug"]},
    "element-web": {"validity": "VALID", "verdict": "CONFIRMED_CORRECT", "expected_defect": None,
                    "forbids": ["weak at", "failed to understand", "is incorrect", "has a bug"]},
    "vuls": {"validity": "VALID", "verdict": "GENUINE_AGENT_FAILURE",
             "expected_defect": "sort.equal_score_order",
             "forbids": ["false fail", "benchmark is wrong", "grader bug"]},
    "NodeBB": {"validity": "INVALID", "verdict": "INCONCLUSIVE", "expected_defect": None,
               "forbids": ["weak javascript", "cannot fix", "failed to understand",
                           "weak redis", "coding weakness", "failed to implement"]},
    "NodeBB-recovery": {"validity": "VALID", "verdict": "CONFIRMED_CORRECT", "expected_defect": None,
                        "forbids": ["weak at", "failed to understand", "is incorrect", "has a bug"]},
}

FROZEN_LLM_PROMPT = (
    "You are given a benchmark result for one coding task: the PASS/FAIL verdict, "
    "the failing test output if any, and basic execution metadata. Produce a short "
    "diagnosis of why the result occurred. Do not speculate beyond the evidence given."
)


@dataclass
class ApproachScore:
    name: str
    defect_identified: int = 0
    defect_total: int = 0
    hallucinations: int = 0        # claims contradicting the answer key
    unresolved_evidence_refs: int = 0
    actionability: int = 0         # recommendations with a measurable metric
    tasks_evaluated: int = 0

    def to_dict(self):
        return asdict(self)


def _raw_report(evidence) -> str:
    """A conventional benchmark report: verdict + the failing test line only."""
    verdict = "PASS" if (evidence.original_score or 0) >= 1.0 else "FAIL"
    failing = visible_failing_tests(evidence)
    line = (
        f"Task {evidence.short_name}: V2 verdict={verdict} (score={evidence.original_score}); "
        f"execution={evidence.execution_validity}."
    )
    if failing:
        line += f" Failing required test(s): {', '.join(failing)}; the agent's change does not satisfy them."
    return line


def visible_failing_tests(evidence) -> list[str]:
    """Only the *observable* failing test names a raw report would see.

    Reads the verifier output that the benchmark itself surfaces; this is the same
    information a conventional report has, so the baseline is not handicapped.
    """
    if evidence.replay and isinstance(evidence.replay, dict):
        ft = evidence.replay.get("failing_tests")
        if isinstance(ft, list):
            return [str(x) for x in ft]
    return []


def _semantic_aware_report(evidence, semantic) -> str:
    base = _raw_report(evidence)
    if semantic and semantic.failing_probes():
        names = ", ".join(p.name for p in semantic.failing_probes())
        clauses = sorted({c for p in semantic.failing_probes() for c in p.clauses})
        return base + (
            f" Independent semantic probes failing: {names}"
            + (f" (clauses: {', '.join(clauses)})." if clauses else ".")
        )
    return base + " Independent semantic probes: none failing on the audited surface."


_NEGATIONS = ("not ", "no ", "never ", "without ", "does not", "cannot", "n't ", "none ")


def _is_unsupported_accusation(text: str, phrase: str) -> bool:
    """True only if `phrase` occurs as an ASSERTION, not inside a negation.

    Naive substring matching falsely flags correct negative statements such as
    "it does not evidence any model coding weakness". We therefore ignore a match
    when a negation cue appears in the ~40 chars preceding it.
    """
    low = text.lower()
    needle = phrase.lower()
    start = 0
    while True:
        i = low.find(needle, start)
        if i < 0:
            return False
        window = low[max(0, i - 40):i]
        if not any(neg in window for neg in _NEGATIONS):
            return True
        start = i + len(needle)


def _contains_forbidden(text: str, task: str) -> bool:
    return any(_is_unsupported_accusation(text, f) for f in ANSWER_KEY[task].get("forbids", []))


def run_comparison(root: Path) -> dict:
    fleet = run_cohort(root)
    by_task = {d.task_id: d for d in fleet.diagnoses}

    A = ApproachScore(name="raw_benchmark")
    Aplus = ApproachScore(name="raw_plus_semantic")
    B = ApproachScore(name="generic_llm")
    DF = ApproachScore(name="dataforge_v3_3")

    hall_A = hall_Aplus = hall_DF = 0
    for name, _job, _att in COHORT:
        key = ANSWER_KEY[name]
        d = by_task[name]
        A.tasks_evaluated += 1
        Aplus.tasks_evaluated += 1
        DF.tasks_evaluated += 1

        # raw report
        raw = _raw_report(load_task_evidence(root, name, _job, _att))
        if _contains_forbidden(raw, name):
            hall_A += 1
        # raw + semantic
        from dataforge_v3.intelligence.normalizer import load_semantic_input

        aware = _semantic_aware_report(load_task_evidence(root, name, _job, _att), load_semantic_input(root, name))
        if _contains_forbidden(aware, name):
            hall_Aplus += 1

        # defect identification (the vuls clause)
        if key["expected_defect"]:
            A.defect_total += 1
            Aplus.defect_total += 1
            DF.defect_total += 1
            clause_name = key["expected_defect"]
            # raw: a conventional report does not name the violated contract clause
            if clause_name in raw.lower():
                A.defect_identified += 1
            # raw + semantic: the clause id is present in the V3.2 probe evidence
            if clause_name in aware.lower():
                Aplus.defect_identified += 1
            # DataForge: the finding is attributed to the clause id
            if any(f.violated_requirement == clause_name for f in d.findings):
                DF.defect_identified += 1
        # DataForge hallucinations: forbidden content in its report
        from dataforge_v3.intelligence.reporting import render_diagnosis_markdown
        from dataforge_v3.intelligence.evidence import EvidenceResolver

        md = render_diagnosis_markdown(d, EvidenceResolver(root))
        if _contains_forbidden(md, name):
            hall_DF += 1
        # evidence refs
        resolver = EvidenceResolver(root)
        for f in d.findings:
            ok, _ = resolver.all_resolve(f.evidence)
            if not ok:
                DF.unresolved_evidence_refs += 1
        # actionability
        DF.actionability += sum(1 for r in d.recommendations if r.get("metric"))

    A.hallucinations = hall_A
    Aplus.hallucinations = hall_Aplus
    DF.hallucinations = hall_DF

    return {
        "answer_key": ANSWER_KEY,
        "frozen_llm_prompt": FROZEN_LLM_PROMPT,
        "approaches": {
            "raw_benchmark": A.to_dict(),
            "raw_plus_semantic": Aplus.to_dict(),
            "generic_llm": {
                **B.to_dict(),
                "status": "INCOMPLETE",
                "reason": (
                    "No external model execution authorized; inputs/outputs were not "
                    "captured. Reported incomplete rather than fabricated."
                ),
            },
            "dataforge_v3_3": DF.to_dict(),
        },
        "isolation_note": (
            "raw_plus_semantic isolates the contribution of additional semantic "
            "evidence; dataforge_v3_3 additionally applies generic clause attribution, "
            "capability evidence and measurable recommendations. generic_llm is the "
            "unrun control that would isolate the value of structured diagnosis over "
            "free-text explanation."
        ),
    }
