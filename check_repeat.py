#!/usr/bin/env python3
import json, glob, os
BASE="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
print("=== repeat oracle controls (flipt) ===")
for j in ["ctrl-oracle-flipt-6fe76d024ee0c50","repeat-oracle-flipt-2","repeat-oracle-flipt-3","audit-oracle-flipt"]:
    d=os.path.join(BASE,j)
    tr=glob.glob(d+"/instance_*/result.json")
    if not tr: print(f"{j}: NOT FOUND"); continue
    t=json.load(open(tr[0]))
    r=(t.get("verifier_result") or {}).get("rewards",{}).get("reward")
    print(f"  {j:34} reward={r}")
print()
print("=== vuls partial pass detail ===")
d=os.path.join(BASE,"f3-vuls-a1")
ts=glob.glob(d+"/instance_*/verifier/test-stdout.txt")
if ts:
    for l in open(ts[0]).read().splitlines():
        if "Required" in l or "Passed" in l or "RESULT" in l or "Missing" in l:
            print("  "+l)
