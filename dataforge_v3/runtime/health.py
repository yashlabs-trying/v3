"""Agent-startup and model-endpoint health checks from recorded transcripts."""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

from dataforge_v3.lifecycle.failure_classifier import (
    count_model_responses,
    _AUTH_SIGNATURES,
    _NETWORK_SIGNATURES,
    _STARTUP_SIGNATURES,
    _TIMEOUT_SIGNATURES,
    _first,
)

_STALL_RE = re.compile(r"(\d{2}:\d{2}:\d{2}).*?(LiteLLM|cost map|retrying)", re.IGNORECASE)


@dataclass
class HealthReport:
    model_responses: int | None
    first_response_seen: bool
    startup_failure: str | None
    transport_failure: str | None
    timeout_signal: str | None
    stalled: bool
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_responses": self.model_responses,
            "first_response_seen": self.first_response_seen,
            "startup_failure": self.startup_failure,
            "transport_failure": self.transport_failure,
            "timeout_signal": self.timeout_signal,
            "stalled": self.stalled,
            "warnings": self.warnings,
        }


def _model_transport_failure(transcript: str, host: str | None) -> str | None:
    if not transcript:
        return None
    for line in transcript.splitlines():
        low = line.lower()
        if host and host.lower() not in low and "litellm" not in low and "completion" not in low:
            continue
        for needle, label in _NETWORK_SIGNATURES:
            if needle in line:
                return label
    return None


def health_report(transcript: str, host: str | None = None, trajectory: dict | None = None) -> HealthReport:
    responses = count_model_responses(transcript or "", trajectory)
    startup = _first(transcript or "", _STARTUP_SIGNATURES)
    transport = _first(transcript or "", _NETWORK_SIGNATURES)
    auth = _first(transcript or "", _AUTH_SIGNATURES)
    timeout = _first(transcript or "", _TIMEOUT_SIGNATURES)
    model_transport = _model_transport_failure(transcript or "", host)
    warnings: list[str] = []
    if transport and not model_transport:
        warnings.append("non-model network error present (e.g. cost-map fetch); not attributed to the model endpoint")
    first = bool(responses and responses > 0)
    stalled = (responses == 0) and bool(timeout)
    return HealthReport(
        model_responses=responses,
        first_response_seen=first,
        startup_failure=startup,
        transport_failure=model_transport or auth,
        timeout_signal=timeout,
        stalled=stalled,
        warnings=warnings,
    )


def endpoint_reachable(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return False, "invalid endpoint url"
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"tcp connect ok {host}:{port}"
    except OSError as exc:
        return False, f"tcp connect failed {host}:{port}: {exc}"


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    require_label: bool = True
    label: str = "recovery"

    def validate(self, label: str | None) -> list[str]:
        problems: list[str] = []
        if self.max_attempts < 1:
            problems.append("max_attempts must be >= 1")
        if self.require_label and not label:
            problems.append("infrastructure recovery must be labelled and must not replace the original result")
        return problems


def run_with_retries(
    fn: Callable[[int], Any],
    policy: RetryPolicy,
    is_infrastructure_error: Callable[[Exception], bool],
    label: str | None = None,
) -> tuple[Any, list[dict[str, Any]]]:
    problems = policy.validate(label)
    if problems:
        raise ValueError("; ".join(problems))
    attempts: list[dict[str, Any]] = []
    last_exc: Exception | None = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            result = fn(attempt)
            attempts.append({"attempt": attempt, "status": "ok", "label": label})
            return result, attempts
        except Exception as exc:  # noqa: BLE001 - classification is explicit
            last_exc = exc
            attempts.append({"attempt": attempt, "status": "error", "error": type(exc).__name__, "label": label})
            if not is_infrastructure_error(exc):
                break
    assert last_exc is not None
    raise last_exc
