#!/usr/bin/env python3
import json, glob, os
base="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"
orig = {
 "nodebb": ("final-nodebb", 0.0),
 "flipt": ("final-flipt", 1.0),
 "vuls": ("f3-vuls-a1", 0.0),
 "openlibrary": ("f3-openlibrary-a1", 1.0),
 "teleport": ("f3-teleport-a1", 1.0),
 "ansible": ("f3-ansible-a1", 1.0),
 "elementweb": ("f3-elementweb-a1", 1.0),
}
print(f"{'task':12} {'orig':>6} {'regrade':>8}  {'agree':>6}  replay_apply_rc  exception")
for s,(job,origr) in orig.items():
    d=os.path.join(base,"regrade-"+s)
    tr=glob.glob(d+"/instance_*/result.json")
    if not tr:
        print(f"{s:12} {origr:>6} {'NONE':>8}"); continue
    t=json.load(open(tr[0]))
    vres=t.get("verifier_result") or {}
    r=(vres.get("rewards") or {}).get("reward")
    exc=(t.get("exception_info") or {}).get("exception_type")
    # replay.json from agent
    rj=glob.glob(d+"/instance_*/agent/replay.json")
    arc=None
    if rj:
        try:
            j=json.load(open(rj[0])); arc=j.get("apply_rc")
        except: pass
    agree = "yes" if (r is not None and abs(r-origr)<1e-9) else ("?" if r is None else "NO")
    print(f"{s:12} {origr:>6} {str(r):>8}  {agree:>6}  {str(arc):>8}  {exc}")
