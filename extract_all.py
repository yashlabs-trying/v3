#!/usr/bin/env python3
import json, glob, os, subprocess
base="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
jobs = {
 "nodebb": "final-nodebb",
 "flipt": "final-flipt",
 "vuls": "f3-vuls-a1",
 "openlibrary": "f3-openlibrary-a1",
 "teleport": "f3-teleport-a1",
 "ansible": "f3-ansible-a1",
 "elementweb": "f3-elementweb-a1",
}
for name,job in jobs.items():
    d=os.path.join(base,job)
    print(f"===== {name} ({job}) =====")
    tr=glob.glob(d+"/instance_*/result.json")
    if not tr: print("  NO RESULT"); continue
    t=json.load(open(tr[0]))
    print("  reward:", json.dumps(t.get("verifier_result")))
    print("  exception:", (t.get("exception_info") or {}).get("exception_type"))
    ae=t.get("agent_execution"); vf=t.get("verifier")
    print("  agent_exec:", ae)
    print("  verifier:", vf)
    p=glob.glob(d+"/instance_*/agent/model.patch")
    ps=os.path.getsize(p[0]) if p else 0
    print("  patch bytes:", ps)
    srcs=[]
    if p and ps>0:
        diffs=subprocess.run(["grep","^diff --git",p[0]],capture_output=True,text=True).stdout.strip().splitlines()
        srcs=[x.split(' b/')[-1] for x in diffs]
        print("  files changed:", len(srcs))
        for x in srcs[:6]: print("     ", x)
    trj=glob.glob(d+"/instance_*/agent/mini-swe-agent.trajectory.json")
    if trj:
        try: print("  trajectory msgs:", len(json.load(open(trj[0])).get("messages",[])))
        except: pass
    ts=glob.glob(d+"/instance_*/verifier/test-stdout.txt")
    if ts:
        lines=open(ts[0]).read().splitlines()
        for l in lines[-6:]: print("   | "+l)
    print()
