"""Pinned runtime compatibility checks derived from the frozen harness manifest."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PINNED_VERSIONS = {
    "mini-swe-agent": "2.4.6",
    "litellm": "1.106.6",
    "mcp": "2.3.0",
    "mcp-types": "2.3.0",
    "openai": "2.54.0",
    "httpx": "0.28.1",
    "pydantic": "2.14.2",
}

REQUIRED_AGENT_ENV = {
    "OPENAI_API_KEY": None,
    "OPENAI_BASE_URL": None,
    "MSWEA_CONFIGURED": "true",
    "MSWEA_COST_TRACKING": "ignore_errors",
}

PINNED_HARBOR = "0.25.0"
PINNED_UPSTREAM_COMMIT = "66f92766bba642462d4bbe5479e83f91f9211862"


@dataclass
class CompatibilityReport:
    ok: bool
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    observed: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "problems": self.problems,
            "warnings": self.warnings,
            "observed": self.observed,
            "pinned": {
                "harbor": PINNED_HARBOR,
                "upstream_commit": PINNED_UPSTREAM_COMMIT,
                "packages": PINNED_VERSIONS,
            },
        }


def check_versions(observed: dict[str, str | None], strict: bool = True) -> list[str]:
    problems: list[str] = []
    for name, pinned in PINNED_VERSIONS.items():
        if name not in observed:
            continue
        actual = observed[name]
        if actual is None:
            problems.append(f"{name}: version not recorded")
        elif actual != pinned:
            problems.append(f"{name}: {actual} != pinned {pinned}")
    if strict and observed.get("harbor") and observed["harbor"] != PINNED_HARBOR:
        problems.append(f"harbor: {observed['harbor']} != pinned {PINNED_HARBOR}")
    return problems


def validate_agent_env(env: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for key, expected in REQUIRED_AGENT_ENV.items():
        if key not in env or env[key] == "":
            problems.append(f"missing required agent env: {key}")
            continue
        if expected is not None and env[key] != expected:
            problems.append(f"{key}={env[key]!r} != required {expected!r}")
    return problems


def preflight(observed_versions: dict[str, str | None], env: dict[str, str]) -> CompatibilityReport:
    problems = check_versions(observed_versions)
    problems.extend(validate_agent_env(env))
    return CompatibilityReport(
        ok=not problems,
        problems=problems,
        observed={"versions": observed_versions, "env_keys": sorted(env.keys())},
    )
