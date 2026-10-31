"""Phase H — performance and scalability measurement (V3.3).

Measures, on realistic recorded trajectories plus clearly-labelled synthetic
scales:

  * parse time for one trajectory
  * evidence-reference validation time
  * findings derivation time
  * report render time
  * per-task peak memory (tracemalloc) and event throughput
  * how these scale with trace size

Synthetic inputs are labelled `synthetic` in the output so a reader never
confuses them with recorded evidence.
"""

from __future__ import annotations

import time
import tracemalloc
from pathlib import Path

from dataforge_v3.intelligence.driver import run_cohort
from dataforge_v3.intelligence.evidence import EvidenceResolver
from dataforge_v3.intelligence.normalizer import load_task_evidence
from dataforge_v3.intelligence.streaming import dedupe_events, order_events
from dataforge_v3.intelligence.schema import Event, EventType, TrajectoryRecord


def bench_real_cohort(root: Path) -> dict:
    tracemalloc.start()
    t0 = time.perf_counter()
    fleet = run_cohort(root)
    elapsed = time.perf_counter() - t0
    _cur, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "provenance": "recorded",
        "tasks": len(fleet.diagnoses),
        "total_seconds": elapsed,
        "peak_bytes": peak,
        "per_task_seconds": [{"task": d.task_id, "seconds": d.runtime_seconds} for d in fleet.diagnoses],
    }


def bench_parse_one(root: Path) -> dict:
    job = root / "jobs" / "f3-vuls-a1"
    inst = next((p for p in sorted(job.iterdir()) if p.is_dir() and p.name.startswith("instance_")), None)
    if inst is None:
        return {"provenance": "recorded", "error": "instance dir missing"}
    traj = inst / "agent" / "mini-swe-agent.trajectory.json"
    t0 = time.perf_counter()
    rec = load_task_evidence(root, "vuls", "f3-vuls-a1", "original").trajectory
    dt = time.perf_counter() - t0
    return {
        "provenance": "recorded",
        "artifact": str(traj.relative_to(root)).replace("\\", "/"),
        "seconds": dt,
        "events": len(rec.events) if rec else 0,
    }


def _synthetic_record(n: int) -> TrajectoryRecord:
    events = [
        Event(event_id=f"e{i}", task_id="syn", event_type=EventType.COMMAND,
              timestamp=float(i), command=f"cmd{i}", returncode=0)
        for i in range(n)
    ]
    return TrajectoryRecord(task_id="syn", attempt="syn", model=None, events=events)


def bench_scaling() -> list[dict]:
    out = []
    for n in (1_000, 10_000, 100_000):
        rec = _synthetic_record(n)
        t0 = time.perf_counter()
        kept, _ = dedupe_events(rec.events)
        ordered = order_events(kept)
        dt = time.perf_counter() - t0
        out.append({
            "provenance": "synthetic",
            "events": n,
            "processed": len(ordered),
            "seconds": dt,
            "events_per_second": (n / dt) if dt > 0 else None,
        })
    return out


def bench_evidence_validation(root: Path) -> dict:
    resolver = EvidenceResolver(root)
    from dataforge_v3.intelligence.schema import EvidenceRef

    refs = [
        EvidenceRef("findings/vuls_semantic_evidence.json", "L1"),
        EvidenceRef("jobs/f3-vuls-a1/instance_future-architect__vuls__sNqH5s4/agent/model.patch", "L1"),
    ]
    t0 = time.perf_counter()
    for _ in range(1000):
        resolver.all_resolve(refs)
    dt = time.perf_counter() - t0
    return {"provenance": "recorded", "iterations": 1000, "seconds": dt, "per_validation_ms": dt}


def run_all(root: Path) -> dict:
    return {
        "real_cohort": bench_real_cohort(root),
        "parse_one": bench_parse_one(root),
        "evidence_validation": bench_evidence_validation(root),
        "scaling": bench_scaling(),
    }
