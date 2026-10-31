from __future__ import annotations

from pathlib import Path

import pytest

from dataforge_v3.integrations.harbor_adapter import _resolve_source_trial, assess_trial
from dataforge_v3.model import FinalClassification, PatchVerdict

ROOT = Path(__file__).resolve().parents[2]
RERUN = ROOT / "jobs" / "df-rerun"
AUDIT = ROOT / "audit_tasks"


def _assess(name: str):
    return assess_trial(RERUN / f"df-rerun-{name}", audit_root=AUDIT)


def test_relocated_replay_resolves_source_trial_inside_checkout(tmp_path):
    job_dir = tmp_path / "jobs" / "df-rerun" / "df-rerun-x"
    source_trial = tmp_path / "jobs" / "final-x" / "instance_x"
    source_trial.mkdir(parents=True)
    job_dir.mkdir(parents=True)
    replay = {
        "source_job": "/mnt/c/elsewhere/jobs/final-x",
        "source_trial": "/mnt/c/elsewhere/jobs/final-x/instance_x",
    }
    assert _resolve_source_trial(job_dir, replay) == source_trial
    assert _resolve_source_trial(job_dir, {}) is None


@pytest.mark.skipif(not RERUN.exists(), reason="DataForge replay jobs not present")
def test_nodebb_rerun_is_invalid_and_contamination_only():
    result = _assess("nodebb")
    assert result.classification is FinalClassification.INVALID
    assert result.patch.verdict is PatchVerdict.CONTAMINATED_ONLY
    assert result.patch.files_accepted == 0
    assert len(result.patch.files_excluded) == 3
    assert all(item["path"].startswith("appendonlydir/") for item in result.patch.files_excluded)
    assert result.execution.model_responses == 0
    assert result.execution.status.value == "INFRASTRUCTURE_TIMEOUT"
    assert result.original_reward == 0.0


@pytest.mark.skipif(not RERUN.exists(), reason="DataForge replay jobs not present")
def test_nodebb_recovery_rerun_is_pass_after_filtering():
    result = _assess("recovery")
    assert result.classification is FinalClassification.PASS
    assert result.patch.verdict is PatchVerdict.VALID
    assert result.patch.files_accepted == 7
    assert len(result.patch.files_excluded) == 3
    assert result.replay["excluded_artifact_integrity_ok"] is True
    assert result.replay["apply_rc"] == 0
    assert result.replay["post_state"]["ok"] is True
    assert result.verification.status.value == "VALID"
    assert result.verification.reward == 1.0
    assert [s["state"] for s in result.lifecycle] == [
        "SETUP_COMPLETE",
        "PATCH_CAPTURED",
        "PATCH_VALIDATED",
        "PATCH_APPLIED",
        "FINALIZED",
    ]


@pytest.mark.skipif(not RERUN.exists(), reason="DataForge replay jobs not present")
@pytest.mark.parametrize(
    "name,expected",
    [
        ("flipt", FinalClassification.PASS),
        ("openlibrary", FinalClassification.PASS),
        ("teleport", FinalClassification.PASS),
        ("ansible", FinalClassification.PASS),
        ("elementweb", FinalClassification.PASS),
        ("vuls", FinalClassification.FAIL),
    ],
)
def test_rerun_verdicts(name, expected):
    result = _assess(name)
    assert result.classification is expected
    assert result.patch.verdict is PatchVerdict.VALID
