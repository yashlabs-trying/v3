#!/usr/bin/env python3
"""Consolidate all Phase 1A results into results.json / results.csv."""
import json, glob, os, subprocess, csv

BASE="/home/yashs/dataforge/experiments/v3_1_baseline/jobs"

# short -> (task_id, repo, lang, original_job, counted=True)
TASKS = [
 ("nodebb","instance_NodeBB__NodeBB-00c70ce7b0541cfc94afe567921d7668cdc8f4ac-vnan","NodeBB/NodeBB","JavaScript/mocha","final-nodebb"),
 ("flipt","instance_flipt-io__flipt-6fe76d024ee0c50ddb09c86f4ae0bd4c208fd65f","flipt-io/flipt","Go","final-flipt"),
 ("vuls","instance_future-architect__vuls-f0b3a8b1db98eb1bd32685f1c36c41a99c3452ed","future-architect/vuls","Go","f3-vuls-a1"),
 ("openlibrary","instance_internetarchive__openlibrary-03095f2680f7516fca35a58e665bf2a41f006273-v8717e18970bcdc4e0d2cea3b1527752b21e74866","internetarchive/openlibrary","Python/pytest","f3-openlibrary-a1"),
 ("teleport","instance_gravitational__teleport-46aa81b1ce96ebb4ebed2ae53fd78cd44a05da6c-vee9b09fb20c43af7e520f57e9239bbcf46b7113d","gravitational/teleport","Go","f3-teleport-a1"),
 ("ansible","instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad","ansible/ansible","Python/pytest","f3-ansible-a1"),
 ("elementweb","instance_element-hq__element-web-aec454dd6feeb93000380523cbb0b3681c0275fd-vnan","element-hq/element-web","TypeScript/jest","f3-elementweb-a1"),
]

def job_info(job):
    d=os.path.join(BASE,job)
    tr=glob.glob(d+"/instance_*/result.json")
    out={"exists":bool(tr)}
    if not tr: return out
    t=json.load(open(tr[0]))
    out["reward"]=(t.get("verifier_result") or {}).get("rewards",{}).get("reward")
    out["exception"]=(t.get("exception_info") or {}).get("exception_type")
    out["agent_exec"]=t.get("agent_execution")
    out["verifier"]=t.get("verifier")
    p=glob.glob(d+"/instance_*/agent/model.patch")
    out["patch_bytes"]=os.path.getsize(p[0]) if p else 0
    out["patch_files"]=[]
    if p and out["patch_bytes"]>0:
        out["patch_files"]=[x.split(" b/")[-1] for x in subprocess.run(["grep","^diff --git",p[0]],capture_output=True,text=True).stdout.strip().splitlines()]
    trj=glob.glob(d+"/instance_*/agent/mini-swe-agent.trajectory.json")
    out["traj_msgs"]=len(json.load(open(trj[0])).get("messages",[])) if trj else 0
    return out

def regrade_info(s):
    d=os.path.join(BASE,"regrade-"+s)
    tr=glob.glob(d+"/instance_*/result.json")
    if not tr: return {"reward":"NOT MEASURED"}
    t=json.load(open(tr[0]))
    rj=glob.glob(d+"/instance_*/agent/replay.json")
    arc=None
    if rj:
        try: arc=json.load(open(rj[0])).get("apply_rc")
        except: pass
    return {"reward":(t.get("verifier_result") or {}).get("rewards",{}).get("reward"),"apply_rc":arc}

results=[]
for short,tid,repo,lang,job in TASKS:
    oi=job_info(job); rg=regrade_info(short)
    src=[f for f in oi.get("patch_files",[]) if not f.startswith("appendonlydir/")]
    results.append({
        "task":short,"task_id":tid,"repo":repo,"language":lang,
        "original_job":job,"original_reward":oi.get("reward"),
        "exception":oi.get("exception"),
        "patch_bytes":oi.get("patch_bytes"),"source_files_changed":len(src),
        "source_files":src,"patch_contaminated_redis":any(f.startswith("appendonlydir/") for f in oi.get("patch_files",[])),
        "traj_msgs":oi.get("traj_msgs"),
        "agent_exec":oi.get("agent_exec"),"verifier":oi.get("verifier"),
        "regrade_reward":rg.get("reward"),"regrade_apply_rc":rg.get("apply_rc"),
    })

# add the recovery rerun (separate, not counted)
rec=job_info("nodebb-recovery")
recrg=regrade_info("nodebb-recovery")
results.append({"task":"nodebb-recovery(rerun,NOT counted)","task_id":TASKS[0][1],"repo":"NodeBB/NodeBB","language":"JavaScript/mocha",
 "original_job":"nodebb-recovery","original_reward":rec.get("reward"),"exception":rec.get("exception"),
 "patch_bytes":rec.get("patch_bytes"),"source_files_changed":len([f for f in rec.get("patch_files",[]) if not f.startswith("appendonlydir/")]),
 "source_files":[f for f in rec.get("patch_files",[]) if not f.startswith("appendonlydir/")],
 "patch_contaminated_redis":any(f.startswith("appendonlydir/") for f in rec.get("patch_files",[])),
 "traj_msgs":rec.get("traj_msgs"),"agent_exec":rec.get("agent_exec"),"verifier":rec.get("verifier"),
 "regrade_reward":recrg.get("reward"),"regrade_apply_rc":recrg.get("apply_rc")})

with open("/home/yashs/dataforge/experiments/v3_1_baseline/results.json","w") as f:
    json.dump(results,f,indent=1)

cols=["task","repo","language","original_reward","exception","patch_bytes","source_files_changed","traj_msgs","regrade_reward","regrade_apply_rc"]
with open("/home/yashs/dataforge/experiments/v3_1_baseline/results.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader()
    for r in results: w.writerow(r)

for r in results:
    print(f"{r['task']:32} reward={str(r['original_reward']):5} regrade={str(r['regrade_reward']):5} apply_rc={r['regrade_apply_rc']} patch={r['patch_bytes']}B srcfiles={r['source_files_changed']} msgs={r['traj_msgs']} exc={r['exception']}")
