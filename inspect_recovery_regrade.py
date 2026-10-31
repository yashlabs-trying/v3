#!/usr/bin/env python3
import json, glob, os
d="/home/yashs/dataforge/experiments/v3_1_baseline/jobs/regrade-nodebb-recovery"
tr=glob.glob(d+"/instance_*/result.json")
if not tr: print("NO RESULT"); raise SystemExit
t=json.load(open(tr[0]))
print("regrade reward:", json.dumps(t.get("verifier_result")))
print("exception:", (t.get("exception_info") or {}).get("exception_type"))
rj=glob.glob(d+"/instance_*/agent/replay.json")
if rj:
    j=json.load(open(rj[0]))
    print("apply_rc:", j.get("apply_rc"))
    print("post_apply_diffstat:", (j.get("post_apply_diffstat") or "")[:400])
ts=glob.glob(d+"/instance_*/verifier/test-stdout.txt")
if ts:
    print("--- verifier tail ---")
    print("\n".join(open(ts[0]).read().splitlines()[-10:]))
