from __future__ import annotations

import json
from pathlib import Path

import pytest

from dataforge_v3.integrations.harbor_adapter import assess_trial
from dataforge_v3.model import FinalClassification, PatchVerdict
from dataforge_v3.patch.validation import parse_patch

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "audit_tasks"
JOBS = ROOT / "jobs"

CASES = [
    ("nodebb", "final-nodebb", FinalClassification.INVALID),
    ("flipt", "final-flipt", FinalClassification.PASS),
    ("vuls", "f3-vuls-a1", FinalClassification.FAIL),
    ("openlibrary", "f3-openlibrary-a1", FinalClassification.PASS),
    ("teleport", "f3-teleport-a1", FinalClassification.PASS),
    ("ansible", "f3-ansible-a1", FinalClassification.PASS),
    ("elementweb", "f3-elementweb-a1", FinalClassification.PASS),
]


@pytest.mark.skipif(not JOBS.exists(), reason="frozen baseline jobs not present")
@pytest.mark.parametrize("name,job,expected", CASES)
def test_baseline_verdicts(name, job, expected):
    result = assess_trial(JOBS / job, audit_root=AUDIT)
    assert result.classification is expected, (
        name,
        result.execution.to_dict(),
        result.verification.to_dict(),
        result.patch.to_dict(),
    )


@pytest.mark.skipif(not JOBS.exists(), reason="frozen baseline jobs not present")
def test_nodebb_original_is_invalid_for_execution_not_model_skill():
    result = assess_trial(JOBS / "final-nodebb", audit_root=AUDIT)
    assert result.classification is FinalClassification.INVALID
    assert result.execution.model_responses == 0
    assert result.execution.status.value == "INFRASTRUCTURE_TIMEOUT"


@pytest.mark.skipif(not JOBS.exists(), reason="frozen baseline jobs not present")
def test_nodebb_frozen_patch_is_redis_only():
    patches = list((JOBS / "final-nodebb").glob("instance_*/agent/model.patch"))
    assert patches
    analysis = parse_patch(patches[0].read_text(encoding="utf-8", errors="replace"))
    assert analysis.entries
    assert all(e.path.startswith("appendonlydir/") for e in analysis.entries)
    assert not any(e.path.startswith("src/") for e in analysis.entries)


@pytest.mark.skipif(not JOBS.exists(), reason="frozen baseline jobs not present")
def test_nodebb_upstream_replay_applied_nothing():
    replays = list((JOBS / "regrade-nodebb").glob("instance_*/agent/replay.json"))
    assert replays
    payload = json.loads(replays[0].read_text())
    assert payload["apply_rc"] == 1
    assert " | " not in payload.get("post_apply_diffstat", "")


@pytest.mark.skipif(not JOBS.exists(), reason="frozen baseline jobs not present")
def test_recovery_upstream_replay_was_partial_and_must_not_be_authoritative():
    result = assess_trial(JOBS / "regrade-nodebb-recovery", audit_root=AUDIT)
    assert result.classification is FinalClassification.INVALID
    assert result.verification.status.value == "PATCH_APPLICATION_ERROR"
