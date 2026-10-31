#!/usr/bin/env python3
"""Compute Phase 1A metrics.json."""
import json, glob, os
from datetime import datetime
BASE="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"

def load(job):
    tr=glob.glob(os.path.join(BASE,job)+"/instance_*/result.json")
    if not tr: return None
    return json.load(open(tr[0]))

tasks = {
 "nodebb":"final-nodebb","flipt":"final-flipt","vuls":"f3-vuls-a1",
 "openlibrary":"f3-openlibrary-a1","teleport":"f3-teleport-a1",
 "ansible":"f3-ansible-a1","elementweb":"f3-elementweb-a1",
}

def secs(t):
    if not t: return None
    a=t.get("started_at"); b=t.get("finished_at")
    if not a or not b: return None
    try:
        return (datetime.fromisoformat(b)-datetime.fromisoformat(a)).total_seconds()
    except: return None

agent_times={}; verifier_times={}; rewards={}
for s,j in tasks.items():
    t=load(j)
    if not t: continue
    rewards[s]=(t.get("verifier_result") or {}).get("rewards",{}).get("reward")
    agent_times[s]=secs(t.get("agent_execution"))
    verifier_times[s]=secs(t.get("verifier"))

m = {
 "selected_tasks": 7,
 "tasks_successfully_executed": 6,
 "tasks_with_infrastructure_failure": 1,
 "note_infra": "nodebb original attempt: agent never ran (0 model responses); verdict invalid",
 "valid_deepseek_patches_produced": 6,
 "official_v2_passes": sum(1 for s in tasks if rewards.get(s)==1.0),
 "official_v2_failures": sum(1 for s in tasks if rewards.get(s)==0.0),
 "reference_solution_pass_rate": "7/7 (oracle=1.0 all selected tasks)",
 "empty_patch_rejection_rate": "7/7 (no-op=0.0 all selected tasks)",
 "regrade_verdict_disagreements": 0,
 "regrade_note": "all 7 regrades agreed with original reward; nodebb regrade agreed via NULL replay (apply_rc=1, nothing applied)",
 "confirmed_false_positive_verdicts": 0,
 "confirmed_false_negative_verdicts": 0,
 "suspected_false_negative_verdicts": 1,
 "suspected_false_negative_detail": "nodebb: reward 0.0 presented as model failure but agent never started; recovery rerun scored 1.0",
 "confirmed_defects": [
   "NodeBB model.patch contaminated by pre-existing untracked appendonlydir/*.rdb baked into image",
   "patch_replay silently applies nothing when patch contains only pre-existing files (null replay)",
   "mini-swe-agent unpinned resolved to 2.4.6 incompatible with V2 harness (setup wizard / cost-map crash) - mitigated, not upstream",
   "Harbor egress sidecar + streaming/multi-request interaction stalls first model call for some tasks"
 ],
 "suspected_defects": [
   "agent edits to test files are reverted before grading (observed vuls edited models/vulninfos_test.go) - correct per V2 design, but changes measured scope",
   "Harbor agent_result reports 0 tokens/cost for DeepInfra (cost not captured)"
 ],
 "infrastructure_errors": 1,
 "agent_execution_seconds": agent_times,
 "verifier_seconds": verifier_times,
 "rewards": rewards,
 "repeat_control_stability": {"flipt_oracle": [1.0,1.0,1.0], "verdict":"stable"},
 "nodebb_recovery_rerun": {"counted": False, "reward": 1.0, "note":"separately labeled; not the original attempt"},
}
with open("/home/yashs/dataforge/experiments/v3_1_baseline/metrics.json","w") as f:
    json.dump(m,f,indent=1)
print(json.dumps(m,indent=1)[:2500])
