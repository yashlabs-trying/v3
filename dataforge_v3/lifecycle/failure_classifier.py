"""Classify agent execution state from real harness evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from dataforge_v3.model import ExecutionStatus, ExecutionRecord

_ASSISTANT_MARKERS = (
    "assistant:",
    "role\": \"assistant\"",
    "\"role\": \"assistant\"",
)

_STARTUP_SIGNATURES = (
    ("This model isn't mapped yet", "unsupported_cost_accounting"),
    ("MSWEA_CONFIGURED", "missing_agent_configuration"),
)

_AUTH_SIGNATURES = (
    ("AuthenticationError", "authentication"),
    ("Invalid API key", "authentication"),
    ("401", "authentication"),
    ("403 Forbidden", "authentication"),
)

_NETWORK_SIGNATURES = (
    ("Name or service not known", "dns_resolution"),
    ("Temporary failure in name resolution", "dns_resolution"),
    ("ConnectError", "connection"),
    ("Connection refused", "connection"),
    ("SSLError", "tls"),
    ("SSL: UNEXPECTED_EOF_WHILE_READING", "tls"),
)

_TIMEOUT_SIGNATURES = (
    ("exit 124", "process_timeout"),
    ("timed out", "process_timeout"),
    ("TimeoutError", "process_timeout"),
    ("ReadTimeout", "request_timeout"),
)

_COST_ACCOUNTING = ("This model isn't mapped yet", "get_model_cost_map", "cost")


def count_model_responses(transcript: str, trajectory: dict[str, Any] | None = None) -> int | None:
    """Count assistant turns using the strongest available artifact.

    Returns ``None`` when no artifact can support a count (incomplete visibility),
    which must not be treated as confirmed nonexecution.
    """
    if trajectory is not None:
        messages = trajectory.get("messages")
        if isinstance(messages, list):
            return sum(
                1
                for m in messages
                if isinstance(m, dict) and str(m.get("role", "")).lower() == "assistant"
            )
        steps = trajectory.get("steps")
        if isinstance(steps, list):
            return sum(
                1
                for s in steps
                if isinstance(s, dict) and str(s.get("source", "")).lower() in ("assistant", "agent")
            )
        info = trajectory.get("info")
        if isinstance(info, dict) and isinstance(info.get("model_stats"), dict):
            n = info["model_stats"].get("api_calls")
            if isinstance(n, int):
                return n
    if not transcript:
        return None
    low = transcript.lower()
    hits = sum(low.count(m) for m in _ASSISTANT_MARKERS)
    if hits:
        return hits
    if "building agent config from specs" in low or "mini-swe-agent version" in low:
        return 0
    return None


def _first(transcript: str, signatures: tuple[tuple[str, str], ...]) -> str | None:
    for needle, label in signatures:
        if needle in transcript:
            return label
    return None


def classify_execution(
    *,
    transcript: str | None,
    trajectory: dict[str, Any] | None,
    trial_result: dict[str, Any] | None,
    expectation_hint: ExecutionStatus | None = None,
) -> ExecutionRecord:
    transcript = transcript or ""
    trial_result = trial_result or {}
    exception_info = trial_result.get("exception_info") or {}
    exc_type = exception_info.get("exception_type")
    exc_msg = (exception_info.get("exception_message") or "") + "\n" + (
        exception_info.get("exception_traceback") or ""
    )
    agent_exec = trial_result.get("agent_execution") or {}
    started = bool(agent_exec.get("started_at"))
    finished = bool(agent_exec.get("finished_at"))
    responses = count_model_responses(transcript, trajectory)

    evidence: dict[str, Any] = {
        "transcript_bytes": len(transcript.encode("utf-8")) if transcript else 0,
        "model_responses": responses,
        "agent_process_started": started,
        "agent_execution_started_at": agent_exec.get("started_at"),
        "agent_execution_finished_at": agent_exec.get("finished_at"),
        "exception_type": exc_type,
        "has_trajectory": trajectory is not None,
    }

    if not started and not transcript and trajectory is None and not exc_type:
        return ExecutionRecord(
            ExecutionStatus.UNKNOWN,
            agent_process_started=None,
            model_responses=None,
            evidence={**evidence, "reason": "no execution artifact of any kind"},
        )

    if not started and not agent_exec and not transcript and trajectory is None:
        return ExecutionRecord(
            ExecutionStatus.UNKNOWN,
            agent_process_started=None,
            model_responses=None,
            evidence={**evidence, "reason": "harness recorded no agent phase"},
        )

    startup = _first(transcript + "\n" + exc_msg, _STARTUP_SIGNATURES)
    if startup and (responses in (0, None)):
        return ExecutionRecord(
            ExecutionStatus.STARTUP_ERROR,
            agent_process_started=started,
            model_responses=responses,
            exception_type=exc_type,
            cause=startup,
            evidence=evidence,
        )

    auth = _first(transcript + "\n" + exc_msg, _AUTH_SIGNATURES)
    net = _first(transcript + "\n" + exc_msg, _NETWORK_SIGNATURES)
    timeout = _first(exc_msg, _TIMEOUT_SIGNATURES) or _first(transcript, _TIMEOUT_SIGNATURES)

    if responses == 0 and timeout:
        cause = net or "no_model_response_before_timeout"
        return ExecutionRecord(
            ExecutionStatus.INFRASTRUCTURE_TIMEOUT,
            agent_process_started=started,
            model_responses=0,
            exception_type=exc_type,
            cause=cause,
            evidence=evidence,
        )

    if responses == 0 and auth:
        return ExecutionRecord(
            ExecutionStatus.MODEL_API_ERROR,
            agent_process_started=started,
            model_responses=0,
            exception_type=exc_type,
            cause=auth,
            evidence=evidence,
        )

    if responses == 0 and net:
        return ExecutionRecord(
            ExecutionStatus.MODEL_API_ERROR,
            agent_process_started=started,
            model_responses=0,
            exception_type=exc_type,
            cause=net,
            evidence=evidence,
        )

    if exc_type:
        if exc_type in ("NonZeroAgentExitCodeError", "AgentSetupTimeoutError") or "Timeout" in str(exc_type):
            if responses in (0, None):
                return ExecutionRecord(
                    ExecutionStatus.INFRASTRUCTURE_TIMEOUT,
                    agent_process_started=started,
                    model_responses=responses,
                    exception_type=exc_type,
                    cause=timeout or "agent_phase_timeout",
                    evidence=evidence,
                )
            return ExecutionRecord(
                ExecutionStatus.INTERRUPTED,
                agent_process_started=started,
                model_responses=responses,
                exception_type=exc_type,
                cause=timeout or "agent_phase_interrupted",
                evidence=evidence,
            )
        return ExecutionRecord(
            ExecutionStatus.EXECUTION_ERROR,
            agent_process_started=started,
            model_responses=responses,
            exception_type=exc_type,
            cause=str(exc_type),
            evidence=evidence,
        )

    if responses is None:
        return ExecutionRecord(
            ExecutionStatus.UNKNOWN,
            agent_process_started=started,
            model_responses=None,
            evidence={**evidence, "reason": "execution artifacts inconclusive"},
        )

    if responses == 0:
        return ExecutionRecord(
            ExecutionStatus.UNKNOWN,
            agent_process_started=started,
            model_responses=0,
            evidence={**evidence, "reason": "no exception and no model response"},
        )

    return ExecutionRecord(
        ExecutionStatus.COMPLETED,
        agent_process_started=started,
        model_responses=responses,
        evidence=evidence,
    )


def load_trajectory(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None
