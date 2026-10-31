# Trajectory Schema — DataForge V3.3 (System A)

## 1. Purpose

A versioned, normalized view of *observable* agent execution. It captures what the
agent demonstrably did (commands, tool results, tests, patches, errors, lifecycle)
and never the model's hidden reasoning.

Source formats consumed (read-only):

- `mini-swe-agent-1.1` — `agent/mini-swe-agent.trajectory.json` (`{info, messages, trajectory_format}`).
- `ATIF-v1.7` — `agent/trajectory.json` (`{schema_version, steps}`), a normalised derivative.
- Generic fallback for future frameworks (`normalizer.py` is the extension point).

## 2. Event envelope (illustrative; schema is in `schema.py`)

```json
{
  "event_id": "evt-00042",
  "task_id": "example",
  "event_type": "test_execution",
  "timestamp": 1712345678.0,
  "command": "go test ./models",
  "exit_code": 1,
  "returncode": 1,
  "payload": {"output_head": "...", "exception_info": ""},
  "artifact_ref": "jobs/example/instance_.../agent/mini-swe-agent.trajectory.json",
  "provenance": "mini-swe-agent-1.1:messages[57]"
}
```

`event_type` ∈ {session_start, session_end, model_response, tool_call, tool_result,
command, file_read, file_write, patch_snapshot, test_execution, test_result, error,
retry, infrastructure_error, unknown}.

## 3. Record envelope

`TrajectoryRecord`: `task_id, attempt, model, events[], exit_status, api_calls,
cost_usd, total_tokens, source_artifact, truncated, warnings[]`.

## 4. Invariants and enforced protections

| Requirement | Implementation |
|---|---|
| Preserve provenance | every event carries `artifact_ref` + `provenance` locator. |
| Record missing data explicitly | `normalizer` appends a note when a trajectory is absent. |
| Handle incomplete trajectories | `truncated` flag + warning at the event cap. |
| Handle duplicate events | `streaming.dedupe_events` drops by `event_id`, warns with the count. |
| Handle out-of-order events | `streaming.order_events` stable-sorts by timestamp; missing ts keeps position. |
| Never invent tool calls | only messages present in the artifact are parsed. |
| Log text is data, not instructions | `streaming.sanitize_log_text` tags instruction-like spans. |
| Redact credentials | `trajectory.redact` scrubs API keys / bearer / private keys. |
| Bounded memory | `MAX_EVENTS`, `MAX_FIELD_CHARS`, `MAX_RECORD_BYTES`; streaming `iter_events`. |
| Link material events to source | `EvidenceRef` + `EvidenceResolver` hash verification. |
| Future-framework compatible | normalizer registry; no format assumption in the engine. |

## 5. Bounds

- `MAX_EVENTS = 200_000`
- `MAX_FIELD_CHARS = 20_000`
- `MAX_RECORD_BYTES = 64 MiB`

An artifact exceeding the byte bound is rejected with `ValidityError`; exceeding
the event cap truncates with a warning (never silently).

## 6. Validation

`Event.from_dict` raises `ValidityError` on a missing `event_id`/`task_id` or an
unknown `event_type`. Malformed entries inside a message list are skipped with a
warning; a wholly invalid record raises.
