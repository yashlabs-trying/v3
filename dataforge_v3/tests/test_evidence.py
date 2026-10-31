from __future__ import annotations

from dataforge_v3.evidence.parser import Observation, RequiredTests
from dataforge_v3.evidence.validation import validate_evidence
from dataforge_v3.model import VerificationStatus

REQ = RequiredTests(fail_to_pass=["TestA"], pass_to_pass=["TestB"])


def _validate(**kwargs):
    base = dict(reward=0.0, observations=[], required=REQ, output_issues=[])
    base.update(kwargs)
    return validate_evidence(**base)


def test_missing_verifier_output_is_incomplete():
    result = _validate(output_issues=["missing verifier output"], reward=None)
    assert result.status is VerificationStatus.EVIDENCE_INCOMPLETE


def test_contradictory_test_statuses_are_detected():
    obs = [Observation("TestA", "PASSED"), Observation("TestA", "FAILED"), Observation("TestB", "PASSED")]
    result = _validate(reward=0.0, observations=obs)
    assert result.status is VerificationStatus.EVIDENCE_CONTRADICTORY
    assert result.contradictory == ["TestA"]


def test_parser_dropping_required_results_is_detected():
    obs = [Observation("TestB", "PASSED")]
    result = _validate(reward=0.0, observations=obs, raw_stdout="--- PASS: TestA (0.01s)\n")
    assert result.status is VerificationStatus.EVIDENCE_INCOMPLETE
    assert result.parser_dropped == ["TestA"]


def test_test_runner_nonzero_exit_is_not_pass():
    result = _validate(reward=1.0, observations=[], runner_exit_code=2)
    assert result.status is VerificationStatus.EVIDENCE_CONTRADICTORY
    result = _validate(reward=0.0, observations=[], runner_exit_code=1)
    assert result.status is VerificationStatus.TEST_EXECUTION_ERROR


def test_test_runner_timeout_is_execution_error():
    result = _validate(reward=0.0, observations=[], runner_timed_out=True)
    assert result.status is VerificationStatus.TEST_EXECUTION_ERROR


def test_reward_disagreement_is_contradictory():
    obs = [Observation("TestA", "PASSED"), Observation("TestB", "PASSED")]
    result = _validate(reward=0.0, observations=obs)
    assert result.status is VerificationStatus.EVIDENCE_CONTRADICTORY


def test_genuine_failure_is_preserved_not_invalidated():
    obs = [Observation("TestA", "FAILED"), Observation("TestB", "PASSED")]
    result = _validate(reward=0.0, observations=obs, raw_stdout="--- FAIL: TestA\n")
    assert result.status is VerificationStatus.VALID
    assert result.not_passed_required == ["TestA"]


def test_all_required_passed_with_matching_reward_is_valid():
    obs = [Observation("TestA", "PASSED"), Observation("TestB", "PASSED")]
    result = _validate(reward=1.0, observations=obs)
    assert result.status is VerificationStatus.VALID


def test_zero_observations_with_contract_is_incomplete():
    result = _validate(reward=0.0, observations=[])
    assert result.status is VerificationStatus.EVIDENCE_INCOMPLETE
