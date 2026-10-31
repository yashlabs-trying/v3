"""Component A — trajectory recording/normalization (V3.3).

Reads the `mini-swe-agent-1.1` trajectory format (and a generic fallback) and
emits a bounded, validated `TrajectoryRecord` of observable `Event`s.

Safety posture (untrusted input):
  * Content is data; it is never executed and never interpreted as instructions.
  * Secrets are redacted before storage.
  * Field and event counts are bounded; oversized records are truncated with a
    warning rather than being silently accepted.
  * Malformed entries are skipped with a warning; a wholly invalid record raises.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from dataforge_v3.intelligence.schema import (
    MAX_EVENTS,
    MAX_FIELD_CHARS,
    MAX_RECORD_BYTES,
    Event,
    EventType,
    TrajectoryRecord,
    ValidityError,
)
from dataforge_v3.intelligence.streaming import sanitize_log_text

# Redaction patterns. Conservative: only clearly-secret shapes.
_REDACTIONS = [
    (re.compile(r"sk-[A-Za-z0-9]{16,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"sk-di-[A-Za-z0-9]{10,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "[REDACTED_GH_TOKEN]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"), "Bearer [REDACTED]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]

# Heuristic: commands that look like test executions (kept conservative; used for
# classification only, never to prove the agent did or did not test).
_TEST_CMD = re.compile(
    r"\b(go test|pytest|python -m pytest|jest|npx jest|npm test|yarn test|mocha|tox|cargo test|"
    r"make test|go build|go vet)\b"
)


def redact(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    out = text
    for pattern, repl in _REDACTIONS:
        out = pattern.sub(repl, out)
    return out


def _clip(text: str) -> str:
    if text is None:
        return ""
    if len(text) > MAX_FIELD_CHARS:
        return text[:MAX_FIELD_CHARS] + f"...[clipped {len(text) - MAX_FIELD_CHARS} chars]"
    return text


def _command_from_tool_call(tc: dict) -> str | None:
    fn = tc.get("function") or {}
    args = fn.get("arguments")
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
        except (ValueError, TypeError):
            return _clip(redact(args))
        if isinstance(parsed, dict) and "command" in parsed:
            return _clip(redact(str(parsed["command"])))
    elif isinstance(args, dict) and "command" in args:
        return _clip(redact(str(args["command"])))
    return None


def _classify_command(cmd: str) -> EventType:
    if _TEST_CMD.search(cmd):
        return EventType.TEST_EXECUTION
    return EventType.COMMAND


class MiniSweAgentNormalizer:
    """Normalizer for the `mini-swe-agent-1.1` trajectory format."""

    format_name = "mini-swe-agent-1.1"

    def __init__(self, max_events: int = MAX_EVENTS) -> None:
        self.max_events = max_events

    def can_handle(self, raw: dict) -> bool:
        return raw.get("trajectory_format", "").startswith("mini-swe-agent") and "messages" in raw

    def normalize(
        self,
        raw: dict,
        task_id: str,
        attempt: str,
        source_artifact: str | None = None,
    ) -> TrajectoryRecord:
        info = raw.get("info", {}) or {}
        messages = raw.get("messages", []) or []
        warnings: list[str] = []
        truncated = False
        if len(messages) > self.max_events:
            messages = messages[: self.max_events]
            truncated = True
            warnings.append(f"event cap reached ({self.max_events}); trajectory truncated")

        model = _extract_model(info)
        exit_status = info.get("exit_status")
        api_calls = _safe_int(info.get("model_stats", {}).get("api_calls"))
        cost = _safe_float(info.get("model_stats", {}).get("instance_cost"))
        total_tokens = _sum_tokens(messages)

        events: list[Event] = []
        counter = 0

        def next_id() -> str:
            nonlocal counter
            eid = f"evt-{counter:05d}"
            counter += 1
            return eid

        events.append(
            Event(
                event_id=next_id(),
                task_id=task_id,
                event_type=EventType.SESSION_START,
                timestamp=None,
                payload={"model": model},
                artifact_ref=source_artifact,
                provenance=self.format_name,
            )
        )

        # Map tool_call_id -> command so tool results can carry the command.
        pending: dict[str, str] = {}

        for idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                warnings.append(f"message[{idx}] not an object; skipped")
                continue
            role = msg.get("role")
            locator = f"messages[{idx}]"
            if role == "assistant":
                for tc in msg.get("tool_calls") or []:
                    cmd = _command_from_tool_call(tc)
                    tcid = tc.get("id")
                    if cmd and tcid:
                        pending[tcid] = cmd
                    if cmd:
                        events.append(
                            Event(
                                event_id=next_id(),
                                task_id=task_id,
                                event_type=_classify_command(cmd),
                                timestamp=_ts(msg),
                                command=cmd,
                                artifact_ref=source_artifact,
                                provenance=f"{self.format_name}:{locator}",
                            )
                        )
            elif role == "tool":
                tcid = msg.get("tool_call_id")
                cmd = pending.pop(tcid, None) if tcid else None
                extra = msg.get("extra") or {}
                rc = _safe_int(extra.get("returncode"))
                raw_out = extra.get("raw_output") or msg.get("content") or ""
                events.append(
                    Event(
                        event_id=next_id(),
                        task_id=task_id,
                        event_type=EventType.TOOL_RESULT,
                        timestamp=_ts(msg),
                        command=cmd,
                        returncode=rc,
                        exit_code=rc,
                        payload={
                            "output_head": sanitize_log_text(redact(str(raw_out))[:4000]),
                            "exception_info": sanitize_log_text(redact(str(extra.get("exception_info", "")))),
                        },
                        artifact_ref=source_artifact,
                        provenance=f"{self.format_name}:{locator}",
                    )
                )
            elif role == "exit":
                extra = msg.get("extra") or {}
                events.append(
                    Event(
                        event_id=next_id(),
                        task_id=task_id,
                        event_type=EventType.SESSION_END,
                        timestamp=_ts(msg),
                        payload={
                            "exit_status": extra.get("exit_status"),
                            "submission": _clip(redact(str(extra.get("submission", "")))),
                        },
                        artifact_ref=source_artifact,
                        provenance=f"{self.format_name}:{locator}",
                    )
                )
            elif role == "system":
                events.append(
                    Event(
                        event_id=next_id(),
                        task_id=task_id,
                        event_type=EventType.MODEL_RESPONSE,
                        payload={"note": "system prompt present (not treated as evidence)"},
                        artifact_ref=source_artifact,
                        provenance=f"{self.format_name}:{locator}",
                    )
                )

        events.append(
            Event(
                event_id=next_id(),
                task_id=task_id,
                event_type=EventType.SESSION_END,
                payload={"exit_status": exit_status, "api_calls": api_calls},
                artifact_ref=source_artifact,
                provenance=self.format_name,
            )
        )

        return TrajectoryRecord(
            task_id=task_id,
            attempt=attempt,
            model=model,
            events=events,
            exit_status=exit_status,
            api_calls=api_calls,
            cost_usd=cost,
            total_tokens=total_tokens,
            source_artifact=source_artifact,
            truncated=truncated,
            warnings=warnings,
        )


def _ts(msg: dict) -> float | None:
    extra = msg.get("extra") or {}
    t = extra.get("timestamp")
    return _safe_float(t)


def _safe_int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _safe_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _extract_model(info: dict) -> str | None:
    cfg = info.get("config") or {}
    model = cfg.get("model") or {}
    return model.get("model_name")


def _sum_tokens(messages: list) -> int | None:
    total = 0
    found = False
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        extra = msg.get("extra") or {}
        resp = extra.get("response") or {}
        usage = resp.get("usage") or {}
        tt = usage.get("total_tokens")
        if isinstance(tt, int):
            total += tt
            found = True
    return total if found else None


def load_trajectory_file(path: Path, task_id: str, attempt: str) -> TrajectoryRecord:
    """Load and normalize a trajectory file, enforcing the size bound."""
    if not path.exists():
        raise ValidityError(f"trajectory not found: {path}")
    size = path.stat().st_size
    if size > MAX_RECORD_BYTES:
        raise ValidityError(f"trajectory exceeds size bound ({size} > {MAX_RECORD_BYTES})")
    try:
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise ValidityError(f"malformed trajectory JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValidityError("trajectory root must be an object")
    normalizer = MiniSweAgentNormalizer()
    if not normalizer.can_handle(raw):
        raise ValidityError(f"unsupported trajectory format: {raw.get('trajectory_format')!r}")
    return normalizer.normalize(raw, task_id=task_id, attempt=attempt, source_artifact=str(path))
