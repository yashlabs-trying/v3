"""Component D — actionable experiment recommendations (V3.3).

Each recommendation is a *testable experiment*, not advice. The template is keyed
by the finding's capability dimension / category — generic, so no task-specific
prose is hardcoded. A recommendation always carries: the finding it addresses,
its evidence, a hypothesis, an intervention, a control, a measurable outcome and
a cost estimate. `executed` stays False unless a controlled run actually happens;
an unexecuted recommendation is reported NOT_EXECUTED, never as an improvement.
"""

from __future__ import annotations

from dataforge_v3.intelligence.schema import (
    ExperimentRecommendation,
    FailureCategory,
    Finding,
)

# Infrastructure categories are not agent-capability findings; they get no
# agent-workflow experiment recommendation.
_INFRA_CATEGORIES = {
    FailureCategory.AGENT_STARTUP_FAILURE,
    FailureCategory.INVALID_PATCH_ARTIFACT,
    FailureCategory.REPLAY_FAILURE,
    FailureCategory.INVALID_VERIFIER_EVIDENCE,
    FailureCategory.BUDGET_EXHAUSTED,
}

# Category -> (intervention, hypothesis, metric) template. Deliberately generic.
_TEMPLATES: dict[FailureCategory, dict[str, str]] = {
    FailureCategory.EXISTING_BEHAVIOR_REMOVED: {
        "intervention": (
            "Add a mandatory pre-edit step: before changing behavior covered by an "
            "existing test, inspect that test and the code path it exercises, and "
            "record the invariant being preserved."
        ),
        "hypothesis": (
            "Requiring pre-edit inspection of pre-existing tests reduces removal of "
            "established, test-covered behavior."
        ),
        "metric": (
            "Rate of satisfying BOTH the newly requested behavior AND the "
            "pre-existing invariant, on the same frozen task set, scored by an "
            "independent semantic oracle."
        ),
    },
    FailureCategory.REGRESSION: {
        "intervention": (
            "Require the agent to run the pre-existing regression suite before and "
            "after its edit and diff the results."
        ),
        "hypothesis": "A pre/post regression diff prevents silent regressions.",
        "metric": "Regression-test pass rate before vs after the edit.",
    },
    FailureCategory.REQUIREMENT_OMITTED: {
        "intervention": (
            "Require an explicit requirement-to-change checklist, mapped to the "
            "instruction bullets, before submission."
        ),
        "hypothesis": "An explicit coverage checklist raises requirement coverage.",
        "metric": "Fraction of instruction bullets with a demonstrably satisfying change.",
    },
    FailureCategory.EDGE_CASE_FAILURE: {
        "intervention": (
            "Require authoring and running boundary probes (empty, single, maximal, "
            "off-by-one) for the changed function."
        ),
        "hypothesis": "Forced boundary probing reduces edge-case failures.",
        "metric": "Edge-case probe pass rate on the same frozen task.",
    },
    FailureCategory.INTERFACE_COMPATIBILITY_VIOLATION: {
        "intervention": (
            "Require searching all call sites of a changed signature/type before the "
            "edit and listing the compatibility impact."
        ),
        "hypothesis": "Call-site enumeration reduces interface-compatibility breaks.",
        "metric": "Number of call sites left inconsistent with the new interface.",
    },
    FailureCategory.RELEVANT_TEST_NOT_EXECUTED: {
        "intervention": (
            "Require the agent to identify and execute the specific pre-existing test "
            "that covers the changed behavior."
        ),
        "hypothesis": "Mandating the covering test reduces untested submissions.",
        "metric": "Fraction of submissions that executed their covering test.",
    },
    FailureCategory.FAILING_TEST_UNRESOLVED: {
        "intervention": (
            "Disallow submission while any executed test is failing, unless the agent "
            "records why the failure is out of scope."
        ),
        "hypothesis": "A no-red-submission gate reduces unresolved failures.",
        "metric": "Fraction of submissions with at least one unresolved failing test.",
    },
}

_GENERIC = {
    "intervention": (
        "Introduce a controlled intervention targeting this finding and compare it "
        "against the unmodified workflow."
    ),
    "hypothesis": "The intervention reduces the recurrence of this finding class.",
    "metric": "Verified-correctness rate on a frozen task set under an independent oracle.",
}


def recommend_for_findings(findings: list[Finding]) -> list[ExperimentRecommendation]:
    recs: list[ExperimentRecommendation] = []
    for f in findings:
        if f.category in _INFRA_CATEGORIES:
            continue  # infrastructure is a platform issue, not an agent-capability finding
        tpl = _TEMPLATES.get(f.category, _GENERIC)
        recs.append(
            ExperimentRecommendation(
                id=f"{f.id}:rec",
                finding_id=f.id,
                task_id=f.id.split(":")[0],
                evidence=list(f.evidence),
                intervention=tpl["intervention"],
                hypothesis=tpl["hypothesis"],
                control=(
                    "Same frozen task, same model and configuration, same evaluation "
                    "budget, same independent verifier; only the intervention differs."
                ),
                expected_outcome=(
                    "Measured change in the metric below with the intervention vs the "
                    "control; null result reported if no improvement."
                ),
                metric=tpl["metric"],
                cost_estimate=(
                    "Additional inspection/token overhead to be measured per run; "
                    "not claimed until executed."
                ),
                confounders=[
                    "Small sample size (n=1 task per class here)",
                    "Model stochasticity across runs",
                    "Intervention may shift behavior on tasks outside this class",
                ],
                executed=False,
                execution_note="no new model execution was authorized",
            )
        )
    return recs
