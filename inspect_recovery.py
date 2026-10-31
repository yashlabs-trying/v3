#!/usr/bin/env python3
import json, glob, os, subprocess
d="/home/yashs/dataforge/experiments/v3_1_baseline/jobs/nodebb-recovery"
tr=glob.glob(d+"/instance_*/result.json")
if not tr:
    print("NO RESULT"); raise SystemExit
t=json.load(open(tr[0]))
print("reward:", json.dumps(t.get("verifier_result")))
print("exception:", (t.get("exception_info") or {}).get("exception_type"))
print("agent_exec:", t.get("agent_execution"))
print("verifier:", t.get("verifier"))
p=glob.glob(d+"/instance_*/agent/model.patch")
ps=os.path.getsize(p[0]) if p else 0
print("patch bytes:", ps)
if p and ps>0:
    diffs=subprocess.run(["grep","^diff --git",p[0]],capture_output=True,text=True).stdout.strip().splitlines()
    print("files changed:", len(diffs))
    for x in diffs[:20]: print("   ", x.split(' b/')[-1])
trj=glob.glob(d+"/instance_*/agent/mini-swe-agent.trajectory.json")
if trj: print("trajectory msgs:", len(json.load(open(trj[0])).get("messages",[])))
ts=glob.glob(d+"/instance_*/verifier/test-stdout.txt")
if ts:
    print("--- verifier tail ---")
    print("\n".join(open(ts[0]).read().splitlines()[-12:]))
