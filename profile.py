#!/usr/bin/env python3
"""Deep-dive candidate profiling for task selection."""
import json, os, re
from collections import Counter

TASKS="/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/v2/tasks"

def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return ""

rows=[]
for t in sorted(os.listdir(TASKS)):
    if not t.startswith("instance_"): continue
    base=os.path.join(TASKS,t)
    rs=read(os.path.join(base,"tests","run_script.sh"))
    cfg=read(os.path.join(base,"tests","config.json"))
    toml=read(os.path.join(base,"task.toml"))
    par=read(os.path.join(base,"tests","parser.py"))
    # repo
    m=re.match(r"instance_(?P<org>[^_]+)__(?P<repo>.+?)-[0-9a-f]{7,}",t)
    repo=f"{m.group('org')}/{m.group('repo')}" if m else "?"
    # count required tests
    def parse_list(s):
        try: return json.loads(s)
        except Exception:
            try:
                import ast; return ast.literal_eval(s)
            except Exception: return []
    f2p=parse_list((re.search(r'"fail_to_pass":\s*(".*"|\[.*?\])',cfg,re.S) or ['','[]'])[1]) if 'fail_to_pass' in cfg else []
    p2p=parse_list((re.search(r'"pass_to_pass":\s*(".*"|\[.*?\])',cfg,re.S) or ['','[]'])[1]) if 'pass_to_pass' in cfg else []
    # signals
    sig=[]
    if "|| echo" in rs: sig.append("or_echo_masks")
    if "|| true" in rs: sig.append("or_true")
    if re.search(r"timeout \d+", rs): sig.append("timeout_wrap")
    if "pytest" in rs: sig.append("pytest")
    if "go test" in rs: sig.append("gotest")
    if "jest" in rs: sig.append("jest")
    if "mocha" in rs: sig.append("mocha")
    if re.search(r"psql|postgres|pg_ctl|initdb", rs): sig.append("postgres")
    if "redis" in rs: sig.append("redis")
    if re.search(r"sleep \d", rs): sig.append("sleep")
    if re.search(r"pkill|kill ", rs): sig.append("kill")
    if re.search(r"npm install|pip install|go mod|curl |wget ", rs): sig.append("net_install")
    # parser markers
    if "ERROR" in par: sig.append("par_has_error")
    if "SKIPPED" in par: sig.append("par_has_skip")
    if "_test.go" in par or "go test" in par: sig.append("par_gotest")
    # test count magnitude
    navail = len(f2p)+len(p2p)
    rows.append({"task":t,"repo":repo,"f2p":len(f2p),"p2p":len(p2p),"ntests":navail,
                 "signals":sig,"verifier_timeout":re.search(r'timeout_sec\s*=\s*([\d.]+)',toml).group(1) if re.search(r'timeout_sec\s*=\s*([\d.]+)',toml) else "?"})

print("=== repos x signals ===")
byrepo={}
for r in rows:
    byrepo.setdefault(r["repo"],[]).append(r)

for repo in sorted(byrepo):
    rs=byrepo[repo]
    sigc=Counter()
    for r in rs:
        for s in r["signals"]: sigc[s]+=1
    print(f"\n{repo}: {len(rs)} tasks")
    print("  signals:", dict(sigc))
    # high-test-count tasks
    top=sorted(rs,key=lambda x:-x["ntests"])[:3]
    for t in top:
        print(f"    big: {t['task'][:70]} f2p={t['f2p']} p2p={t['p2p']} sig={t['signals']}")
