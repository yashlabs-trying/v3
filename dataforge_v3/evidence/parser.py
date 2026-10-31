"""Parse verifier evidence and required-test contracts."""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RequiredTests:
    fail_to_pass: list[str] = field(default_factory=list)
    pass_to_pass: list[str] = field(default_factory=list)

    @property
    def all_required(self) -> list[str]:
        return sorted(set(self.fail_to_pass) | set(self.pass_to_pass))


@dataclass
class Observation:
    name: str
    status: str


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            pass
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (ValueError, SyntaxError):
            pass
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return []


def load_required(config_path: Path) -> RequiredTests:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return RequiredTests(
        fail_to_pass=_as_list(payload.get("fail_to_pass")),
        pass_to_pass=_as_list(payload.get("pass_to_pass")),
    )


def parse_output(output_path: Path) -> tuple[list[Observation], list[str]]:
    issues: list[str] = []
    if not output_path.exists():
        return [], [f"missing verifier output: {output_path}"]
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError) as exc:
        return [], [f"malformed verifier output: {exc}"]
    tests = payload.get("tests") if isinstance(payload, dict) else None
    if not isinstance(tests, list):
        return [], ["verifier output has no tests list"]
    observations: list[Observation] = []
    for item in tests:
        if not isinstance(item, dict):
            issues.append("non-object test record")
            continue
        name = item.get("name")
        status = item.get("status")
        if not isinstance(name, str) or not isinstance(status, str):
            issues.append("test record missing name/status")
            continue
        observations.append(Observation(name=name, status=status.upper()))
    return observations, issues


def parse_reward(reward_path: Path) -> float | None:
    if not reward_path.exists():
        return None
    raw = reward_path.read_text(encoding="utf-8", errors="replace").strip()
    try:
        return float(raw.splitlines()[0])
    except (ValueError, IndexError):
        return None


def read_text(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    data = path.read_text(encoding="utf-8", errors="replace")
    return data if limit is None else data[:limit]


def parse_test_patch_paths(patch_path: Path) -> list[str]:
    if not patch_path.exists():
        return []
    paths: list[str] = []
    for line in patch_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("+++ b/"):
            paths.append(line[len("+++ b/") :])
        elif line.startswith("--- a/"):
            paths.append(line[len("--- a/") :])
    return sorted(set(paths))


def detect_masking(run_script_text: str) -> list[str]:
    patterns = {
        "|| true": "nonzero exit masked with '|| true'",
        "|| echo": "nonzero exit masked with '|| echo'",
    }
    return [msg for pat, msg in patterns.items() if pat in run_script_text]
