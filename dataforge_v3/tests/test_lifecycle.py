from __future__ import annotations

import pytest

from dataforge_v3.lifecycle.failure_classifier import classify_execution
from dataforge_v3.lifecycle.state_machine import LifecycleError, LifecycleState, LifecycleTracker
from dataforge_v3.model import (
    DataForgeResult,
    ExecutionRecord,
    ExecutionStatus,
    FinalClassification,
    PatchRecord,
    PatchVerdict,
    VerificationRecord,
    VerificationStatus,
)
from dataforge_v3.reporting.schema import classify_final


def _result(execution, patch_verdict=PatchVerdict.VALID, status=VerificationStatus.VALID, reward=1.0):
    return classify_final(
        execution,
        PatchRecord(verdict=patch_verdict),
        VerificationRecord(status=status, reward=reward),
    )


def test_agent_never_starts_is_not_a_model_failure():
    record = classify_execution(transcript=None, trajectory=None, trial_result={})
    assert record.status is ExecutionStatus.UNKNOWN
    assert record.model_responses is None
    final, _ = _result(record)
    assert final is FinalClassification.INVALID


def test_incomplete_visibility_is_not_confirmed_nonexecution():
    trial = {"agent_execution": {"started_at": "2026-01-01T00:00:00Z"}}
    record = classify_execution(transcript="", trajectory=None, trial_result=trial)
    assert record.status is ExecutionStatus.UNKNOWN
    assert record.agent_process_started is True


def test_model_api_fails_before_first_response():
    transcript = "mini-swe-agent version 2.4.6\nAuthenticationError: Invalid API key\n"
    record = classify_execution(transcript=transcript, trajectory=None, trial_result={})
    assert record.status is ExecutionStatus.MODEL_API_ERROR
    assert record.model_responses == 0


def test_startup_cost_accounting_failure_is_startup_error():
    transcript = "mini-swe-agent version 2.4.6\nRuntimeError: This model isn't mapped yet\n"
    record = classify_execution(transcript=transcript, trajectory=None, trial_result={})
    assert record.status is ExecutionStatus.STARTUP_ERROR
    assert record.cause == "unsupported_cost_accounting"


def test_nodebb_style_zero_response_timeout_is_infrastructure():
    transcript = (
        "This is mini-swe-agent version 2.4.6.\n"
        "LiteLLM: Failed to fetch remote model cost map ... ConnectError\n"
        "System:\nYou are a helpful assistant\nUser:\nsolve it\n"
    )
    trial = {
        "exception_info": {
            "exception_type": "NonZeroAgentExitCodeError",
            "exception_message": "Command failed (exit 124): timeout -k 30 2940 ...",
        },
        "agent_execution": {"started_at": "a", "finished_at": "b"},
    }
    record = classify_execution(transcript=transcript, trajectory=None, trial_result=trial)
    assert record.status is ExecutionStatus.INFRASTRUCTURE_TIMEOUT
    assert record.model_responses == 0
    final, reasons = _result(record, PatchVerdict.CONTAMINATED_ONLY, VerificationStatus.PATCH_INVALID, 0.0)
    assert final is FinalClassification.INVALID
    assert reasons


def test_legitimate_agent_failure_is_preserved():
    trial = {
        "agent_execution": {"started_at": "a", "finished_at": "b"},
        "exception_info": None,
    }
    trajectory = {"messages": [{"role": "assistant", "content": "working"}, {"role": "user", "content": "x"}]}
    record = classify_execution(transcript="", trajectory=trajectory, trial_result=trial)
    assert record.status is ExecutionStatus.COMPLETED
    final, _ = _result(record, status=VerificationStatus.VALID, reward=0.0)
    assert final is FinalClassification.FAIL


def test_legitimate_pass_is_preserved():
    trial = {"agent_execution": {"started_at": "a", "finished_at": "b"}}
    trajectory = {"messages": [{"role": "assistant", "content": "done"}]}
    record = classify_execution(transcript="", trajectory=trajectory, trial_result=trial)
    final, _ = _result(record, status=VerificationStatus.VALID, reward=1.0)
    assert final is FinalClassification.PASS


def test_lifecycle_requires_evidence_and_is_monotonic():
    tracker = LifecycleTracker()
    with pytest.raises(LifecycleError):
        tracker.advance(LifecycleState.SETUP_COMPLETE, {})
    tracker.advance(LifecycleState.SETUP_COMPLETE, {"environment": "docker", "agent_config": "x"})
    tracker.advance(LifecycleState.AGENT_STARTED, {"agent_process_started": True})
    with pytest.raises(LifecycleError):
        tracker.advance(LifecycleState.SETUP_PENDING, {})
    assert tracker.current is LifecycleState.AGENT_STARTED
