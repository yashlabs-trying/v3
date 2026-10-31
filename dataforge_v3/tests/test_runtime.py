from __future__ import annotations

import pytest

from dataforge_v3.runtime.compatibility import PINNED_VERSIONS, check_versions, preflight, validate_agent_env
from dataforge_v3.runtime.health import RetryPolicy, endpoint_reachable, health_report, run_with_retries


def test_endpoint_unreachable_is_detected():
    ok, detail = endpoint_reachable("http://127.0.0.1:1", timeout=0.5)
    assert ok is False
    assert "tcp connect failed" in detail


def test_unsupported_usage_accounting_is_visible_in_health():
    transcript = "mini-swe-agent version 2.4.6\nRuntimeError: This model isn't mapped yet\n"
    report = health_report(transcript, host="api.deepinfra.com")
    assert report.startup_failure == "unsupported_cost_accounting"
    assert report.model_responses == 0


def test_missing_agent_configuration_is_detected():
    problems = validate_agent_env({"OPENAI_API_KEY": "x", "OPENAI_BASE_URL": "https://example"})
    assert any("MSWEA_CONFIGURED" in p for p in problems)
    assert any("MSWEA_COST_TRACKING" in p for p in problems)


def test_version_mismatch_is_detected():
    observed = {"mini-swe-agent": "9.9.9", "litellm": "1.106.6"}
    problems = check_versions(observed)
    assert any("mini-swe-agent" in p for p in problems)
    assert not any("litellm" in p for p in problems)


def test_matching_pins_and_env_pass_preflight():
    observed = dict(PINNED_VERSIONS)
    observed["harbor"] = "0.25.0"
    env = {
        "OPENAI_API_KEY": "x",
        "OPENAI_BASE_URL": "https://api.deepinfra.com/v1/openai",
        "MSWEA_CONFIGURED": "true",
        "MSWEA_COST_TRACKING": "ignore_errors",
    }
    report = preflight(observed, env)
    assert report.ok, report.problems


def test_infrastructure_retry_requires_label_and_preserves_attempts():
    policy = RetryPolicy(max_attempts=2)
    with pytest.raises(ValueError):
        run_with_retries(lambda i: None, policy, lambda e: True, label=None)

    calls = {"n": 0}

    def flaky(attempt):
        calls["n"] += 1
        if attempt == 1:
            raise TimeoutError("sidecar stall")
        return "ok"

    result, attempts = run_with_retries(flaky, policy, lambda e: isinstance(e, TimeoutError), label="recovery")
    assert result == "ok"
    assert [a["status"] for a in attempts] == ["error", "ok"]
    assert attempts[0]["label"] == "recovery"
