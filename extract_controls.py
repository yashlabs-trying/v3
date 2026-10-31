#!/usr/bin/env python3
import json, glob, os
base="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
rows=[]
for d in sorted(glob.glob(base+"/ctrl-*")):
    name=os.path.basename(d)
    # job-level
    jr=os.path.join(d,"result.json")
    if not os.path.exists(jr):
        rows.append((name,"NO_JOB_RESULT",None,None)); continue
    job=json.load(open(jr))
    # find evals
    evals=job.get("stats",{}).get("evals",{})
    rewards={}
    for k,v in evals.items():
        rewards[k]=v.get("reward_stats",{}).get("reward",{})
    # trial-level reward + exception
    tr=glob.glob(d+"/instance_*/result.json")
    trial=None; exc=None; vres=None
    if tr:
        t=json.load(open(tr[0]))
        vres=t.get("verifier_result")
        exc=t.get("exception_info",{}).get("exception_type") if t.get("exception_info") else None
    print(f"{name}")
    print(f"   evals: {json.dumps(rewards)}")
    print(f"   trial_verifier_result: {json.dumps(vres)}  exception={exc}")
