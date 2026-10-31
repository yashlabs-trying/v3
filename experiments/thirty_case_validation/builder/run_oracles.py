"""Execute every controlled defect against its real pytest oracle.

For each domain and each tagged mutant this writes `mutant.py` + `test_oracle.py`
into a temp package directory, runs pytest, parses the per-test PASS/FAIL, and
records the failing probe names. The result is the executable ground truth for
the controlled-defect cases: the failures are produced by the real pytest runner,
not asserted by hand.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from domains import DOMAINS  # noqa: E402

_LINE = re.compile(r"::(test_\w+)\s+(PASSED|FAILED|ERROR)", re.MULTILINE)


_IMPORT = re.compile(r"^\s*from\s+(\w+)\s+import", re.MULTILINE)


def _module_name(oracle: str) -> str:
    m = _IMPORT.search(oracle)
    return m.group(1) if m else "candidate_module"


def run_candidate(source: str, oracle: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory(prefix="df30_") as td:
        d = Path(td)
        (d / f"{_module_name(oracle)}.py").write_text(source, encoding="utf-8")
        (d / "test_oracle.py").write_text(oracle, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider",
             "-o", "addopts=", "test_oracle.py"],
            cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        results: dict[str, str] = {}
        for m in _LINE.finditer(proc.stdout):
            results[m.group(1)] = m.group(2)
        if not results:
            results["<harness>"] = "ERROR"
        return results


def main() -> int:
    out = {}
    for dom in DOMAINS:
        # the correct source must pass the oracle
        base = run_candidate(dom.source, dom.oracle)
        base_failed = [t for t, r in base.items() if r not in ("PASSED",)]
        out[dom.name] = {"correct": {"results": base, "failing": base_failed}, "mutants": {}}
        print(f"=== {dom.name} ===")
        print(f"  correct: {'ALL PASS' if not base_failed else 'FAILING ' + str(base_failed)}")
        for mname, msrc in dom.mutants.items():
            res = run_candidate(msrc, dom.oracle)
            failing = sorted(t for t, r in res.items() if r not in ("PASSED",))
            out[dom.name]["mutants"][mname] = {"results": res, "failing": failing}
            print(f"  {mname:28s} failing={failing}")

    Path(HERE / "oracle_results.json").write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
