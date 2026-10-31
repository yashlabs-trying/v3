#!/usr/bin/env python3
import json, glob, os
base="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
for job in ["final-nodebb","final-flipt"]:
    d=os.path.join(base,job)
    tr=glob.glob(d+"/instance_*/result.json")
    print(f"===== {job} =====")
    if not tr:
        print("  no trial result"); continue
    t=json.load(open(tr[0]))
    print("  reward:", json.dumps(t.get("verifier_result")))
    print("  exception:", (t.get("exception_info") or {}).get("exception_type"))
    print("  agent_exec:", t.get("agent_execution"))
    print("  verifier:", t.get("verifier"))
    patch=glob.glob(d+"/instance_*/agent/model.patch")
    ps=os.path.getsize(patch[0]) if patch else 0
    print("  patch bytes:", ps)
    if patch and ps>0:
        import subprocess
        diffs=subprocess.run(["grep","^diff --git",patch[0]],capture_output=True,text=True).stdout.strip().splitlines()
        print("  files in patch:")
        for x in diffs[:20]: print("    ", x)
    trj=glob.glob(d+"/instance_*/agent/*trajectory*.json")
    for x in trj:
        try:
            j=json.load(open(x)); print(f"  {os.path.basename(x)}: messages={len(j.get('messages',[])) if isinstance(j,dict) else len(j)}")
        except Exception as e: print("  traj err", e)
    ts=glob.glob(d+"/instance_*/verifier/test-stdout.txt")
    if ts:
        print("  --- verifier test-stdout tail ---")
        for l in open(ts[0]).read().splitlines()[-10:]: print("    "+l)
    print()
