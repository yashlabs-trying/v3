"""Harbor agent: validate provenance, apply fail-closed, record replay evidence.

Loaded by Harbor as
``dataforge_v3.integrations.df_replay_agent:DataForgeReplayAgent`` with
``--ak source_job=/abs/path/to/job``. The agent never modifies upstream grading
files; it only refuses to let verification proceed on untrustworthy patches.
"""

from __future__ import annotations

import json
import shlex
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from dataforge_v3.lifecycle.state_machine import LifecycleState, LifecycleTracker
from dataforge_v3.patch.provenance import BaselineState, analyze_provenance, parse_git_status
from dataforge_v3.patch.validation import parse_patch, patch_identity, sha256_text
from dataforge_v3.replay.controller import (
    AcceptedChange,
    assess_post_state,
    coerce_accepted,
    decide_replay,
    strict_apply_command,
)
from dataforge_v3.model import PatchVerdict, VerificationStatus


class DataForgePatchError(RuntimeError):
    """Raised when a patch cannot be trusted; verification must not be authoritative."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataForgeReplayAgent(BaseAgent):
    def __init__(
        self,
        *args,
        source_job: str,
        patch_name: str = "model.patch",
        dataforge_root: str | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._source_job = Path(source_job)
        self._patch_name = patch_name
        self._dataforge_root = Path(dataforge_root) if dataforge_root else None

    @staticmethod
    def name() -> str:
        return "dataforge-replay-agent"

    def version(self) -> str:
        return "3.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    def _task_id(self) -> str:
        try:
            cfg = json.loads((self.logs_dir.parent / "config.json").read_text())
            return Path(cfg["task"]["path"]).name
        except Exception:
            return self.logs_dir.parent.name

    def _find_patch(self, task_id: str) -> tuple[Path | None, Path | None]:
        for rj in sorted(self._source_job.glob("instance_*/result.json")):
            try:
                payload = json.loads(rj.read_text())
                name = payload.get("task_name", "").split("/")[-1]
            except Exception:
                continue
            if name == task_id:
                trial = rj.parent
                patch = trial / "agent" / self._patch_name
                return (patch if patch.exists() else None), trial
        return None, None

    async def _git(self, environment: BaseEnvironment, command: str, timeout: int = 120):
        return await environment.exec(
            command="cd /app 2>/dev/null || cd /testbed 2>/dev/null || exit 90; " + command,
            timeout_sec=timeout,
        )

    async def _hash_paths(self, environment: BaseEnvironment, paths: list[str]) -> dict[str, str]:
        if not paths:
            return {}
        quoted = " ".join(shlex.quote(p) for p in paths)
        result = await self._git(environment, f"sha256sum -- {quoted} 2>/dev/null || true", timeout=120)
        hashes: dict[str, str] = {}
        for line in (result.stdout or "").splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                hashes[parts[1].strip()] = parts[0]
        return hashes

    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        started = _now()
        task_id = self._task_id()
        tracker = LifecycleTracker()
        tracker.advance(
            LifecycleState.SETUP_COMPLETE,
            {"environment": "harbor", "agent_config": task_id},
        )
        patch_path, source_trial = self._find_patch(task_id)
        record: dict[str, Any] = {
            "version": "3.1.0",
            "task_id": task_id,
            "source_job": str(self._source_job),
            "source_trial": str(source_trial) if source_trial else None,
            "source_patch": str(patch_path) if patch_path else None,
            "started_at": started,
        }

        if patch_path is None:
            record.update(
                {
                    "patch": {"verdict": PatchVerdict.ABSENT.value, "reasons": ["source patch not found"]},
                    "replay_status": VerificationStatus.PATCH_MISSING.value,
                    "replay_reasons": ["source patch not found"],
                    "finished_at": _now(),
                }
            )
            tracker.advance(
                LifecycleState.FINALIZED,
                {"classification": VerificationStatus.PATCH_MISSING.value},
            )
            record["lifecycle"] = tracker.to_list()
            self._write(record)
            raise DataForgePatchError("DataForge: source patch is missing")

        raw_bytes = patch_path.read_bytes()
        identity = patch_identity(raw_bytes)
        raw_text = identity.text
        canonical_sha = identity.canonical_sha256
        record["patch_sha256"] = canonical_sha
        record["patch_sha256_raw"] = identity.raw_sha256
        record["patch_sha256_lf"] = identity.lf_sha256
        record["patch_eol"] = identity.eol
        record["patch_bytes"] = len(raw_bytes)
        tracker.advance(
            LifecycleState.PATCH_CAPTURED,
            {"patch_sha256": record["patch_sha256"]},
        )

        state = await self._git(environment, "git rev-parse HEAD; echo ---; git status --porcelain --untracked-files=all")
        head, _, porcelain = (state.stdout or "").partition("\n---\n")
        baseline = parse_git_status(porcelain)
        baseline.head = head.strip()
        record["baseline"] = {
            "head": baseline.head,
            "tracked_count": len(baseline.tracked),
            "untracked": sorted(baseline.untracked),
        }

        if not raw_text:
            record.update(
                {
                    "patch": {
                        "verdict": PatchVerdict.EMPTY.value,
                        "sha256": record["patch_sha256"],
                        "size_bytes": 0,
                        "files_total": 0,
                        "files_accepted": 0,
                        "files_excluded": [],
                        "entries": [],
                        "reasons": ["zero-byte patch"],
                    },
                    "provenance": {},
                    "apply_rc": None,
                    "replay_status": VerificationStatus.PATCH_EMPTY.value,
                    "replay_reasons": ["agent produced an explicitly empty submission"],
                    "finished_at": _now(),
                }
            )
            tracker.advance(
                LifecycleState.PATCH_VALIDATED,
                {"patch_sha256": record["patch_sha256"], "patch_validation": PatchVerdict.EMPTY.value},
            )
            tracker.advance(
                LifecycleState.FINALIZED,
                {"classification": VerificationStatus.PATCH_EMPTY.value},
            )
            record["lifecycle"] = tracker.to_list()
            self._write(record)
            return

        analysis = parse_patch(raw_text)
        patch_record, provenance, filtered, accepted = analyze_provenance(analysis, baseline)
        patch_record.sha256 = canonical_sha
        patch_record.size_bytes = len(raw_bytes)
        record["patch"] = patch_record.to_dict()
        record["provenance"] = provenance
        tracker.advance(
            LifecycleState.PATCH_VALIDATED,
            {"patch_sha256": record["patch_sha256"], "patch_validation": patch_record.verdict.value},
        )
        record["filtered_patch_sha256"] = sha256_text(filtered) if filtered else None
        record["filtered_patch_bytes"] = len(filtered.encode("utf-8", errors="surrogateescape"))

        excluded_paths = sorted(
            {
                str(item.get("path"))
                for item in provenance.get("excluded", [])
                if item.get("path")
            }
        )
        before_hashes = await self._hash_paths(environment, excluded_paths)
        record["excluded_artifact_hashes_before"] = before_hashes

        if patch_record.verdict != PatchVerdict.VALID:
            status, reasons = decide_replay(
                patch_verdict=patch_record.verdict,
                apply_rc=None,
                accepted_count=patch_record.files_accepted,
                post_state=None,
            )
            record.update(
                {
                    "apply_rc": None,
                    "replay_status": status.value,
                    "replay_reasons": reasons + patch_record.reasons,
                    "finished_at": _now(),
                }
            )
            tracker.advance(
                LifecycleState.FINALIZED,
                {"classification": status.value},
            )
            record["lifecycle"] = tracker.to_list()
            self._write(record)
            raise DataForgePatchError(f"DataForge: patch rejected ({patch_record.verdict.value})")

        accepted_changes = coerce_accepted(patch_record.entries)
        await environment.upload_file(source_path=self._write_filtered(filtered), target_path="/tmp/dataforge_filtered.patch")
        apply_result = await environment.exec(
            command=strict_apply_command("/tmp/dataforge_filtered.patch"),
            timeout_sec=300,
        )
        apply_rc = apply_result.return_code
        if "DATAFORGE_APPLY_RC=" in (apply_result.stdout or ""):
            for line in (apply_result.stdout or "").splitlines():
                if line.startswith("DATAFORGE_APPLY_RC="):
                    try:
                        apply_rc = int(line.split("=", 1)[1])
                    except ValueError:
                        pass
        record["apply_rc"] = apply_rc
        record["apply_stdout"] = ((apply_result.stdout or "") + (apply_result.stderr or ""))[-6000:]

        post = await self._git(environment, "git status --porcelain --untracked-files=all; echo ---; git --no-pager diff --stat")
        post_porcelain, _, diffstat = (post.stdout or "").partition("\n---\n")
        post_state = assess_post_state(
            accepted_changes,
            post_porcelain,
            baseline.untracked,
        )
        record["post_state"] = {
            "porcelain": post_porcelain[-6000:],
            "diffstat": diffstat[-4000:],
            "touched": post_state.touched,
            "unexpected": post_state.unexpected,
            "missing": post_state.missing,
            "ok": post_state.ok,
        }
        after_hashes = await self._hash_paths(environment, excluded_paths)
        record["excluded_artifact_hashes_after"] = after_hashes
        integrity_ok = before_hashes == after_hashes
        record["excluded_artifact_integrity_ok"] = integrity_ok

        status, reasons = decide_replay(
            patch_verdict=patch_record.verdict,
            apply_rc=apply_rc,
            accepted_count=patch_record.files_accepted,
            post_state=post_state,
        )
        if not integrity_ok:
            status = VerificationStatus.PATCH_APPLICATION_ERROR
            reasons.append("excluded pre-existing artifacts changed during replay")
        record["replay_status"] = status.value
        record["replay_reasons"] = reasons
        record["finished_at"] = _now()
        tracker.advance(
            LifecycleState.PATCH_APPLIED,
            {
                "apply_rc": apply_rc,
                "post_apply_state": {
                    "ok": post_state.ok,
                    "touched": post_state.touched,
                    "unexpected": post_state.unexpected,
                    "missing": post_state.missing,
                },
            },
        )
        tracker.advance(
            LifecycleState.FINALIZED,
            {"classification": status.value},
        )
        record["lifecycle"] = tracker.to_list()
        self._write(record)

        if status != VerificationStatus.VALID:
            raise DataForgePatchError(f"DataForge: replay rejected ({status.value}): {'; '.join(reasons)}")

    def _write_filtered(self, filtered: str) -> Path:
        path = self.logs_dir / "dataforge_filtered.patch"
        path.write_text(filtered, encoding="utf-8", errors="surrogateescape", newline="\n")
        return path

    def _write(self, record: dict[str, Any]) -> None:
        (self.logs_dir / "dataforge_replay.json").write_text(
            json.dumps(record, indent=2, sort_keys=True), encoding="utf-8"
        )
