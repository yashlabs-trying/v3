#!/usr/bin/env python3
import json, glob, os
d="/home/yashs/dataforge/experiments/v3_1_baseline/jobs/final-nodebb"
tr=glob.glob(d+"/instance_*/agent/*trajectory*.json")
print("trajectory files:", [os.path.basename(x) for x in tr])
for x in tr:
    try:
        j=json.load(open(x))
        msgs=j.get("messages",[]) if isinstance(j,dict) else j
        print(f"\n=== {os.path.basename(x)}: {len(msgs)} messages ===")
        for m in msgs[-10:]:
            role=m.get("role")
            c=m.get("content")
            if isinstance(c,list): c=" ".join(str(p.get("text",p)) if isinstance(p,dict) else str(p) for p in c)
            print(f"--- {role} ---")
            print((c or "")[:500])
            for tc in (m.get("tool_calls") or []): print("  TOOL:", json.dumps(tc)[:300])
    except Exception as e:
        print(x,"ERR",e)
# transcript size
ts=glob.glob(d+"/instance_*/agent/mini-swe-agent.txt")
if ts: print("\nmini-swe-agent.txt size:", os.path.getsize(ts[0]))
