"""Run the security battery against the ORIGINAL (pre-fix) evidence module."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("evidence_orig", sys.argv[1])
m = importlib.util.module_from_spec(spec)
sys.modules["evidence_orig"] = m
spec.loader.exec_module(m)
from dataforge_v3.intelligence.schema import EvidenceRef  # noqa: E402

root = Path(ROOT).resolve()
r = m.EvidenceResolver(root)
battery = [
    ("absolute inside root (real file)", str(root / "findings" / "vuls_semantic_evidence.json"), "rejected"),
    ("absolute outside root", "C:/Windows/System32/drivers/etc/hosts", "rejected"),
    ("dotdot traversal", "findings/../../Windows/System32/drivers/etc/hosts", "rejected"),
    ("dotdot in middle", "jobs/../../secret.txt", "rejected"),
    ("posix absolute", "/etc/passwd", "rejected"),
    ("tilde", "~/secret.txt", "rejected"),
    ("relative inside approved evidence root", "findings/vuls_semantic_evidence.json", "trusted"),
    ("repo file outside evidence roots (.git)", ".git/config", "rejected"),
    ("answer key inside repo", "experiments/six_case_validation/ground_truth.json", "rejected"),
    ("nonexistent inside root", "findings/does_not_exist.json", "rejected"),
    ("empty path", "", "rejected"),
]
rows = []
for name, art, exp in battery:
    res = r.resolve(EvidenceRef(art, "x", name))
    ok = (res.exists and res.authoritative) if exp == "trusted" else not res.exists
    rows.append({"name": name, "artifact": art, "expectation": exp, "exists": res.exists,
                 "authoritative": res.authoritative, "error": res.error, "ok": ok})
    print(f"[{'OK ' if ok else 'XX '}] {name:42s} exists={str(res.exists):5s} err={res.error}")
n_ok = sum(1 for x in rows if x["ok"])
print(f"\npre-fix: {n_ok}/{len(rows)}")
Path("experiments/thirty_case_validation/security/pre_fix.json").write_text(
    json.dumps({"label": "pre-fix", "rows": rows}, indent=2), encoding="utf-8"
)
