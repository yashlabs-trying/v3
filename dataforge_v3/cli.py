"""Command line entry point for DataForge V3.1 audits."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dataforge_v3.evidence.manifest import verify_artifact_manifest
from dataforge_v3.integrations.harbor_adapter import assess_job_fleet, assess_trial
from dataforge_v3.reporting.schema import FleetReport, classify_final, summarize_metrics
from dataforge_v3.runtime.compatibility import PINNED_VERSIONS, preflight


def _cmd_audit(args: argparse.Namespace) -> int:
    mapping = json.loads(Path(args.job_map).read_text(encoding="utf-8"))
    job_map = {name: Path(path) for name, path in mapping.items()}
    audit_root = Path(args.audit_root) if args.audit_root else None
    upstream_root = Path(args.upstream_root) if args.upstream_root else None
    results = assess_job_fleet(job_map, audit_root=audit_root, upstream_root=upstream_root)
    report = FleetReport(results=results)
    out = Path(args.out)
    report.write_json(out)
    if args.csv:
        report.write_comparison_csv(Path(args.csv))
    if args.metrics:
        Path(args.metrics).write_text(
            json.dumps(summarize_metrics(results), indent=2, sort_keys=True), encoding="utf-8"
        )
    for r in results:
        print(f"{r.task:16s} original={r.original_reward} -> {r.classification.value:8s} "
              f"exec={r.execution.status.value} verify={r.verification.status.value} patch={r.patch.verdict.value}")
    return 0


def _cmd_classify(args: argparse.Namespace) -> int:
    result = assess_trial(
        Path(args.job),
        task_config=Path(args.task_config) if args.task_config else None,
        audit_root=Path(args.audit_root) if args.audit_root else None,
        upstream_root=Path(args.upstream_root) if args.upstream_root else None,
    )
    print(result.to_json())
    return 0


def _cmd_verify_manifest(args: argparse.Namespace) -> int:
    problems = verify_artifact_manifest(Path(args.manifest))
    if problems:
        for p in problems:
            print(f"FAIL {p}")
        return 1
    print("OK")
    return 0


def _cmd_preflight(args: argparse.Namespace) -> int:
    observed = json.loads(args.versions) if args.versions else {}
    env = json.loads(args.env) if args.env else {}
    report = preflight(observed, env)
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.ok else 1


def _cmd_intelligence(args: argparse.Namespace) -> int:
    from pathlib import Path

    from dataforge_v3.intelligence.driver import run_cohort
    from dataforge_v3.intelligence.evidence import EvidenceResolver
    from dataforge_v3.intelligence.reporting import write_diagnosis

    root = Path(args.root)
    out_dir = Path(args.out_dir)
    resolver = EvidenceResolver(root)
    fleet = run_cohort(root)
    for d in fleet.diagnoses:
        write_diagnosis(d, resolver, out_dir / "per_task", d.task_id.replace("/", "_"))
    (out_dir / "capability_profile.json").write_text(
        json.dumps(fleet.to_dict()["capability_profile"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (out_dir / "fleet_diagnosis.json").write_text(
        json.dumps(fleet.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    for d in fleet.diagnoses:
        print(
            f"{d.task_id:16s} valid={d.execution_validity:8s} sem={d.semantic_verdict} "
            f"findings={len(d.findings)} recommendations={len(d.recommendations)}"
        )
    print(f"fleet runtime: {fleet.runtime_seconds:.3f}s")
    return 0


def _cmd_diagnose_case(args: argparse.Namespace) -> int:
    from dataforge_v3.intelligence.case_adapter import diagnose_manifest
    from dataforge_v3.intelligence.evidence import EvidenceResolver
    from dataforge_v3.intelligence.reporting import (
        render_diagnosis_json,
        render_diagnosis_markdown,
    )

    root = Path(args.root)
    manifest = Path(args.manifest)
    diagnosis, _semantic, _obs = diagnose_manifest(root, manifest)
    resolver = EvidenceResolver(root)
    out = Path(args.out) if args.out else None
    payload_json = render_diagnosis_json(diagnosis, resolver)
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload_json, encoding="utf-8")
        md = out.with_suffix(".md")
        md.write_text(render_diagnosis_markdown(diagnosis, resolver), encoding="utf-8")
    print(payload_json)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dataforge_v3")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("audit", help="classify a fleet of Harbor jobs")
    p.add_argument("--job-map", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--csv")
    p.add_argument("--metrics")
    p.add_argument("--audit-root")
    p.add_argument("--upstream-root")
    p.set_defaults(func=_cmd_audit)

    p = sub.add_parser("classify", help="classify one Harbor job")
    p.add_argument("--job", required=True)
    p.add_argument("--task-config")
    p.add_argument("--audit-root")
    p.add_argument("--upstream-root")
    p.set_defaults(func=_cmd_classify)

    p = sub.add_parser("verify-manifest", help="verify an artifact hash manifest")
    p.add_argument("--manifest", required=True)
    p.set_defaults(func=_cmd_verify_manifest)

    p = sub.add_parser("preflight", help="check pinned runtime versions and agent env")
    p.add_argument("--versions", help="JSON object of observed versions")
    p.add_argument("--env", help="JSON object of agent env")
    p.set_defaults(func=_cmd_preflight)

    p = sub.add_parser("intelligence", help="run the V3.3 diagnostic engine over the frozen cohort")
    p.add_argument("--root", default=".", help="repository root")
    p.add_argument("--out-dir", default="findings/intelligence", help="output directory")
    p.set_defaults(func=_cmd_intelligence)

    p = sub.add_parser("diagnose-case", help="run the V3.3 engine on one controlled case manifest")
    p.add_argument("--manifest", required=True, help="path to a case manifest JSON")
    p.add_argument("--root", default=".", help="repository root")
    p.add_argument("--out", help="optional path to write the diagnostic JSON (and .md)")
    p.set_defaults(func=_cmd_diagnose_case)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
