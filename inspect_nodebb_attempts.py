#!/usr/bin/env python3
import json, glob, os
base="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
for job in ["ds-nodebb-a1","ds-nodebb-a2"]:
    d=os.path.join(base,job)
    if not os.path.isdir(d):
        print(f"{job}: missing"); continue
    tr=glob.glob(d+"/instance_*/result.json")
    print(f"=== {job} ===")
    if not tr:
        print("  no trial result"); continue
    t=json.load(open(tr[0]))
    print("  reward:", json.dumps(t.get("verifier_result")))
    print("  exception:", (t.get("exception_info") or {}).get("exception_type"))
    print("  agent_exec:", t.get("agent_execution"))
    print("  verifier:", t.get("verifier"))
    patch=glob.glob(d+"/instance_*/agent/model.patch")
    print("  patch bytes:", os.path.getsize(patch[0]) if patch else 0)
    for tf in glob.glob(d+"/instance_*/agent/*trajectory*.json"):
        try:
            j=json.load(open(tf))
            n=len(j.get("messages",[])) if isinstance(j,dict) else len(j)
        except Exception as e:
            n=f"unreadable:{e}"
        print(f"  {os.path.basename(tf)}: messages={n}")
    # verifier test-stdout
    ts=glob.glob(d+"/instance_*/verifier/test-stdout.txt")
    if ts:
        print("  --- verifier test-stdout tail ---")
        print("  " + "\n  ".join(open(ts[0]).read().splitlines()[-12:]))
