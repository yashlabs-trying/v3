#!/usr/bin/env python3
import json, glob
trial="/home/yashs/dataforge/experiments/v3_1_baseline/jobs/deepseek2-flipt-a1/instance_flipt-io__flipt-6fe76d0__KGCvVE5/agent/mini-swe-agent.trajectory.json"
d=json.load(open(trial))
print("keys:", list(d.keys()) if isinstance(d,dict) else type(d))
msgs = d.get("messages") if isinstance(d,dict) else d
print("num messages:", len(msgs))
# print last 12 messages compactly
for m in msgs[-14:]:
    role=m.get("role")
    content=m.get("content")
    if isinstance(content,list):
        content=" ".join(str(c.get("text",c)) if isinstance(c,dict) else str(c) for c in content)
    content=(content or "")
    print(f"--- {role} ---")
    print(content[:600])
    for tc in (m.get("tool_calls") or []):
        print("  TOOLCALL:", json.dumps(tc)[:500])
