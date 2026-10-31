#!/usr/bin/env python3
import json, glob, os
base="/home/yashs/dataforge/experiments/v3_1_baseline/upstream_lf/jobs/pilot-deepseek-2"
tr=glob.glob(base+"/instance_*/result.json")[0]
r=json.load(open(tr))
print("trial result keys:", list(r.keys()))
print("verifier_result:", json.dumps(r.get("verifier_result"), indent=1))
print()
job=json.load(open(base+"/result.json"))
print("job result keys:", list(job.keys()))
print(json.dumps(job, indent=1)[:2000])
