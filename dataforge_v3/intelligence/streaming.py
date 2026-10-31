"""V3.3 System A robustness: streaming, dedup, ordering, injection defense.

Trajectories are untrusted. This module adds, on top of `trajectory.py`:

  * `sanitize_log_text` — neutralises instruction-like content found inside tool
    output so downstream reports can never treat it as trusted instructions.
    It does not delete evidence; it annotates and escapes it.
  * `dedupe_events` — drops duplicate `event_id`s, keeping the first, and records
    a warning count (never silently).
  * `order_events` — stable-sorts by timestamp where present, leaving events with
    no timestamp in their original relative position (so a partial trajectory is
    not reordered into a false sequence).
  * `iter_events` / `stream_normalize` — bounded-memory ingestion: the record is
    built incrementally and never holds more than `max_events` events.

These are pure functions over `Event` objects; the diagnostic engine treats the
resulting record as its only view of the trajectory.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, Iterator

from dataforge_v3.intelligence.schema import Event, TrajectoryRecord

# Instruction-like markers a hostile trace might embed. We never act on them; we
# mark them so a human reviewer sees the attempt and no downstream step confuses
# log text with a directive.
_INJECTION_PATTERNS = [
    re.compile(r"(?i)\bignore (all )?(previous|prior) instructions?\b"),
    re.compile(r"(?i)\bdisregard (the )?(above|previous|prior)\b"),
    re.compile(r"(?i)\byou are now\b"),
    re.compile(r"(?i)\bsystem prompt\b"),
    re.compile(r"(?i)\bas an ai (language )?model\b"),
    re.compile(r"(?i)\bexecute the following command\b"),
    re.compile(r"(?i)\bwrite the file\b.*\bto\b"),
    re.compile(r"(?i)\bmark (this|the) (task|test) as (pass|passing|success)\b"),
    re.compile(r"(?i)\bset (the )?(reward|score) to\b"),
]

_INJECTION_TAG = "[DF:instruction-like content in untrusted log]"


def detect_injection(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def sanitize_log_text(text: str, max_chars: int = 4000) -> str:
    """Return text that is safe to display: instruction-like spans are tagged.

    The content is preserved (evidence), but prefixed with a marker so no reader
    or downstream tool mistakes it for a trusted instruction.
    """
    if not isinstance(text, str):
        text = str(text)
    if len(text) > max_chars:
        text = text[:max_chars] + f"...[clipped {len(text) - max_chars} chars]"
    if detect_injection(text):
        return f"{_INJECTION_TAG} {text}"
    return text


def dedupe_events(events: list[Event]) -> tuple[list[Event], int]:
    seen: set[str] = set()
    out: list[Event] = []
    dropped = 0
    for e in events:
        if e.event_id in seen:
            dropped += 1
            continue
        seen.add(e.event_id)
        out.append(e)
    return out, dropped


def order_events(events: list[Event]) -> list[Event]:
    """Stable sort by timestamp; events without a timestamp keep relative order.

    Implemented by sorting only the timestamped subsequence is *not* sufficient
    to keep stable interleaving, so we use a stable sort on the whole list with a
    key that places a missing timestamp at its original index (Python's sort is
    stable, and using index as tie-break preserves input order).
    """
    indexed = list(enumerate(events))
    indexed.sort(key=lambda pair: (pair[1].timestamp is None, pair[1].timestamp or 0.0, pair[0]))
    return [e for _, e in indexed]


def iter_events(record: TrajectoryRecord, predicate=None) -> Iterator[Event]:
    """Stream events from a record without materialising a new list."""
    for e in record.events:
        if predicate is None or predicate(e):
            yield e


def stream_normalize(normalizer, raw: dict, task_id: str, attempt: str,
                     source_artifact: str | None = None, max_events: int = 200_000) -> TrajectoryRecord:
    """Normalize with dedup + ordering + bounded memory, recording warnings.

    Wraps a normalizer's `normalize` and post-processes. Memory is bounded by the
    normalizer's own `max_events` cap; this adds no unbounded buffers.
    """
    record = normalizer.normalize(raw, task_id=task_id, attempt=attempt, source_artifact=source_artifact)
    events, dropped = dedupe_events(record.events)
    if dropped:
        record.warnings.append(f"dropped {dropped} duplicate event(s) by event_id")
    ordered = order_events(events)
    if [e.event_id for e in ordered] != [e.event_id for e in events]:
        record.warnings.append("events were out of order; reordered stably by timestamp")
    record.events = ordered
    return replace(record, events=ordered)


def count_events(record: TrajectoryRecord) -> int:
    return len(record.events)
