#!/usr/bin/env python3
import json, glob, os
base="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
for d in sorted(glob.glob(base+"/deepseek-*")):
    name=os.path.basename(d)
    tr=glob.glob(d+"/instance_*/result.json")
    if not tr:
        print(f"{name}: NOT DONE"); continue
    t=json.load(open(tr[0]))
    vres=t.get("verifier_result")
    exc=t.get("exception_info",{}).get("exception_type") if t.get("exception_info") else None
    ag=t.get("agent_result") or {}
    patch=glob.glob(d+"/instance_*/agent/model.patch")
    psize=os.path.getsize(patch[0]) if patch else 0
    print(f"{name}")
    print(f"   verifier: {json.dumps(vres)}  exception={exc}")
    print(f"   patch_bytes={psize}  tokens in/out={ag.get('n_input_tokens')}/{ag.get('n_output_tokens')} cost={ag.get('cost_usd')}")
