#!/usr/bin/env python3
import json, glob, os
d="/home/yashs/dataforge/experiments/v3_1_baseline/jobs/auditcfg-vuls"
x=glob.glob(d+"/instance_*/agent/mini-swe-agent.trajectory.json")[0]
j=json.load(open(x))
msgs=j.get("messages",[])
print("messages:", len(msgs))
for i,m in enumerate(msgs):
    role=m.get("role")
    c=m.get("content")
    if isinstance(c,list): c=" ".join(str(p.get("text",p)) if isinstance(p,dict) else str(p) for p in c)
    c=(c or "")
    if role=="assistant":
        print(f"\n[{i}] ASSISTANT:")
        print(c[:400])
        for tc in (m.get("tool_calls") or []):
            fn=tc.get("function",{})
            print("   TOOL:", fn.get("name"), (fn.get("arguments") or "")[:200])
    elif role=="tool":
        print(f"[{i}] TOOL RESULT: {c[:200]}")
# also the exit tail of transcript
tt=glob.glob(d+"/instance_*/agent/mini-swe-agent.txt")
if tt:
    print("\n===== transcript tail 25 =====")
    print("\n".join(open(tt[0]).read().splitlines()[-25:]))
