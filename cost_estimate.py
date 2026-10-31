#!/usr/bin/env python3
"""Estimate DeepSeek cost from captured trajectories (rough token proxy)."""
import json, glob, os
BASE="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
jobs = {"nodebb":"final-nodebb","flipt":"final-flipt","vuls":"f3-vuls-a1",
 "openlibrary":"f3-openlibrary-a1","teleport":"f3-teleport-a1",
 "ansible":"f3-ansible-a1","elementweb":"f3-elementweb-a1","nodebb-recovery":"nodebb-recovery"}
# DeepInfra DeepSeek-V4.1-Flash observed pricing: ~$0.20/M input, blended. Use $0.27/M in, $1.10/M out as rough.
IN_RATE=0.27/1_000_000; OUT_RATE=1.10/1_000_000
total_in=0; total_out=0
rows=[]
for s,j in jobs.items():
    x=glob.glob(os.path.join(BASE,j)+"/instance_*/agent/mini-swe-agent.trajectory.json")
    if not x: continue
    try: msgs=json.load(open(x[0])).get("messages",[])
    except: continue
    chars=sum(len(json.dumps(m)) for m in msgs)
    approx_in=chars//4  # ~4 chars/token, upper bound on context
    approx_out=sum(len(json.dumps(m)) for m in msgs if m.get("role")=="assistant")//4
    total_in+=approx_in; total_out+=approx_out
    rows.append((s,len(msgs),approx_in,approx_out))
for r in rows:
    print(f"{r[0]:16} msgs={r[1]:4} approx_in_tokens={r[2]:>9} approx_out_tokens={r[3]:>8}")
cost=total_in*IN_RATE+total_out*OUT_RATE
print(f"\nTOTAL approx_in={total_in} approx_out={total_out} estimated_cost_usd=${cost:.2f}")
print("Note: rough proxy; DeepInfra per-call estimated_cost was available but not aggregated by Harbor (agent_result=0).")
