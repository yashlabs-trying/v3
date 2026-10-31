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
            encoding="utf-8",
            errors="replace",
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


# --- vuls (models package) -------------------------------------------------

VULS_IMAGE = (
    "dataforge-agent:instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed"
)

_VULS_TEST_LINE = re.compile(r"^\s*--- (PASS|FAIL|SKIP):\s+(TestDataForgeVulsOrdering\S*)")


def parse_vuls_probe_output(stdout: str) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for line in stdout.splitlines():
        m = _VULS_TEST_LINE.match(line)
        if not m:
            continue
        status, name = m.groups()
        if "TestDataForgeVulsOrdering/" not in name:
            continue  # parent test line, not a property subtest
        short = name.split("TestDataForgeVulsOrdering/", 1)[1]
        passed = status == "PASS"
        clauses = []
        if short.startswith("score.order"):
            clauses = ["sort.by_score"]
        elif short.startswith("tie.order"):
            clauses = ["sort.equal_score_order"]
        detail = "" if passed else f"go subtest {status}"
        results.append(
            ProbeResult(
                name=f"vuls:{short}",
                kind="differential",
                passed=passed,
                clauses=clauses,
                detail=detail,
                counterexample=None if passed else {"go_subtest": short, "status": status},
            )
        )
    return results


def run_vuls_probes(    candidate_vulninfos: str,
    oracle_source: str,
    image: str = VULS_IMAGE,
    go_package: str = "./models",
    test_name: str = "TestDataForgeVulsOrdering",
    probe_filename: str = "zz_df_vuls_oracle_test.go",
    timeout_s: int = 900,
) -> list[ProbeResult]:
    """Swap candidate models/vulninfos.go into /app/models, run the oracle, parse."""
    with tempfile.TemporaryDirectory(prefix="df32_vuls_") as td:
        tmp = Path(td)
        (tmp / "vulninfos.go").write_text(candidate_vulninfos, encoding="utf-8")
        (tmp / probe_filename).write_text(oracle_source, encoding="utf-8")

        inner = (
            "set -e; "
            "cp /overlay/vulninfos.go /app/models/vulninfos.go; "
            f"cp /overlay/{probe_filename} /app/models/{probe_filename}; "
            "cd /app; "
            # Move the image's own models tests aside so a stale test file that
            # references removed identifiers cannot break compilation. The oracle
            # is self-contained.
            "mv models/vulninfos_test.go /tmp/_hidden_vulninfos_test.go 2>/dev/null || true; "
            "export PATH=/usr/local/go/bin:/usr/bin:/bin:/usr/sbin:/sbin; "
            f"go test -count=1 -v -run '^{test_name}$' {go_package} 2>&1; "
            "true"
        )
        script = (
            "#!/bin/bash\n"
            f'docker run --rm -v "{_wsl_path(tmp)}:/overlay" {image} bash -c "{inner}"\n'
        )
        (tmp / "run.sh").write_text(script, encoding="ascii", newline="\n")

        proc = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "bash", f"{_wsl_path(tmp)}/run.sh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        combined = proc.stdout + "\n" + proc.stderr
        results = parse_vuls_probe_output(combined)
        if not results:
            results = [
                ProbeResult(
                    name="vuls:harness-error",
                    kind="differential",
                    passed=False,
                    detail=f"no probe results parsed (exit {proc.returncode})",
                    counterexample={"tail": combined[-2000:]},
                )
            ]
        return results


# --- teleport (lib/asciitable) ---------------------------------------------

TELEPORT_IMAGE = (
    "dataforge-agent:instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-"
    "vee9b09fb20c43af7e520f57e9239bbcf46b7113d"
)

_TELE_TEST_LINE = re.compile(
    r"^\s*--- (PASS|FAIL|SKIP):\s+(TestDataForgeTeleportTruncation\S*)"
)


def parse_teleport_probe_output(stdout: str) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    for line in stdout.splitlines():
        m = _TELE_TEST_LINE.match(line)
        if not m:
            continue
        status, name = m.groups()
        if "TestDataForgeTeleportTruncation/" not in name:
            continue  # parent
        short = name.split("TestDataForgeTeleportTruncation/", 1)[1]
        passed = status == "PASS"
        results.append(
            ProbeResult(
                name=f"teleport:{short}",
                kind="differential",
                passed=passed,
                clauses=[short],
                detail="" if passed else f"go subtest {status}",
                counterexample=None if passed else {"go_subtest": short, "status": status},
            )
        )
    return results


def run_teleport_probes(
    candidate_table: str,
    oracle_source: str,
    image: str = TELEPORT_IMAGE,
    go_package: str = "./lib/asciitable",
    test_name: str = "TestDataForgeTeleportTruncation",
    probe_filename: str = "zz_df_teleport_oracle_test.go",
    timeout_s: int = 1200,
) -> list[ProbeResult]:
    with tempfile.TemporaryDirectory(prefix="df32_tele_") as td:
        tmp = Path(td)
        (tmp / "table.go").write_text(candidate_table, encoding="utf-8")
        (tmp / probe_filename).write_text(oracle_source, encoding="utf-8")
        inner = (
            "set -e; "
            "cp /overlay/table.go /app/lib/asciitable/table.go; "
            f"cp /overlay/{probe_filename} /app/lib/asciitable/{probe_filename}; "
            "cd /app; "
            "mv lib/asciitable/table_test.go /tmp/_hidden_table_test.go 2>/dev/null || true; "
            "export PATH=/usr/local/go/bin:/usr/bin:/bin:/usr/sbin:/sbin; "
            "export CGO_ENABLED=1; "
            f"go test -count=1 -v -run '^{test_name}$' {go_package} 2>&1; "
            "true"
        )
        script = (
            "#!/bin/bash\n"
            f'docker run --rm -v "{_wsl_path(tmp)}:/overlay" {image} bash -c "{inner}"\n'
        )
        (tmp / "run.sh").write_text(script, encoding="ascii", newline="\n")
        proc = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "bash", f"{_wsl_path(tmp)}/run.sh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        combined = proc.stdout + "\n" + proc.stderr
        results = parse_teleport_probe_output(combined)
        if not results:
            results = [
                ProbeResult(
                    name="teleport:harness-error",
                    kind="differential",
                    passed=False,
                    detail=f"no probe results parsed (exit {proc.returncode})",
                    counterexample={"tail": combined[-2000:]},
                )
            ]
        return results


# --- ansible (lib/ansible/module_utils/urls.py) ----------------------------

ANSIBLE_IMAGE = (
    "dataforge-agent:instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-"
    "v173091e2e36d38c978002990795f66cfc0af30ad"
)

_ANS_TEST_LINE = re.compile(r"(test_df_\w+)\s+(PASSED|FAILED|ERROR)")


def parse_ansible_probe_output(stdout: str) -> list[ProbeResult]:
    results: list[ProbeResult] = []
    seen = set()
    for line in stdout.splitlines():
        m = _ANS_TEST_LINE.search(line)
        if not m:
            continue
        name, status = m.groups()
        if name in seen:
            continue
        seen.add(name)
        passed = status == "PASSED"
        results.append(
            ProbeResult(
                name=f"ansible:{name}",
                kind="differential",
                passed=passed,
                clauses=[name],
                detail="" if passed else f"pytest {status}",
                counterexample=None if passed else {"test": name, "status": status},
            )
        )
    return results


def run_ansible_probes(
    candidate_urls: str,
    oracle_files: dict[str, str],
    image: str = ANSIBLE_IMAGE,
    timeout_s: int = 1200,
) -> list[ProbeResult]:
    with tempfile.TemporaryDirectory(prefix="df32_ansible_") as td:
        tmp = Path(td)
        (tmp / "urls.py").write_text(candidate_urls, encoding="utf-8")
        for fname, content in oracle_files.items():
            (tmp / fname).write_text(content, encoding="utf-8")

        copies = " ".join(
            f"cp /overlay/{fname} /app/test/units/module_utils/urls/{fname};" for fname in oracle_files
        )
        inner = (
            "set -e; "
            "cp /overlay/urls.py /app/lib/ansible/module_utils/urls.py; "
            + copies +
            " cd /app; "
            "export PYTHONPATH=/app/lib; "
            "python -m pytest -v -p no:cacheprovider "
            + " ".join(f"test/units/module_utils/urls/{fname}" for fname in oracle_files) +
            " 2>&1; true"
        )
        script = (
            "#!/bin/bash\n"
            f'docker run --rm -v "{_wsl_path(tmp)}:/overlay" {image} bash -c "{inner}"\n'
        )
        (tmp / "run.sh").write_text(script, encoding="ascii", newline="\n")
        proc = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "bash", f"{_wsl_path(tmp)}/run.sh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        combined = proc.stdout + "\n" + proc.stderr
        results = parse_ansible_probe_output(combined)
        if not results:
            results = [
                ProbeResult(
                    name="ansible:harness-error",
                    kind="differential",
                    passed=False,
                    detail=f"no probe results parsed (exit {proc.returncode})",
                    counterexample={"tail": combined[-2000:]},
                )
            ]
        return results


# --- element-web (src/utils/LruCache.ts) ------------------------------------

ELEMENTWEB_IMAGE = (
    "dataforge-agent:instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan"
)

_EW_TEST_LINE = re.compile(r"\b(df_\w+)\b")


def parse_elementweb_probe_output(stdout: str) -> list[ProbeResult]:
    """Parse jest verbose output for our generated df_* test names."""
    results: list[ProbeResult] = []
    seen = set()
    for line in stdout.splitlines():
        if not (line.strip().startswith(("✓", "✗", "✕", "√", "×")) or "df_" in line):
            continue
        m = _EW_TEST_LINE.search(line)
        if not m:
            continue
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        passed = line.strip().startswith(("✓", "√"))
        results.append(
            ProbeResult(
                name=f"element-web:{name}",
                kind="differential",
                passed=passed,
                clauses=[name],
                detail="" if passed else "jest failed",
                counterexample=None if passed else {"test": name},
            )
        )
    return results


def run_elementweb_probes(
    candidate_lru: str,
    test_source: str,
    test_filename: str = "zz_df_LruCache-test.ts",
    image: str = ELEMENTWEB_IMAGE,
    timeout_s: int = 1800,
) -> list[ProbeResult]:
    with tempfile.TemporaryDirectory(prefix="df32_ew_") as td:
        tmp = Path(td)
        (tmp / "LruCache.ts").write_text(candidate_lru, encoding="utf-8")
        (tmp / test_filename).write_text(test_source, encoding="utf-8")
        inner = (
            "set -e; "
            "cp /overlay/LruCache.ts /app/src/utils/LruCache.ts; "
            f"cp /overlay/{test_filename} /app/test/utils/{test_filename}; "
            "cd /app; "
            f"npx jest --verbose --silent --maxWorkers=1 --forceExit test/utils/{test_filename} 2>&1; "
            "true"
        )
        script = (
            "#!/bin/bash\n"
            f'docker run --rm -v "{_wsl_path(tmp)}:/overlay" {image} bash -c "{inner}"\n'
        )
        (tmp / "run.sh").write_text(script, encoding="ascii", newline="\n")
        proc = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "bash", f"{_wsl_path(tmp)}/run.sh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        combined = proc.stdout + "\n" + proc.stderr
        results = parse_elementweb_probe_output(combined)
        if not results:
            results = [
                ProbeResult(
                    name="element-web:harness-error",
                    kind="differential",
                    passed=False,
                    detail=f"no probe results parsed (exit {proc.returncode})",
                    counterexample={"tail": combined[-2000:]},
                )
            ]
        return results
