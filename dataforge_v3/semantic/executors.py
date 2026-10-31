"""Docker-backed Go executor for the flipt semantic oracle (V3.2).

Runs the generated semantic probes against a candidate `middleware.go` inside
the task's own Docker image, so the probe uses the repo's real dependencies. The
host runs Windows; Docker lives in WSL, so this module writes a small bash script
to a temp directory and invokes it through `wsl`.

Output contract: the Go test emits standard `--- PASS/FAIL: TestDataForgeSemanticProbes/<name>`
lines. This module parses them into `ProbeResult`s. Parsing is unit-tested from
captured fixtures so the logic can be validated without Docker.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from dataforge_v3.semantic.model import ProbeResult

FLIPT_IMAGE = (
    "dataforge-agent:instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f"
)

_TEST_LINE = re.compile(r"^\s*--- (PASS|FAIL|SKIP):\s+(TestDataForgeSemanticProbes\S*)")
_CLAUSE_BY_PROBE = {
    "bearer": "bearer.exact",
    "cookie.fallback": "cookie.fallback",
    "cookie.multiple": "cookie.multiple",
    "header.precedence": "header.precedence",
    "header.malformed": "header.malformed.no_fallback",
    "bypass.membership": "bypass.membership",
    "bypass.before_extraction": "bypass.before_extraction",
}


def clauses_for_probe(name: str) -> list[str]:
    for prefix, clause in _CLAUSE_BY_PROBE.items():
        if prefix in name:
            return [clause]
    return []


def parse_go_probe_output(stdout: str) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for line in stdout.splitlines():
        m = _TEST_LINE.match(line)
        if not m:
            continue
        status, name = m.groups()
        short = name.split("/", 1)[1] if "/" in name else name
        passed = status == "PASS"
        results.append(
            ProbeResult(
                name=f"flipt:{short}",
                kind="differential",
                passed=passed,
                clauses=clauses_for_probe(short),
                detail="" if passed else f"go subtest {status}",
                counterexample=None
                if passed
                else {"go_subtest": short, "status": status},
            )
        )
    return results


def run_flipt_probes(
    candidate_middleware: str,
    probe_source: str,
    image: str = FLIPT_IMAGE,
    go_package: str = "./internal/server/auth",
    test_name: str = "TestDataForgeSemanticProbes",
    probe_filename: str = "zz_df_semantic_test.go",
    timeout_s: int = 900,
) -> list[ProbeResult]:
    """Materialize candidate+probe, run them in the image, parse subtest results."""
    with tempfile.TemporaryDirectory(prefix="df32_flipt_") as td:
        tmp = Path(td)
        (tmp / "middleware.go").write_text(candidate_middleware, encoding="utf-8")
        (tmp / probe_filename).write_text(probe_source, encoding="utf-8")

        script = _build_script(tmp, image, go_package, test_name, probe_filename)
        script_path = tmp / "run.sh"
        script_path.write_text(script, encoding="ascii", newline="\n")

        mount = _wsl_path(tmp)
        proc = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "bash", f"{mount}/run.sh"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        combined = proc.stdout + "\n" + proc.stderr
        results = parse_go_probe_output(combined)
        if not results:
            results = [
                ProbeResult(
                    name="flipt:harness-error",
                    kind="differential",
                    passed=False,
                    detail=f"no probe results parsed (exit {proc.returncode})",
                    counterexample={"tail": combined[-2000:]},
                )
            ]
        return results


def _wsl_path(win_path: Path) -> str:
    s = str(win_path).replace("\\", "/")
    if len(s) >= 2 and s[1] == ":":
        drive = s[0].lower()
        return f"/mnt/{drive}{s[2:]}"
    return s


def _build_script(tmp: Path, image: str, go_package: str, test_name: str, probe_filename: str) -> str:
    inner = (
        "set -e; "
        "cp /overlay/middleware.go /app/internal/server/auth/middleware.go; "
        f"cp /overlay/{probe_filename} /app/internal/server/auth/{probe_filename}; "
        "cd /app; "
        "export PATH=/usr/local/go/bin:/usr/bin:/bin:/usr/sbin:/sbin; "
        f"go test -count=1 -v -run '^{test_name}$' {go_package} 2>&1; "
        "true"
    )
    return (
        "#!/bin/bash\n"
        f'docker run --rm -v "{_wsl_path(tmp)}:/overlay" {image} bash -c "{inner}"\n'
    )
