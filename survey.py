#!/usr/bin/env python3
"""Survey V2 tasks for selection-relevant risk characteristics."""
import json, os, re, glob
from collections import Counter, defaultdict

TASKS = "/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks"

def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

task_dirs = sorted(d for d in os.listdir(TASKS) if d.startswith("instance_"))
print(f"total tasks: {len(task_dirs)}")

# repo distribution
repo_counts = Counter()
lang_by_repo = defaultdict(set)
rows = []
for t in task_dirs:
    base = os.path.join(TASKS, t)
    # repo name: instance_<org>__<repo>-<sha>...
    m = re.match(r"instance_(?P<org>[^_]+)__(?P<repo>.+?)-[0-9a-f]{7,}", t)
    org = m.group("org") if m else "?"
    repo = m.group("repo") if m else "?"
    key = f"{org}/{repo}"
    repo_counts[key] += 1
    rs = read(os.path.join(base, "tests", "run_script.sh"))
    cfg = read(os.path.join(base, "tests", "config.json"))
    sh = read(os.path.join(base, "tests", "test.sh"))
    toml = read(os.path.join(base, "task.toml"))
    # detect language hints
    lang = []
    if re.search(r"\bgo test\b|_test\.go", rs): lang.append("go")
    if re.search(r"\bpytest\b|python", rs, re.I): lang.append("python")
    if re.search(r"\bmocha\b|\bjest\b|npm |node ", rs): lang.append("js")
    if re.search(r"\bcargo\b|rustc", rs): lang.append("rust")
    if re.search(r"\brspec\b|gem ", rs): lang.append("ruby")
    for l in lang:
        lang_by_repo[key].add(l)
    # risk signals
    signals = []
    if rs.count("|| true") >= 1: signals.append("or_true")
    if rs.count("|| echo") >= 1: signals.append("or_echo")
    if "timeout " in rs or "timeout " in sh: signals.append("timeout")
    if "pytest" in rs or "pytest" in sh: signals.append("pytest")
    if "go test" in rs: signals.append("gotest")
    if "psql" in rs or "postgres" in rs or "mysql" in rs: signals.append("db")
    if "redis" in rs: signals.append("redis")
    if "curl http" in rs or "wget " in rs or "npm install" in rs or "pip install" in rs: signals.append("network")
    if "sleep " in rs: signals.append("sleep")
    if "pkill" in rs or "kill " in rs: signals.append("kill")
    if re.search(r"\bjest\b", rs): signals.append("jest")
    if re.search(r"\bmocha\b", rs): signals.append("mocha")
    if re.search(r"\bpytest\b", rs): signals.append("pytest")
    # parser complexity: size + special handling
    psize = os.path.getsize(os.path.join(base, "tests", "parser.py")) if os.path.exists(os.path.join(base, "tests", "parser.py")) else 0
    # f2p/p2p counts
    f2p = cfg.count("|")  # rough
    rows.append({
        "task": t, "repo": key, "langs": ",".join(sorted(set(lang))),
        "signals": ",".join(signals), "parser_size": psize,
        "verifier_net": ("verifier.network" in toml, "network = \"public\"" in toml),
    })

print("\n=== repo distribution ===")
for k, v in repo_counts.most_common():
    langs = ",".join(sorted(lang_by_repo[k]))
    print(f"{v:4d}  {k:45s} [{langs}]")

print("\n=== signal distribution ===")
sig = Counter()
for r in rows:
    for s in filter(None, r["signals"].split(",")):
        sig[s] += 1
for k, v in sig.most_common():
    print(f"{v:4d}  {k}")

print("\n=== parser size buckets ===")
buckets = Counter()
for r in rows:
    b = (r["parser_size"] // 500) * 500
    buckets[b] += 1
for k in sorted(buckets):
    print(f"{k:5d}-{k+499:5d}: {buckets[k]}")

# save full survey
with open("/home/yashs/dataforge/experiments/v3_1_baseline/task_survey.json", "w") as f:
    json.dump(rows, f, indent=1)
print("\nsaved task_survey.json")
