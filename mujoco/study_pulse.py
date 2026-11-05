"""Fresh isolated MuJoCo conditions, global/pulse models and fair pulse timeout."""
import argparse
import hashlib
import json
from pathlib import Path
from calibrate_residual import conditions,simulate,save,validate_plan,digest
from config import load_config
from innovation import EventResidual
from pulse_observer import PulseObserver
from signals import SignalFrame

HERE=Path(__file__).resolve().parent

def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]

def study(plan_path,calibration,out):
    plan=json.loads(plan_path.read_text());p=validate_plan(plan["segment_plan"])
    baseline=json.loads(calibration.read_text())["settings"];base=load_config(HERE/"configs/reconfigurable_cell_20261030.json")
    out.mkdir(parents=True,exist_ok=False);save(out/"plan.json",plan)
    save(out/"source_manifest.json",{"calibration_sha256":digest(calibration),"plan_sha256":digest(plan_path),"sources":{x.name:digest(x) for x in HERE.glob('*.py')}})
    results=[]
    for group,fixtures in conditions(p)[1:]:
        for i,fixture in enumerate(fixtures):
            name=f"{group}_{i:02}";print(name,flush=True);folder=out/name
            original=simulate(folder,base,fixture,p)
            observers={"global":EventResidual(base,baseline),"pulse":PulseObserver(base,baseline,plan["length_guard_m"])}
            counts={n:{"samples":0,"covered":0,"width_sum_m":0.} for n in observers};timeout=None;seen=False;inputs={}
            for fname in ("observations.jsonl","issued_commands.jsonl","evaluator_only.jsonl"):inputs[fname]=digest(folder/fname)
            obs,cmd,truth=(rows(folder/f) for f in ("observations.jsonl","issued_commands.jsonl","evaluator_only.jsonl"))
            if not len(obs)==len(cmd)==len(truth):raise ValueError("unaligned logs")
            with (folder/"pulse_decisions.jsonl").open("w",encoding="utf-8",newline="\n") as log:
                for o,c,t in zip(obs,cmd,truth):
                    now=c["time_s"]
                    if now!=o["received_time_s"] or now!=t["time_s"]:raise ValueError("unaligned clocks")
                    frame=SignalFrame(**o);record={n:m.observe(frame,now) for n,m in observers.items()}
                    fit=observers["pulse"].fit
                    if frame.values["ps2"]:seen=True
                    if fit is not None and not seen and timeout is None:
                        d=base["geometry"]["ps_y_m"]["ps2"]-base["geometry"]["ps_y_m"]["ps1"]-base["geometry"]["product_size_m"][1]
                        # Same pulse information, point speed and a pre-existing fixed 0.2 s allowance.
                        deadline=fit["at_s"]+d/(c["command"]["long"]*fit["gain_point"])+p["fixed_timeout_slack_s"]
                        if now+1e-9>=deadline:timeout=now
                    for n,m in observers.items():
                        interval=record[n]["predicted_center_m"]
                        if interval is not None:
                            counts[n]["samples"]+=1;counts[n]["covered"]+=int(interval[0]<=t["product_xyz_m"][1]<=interval[1]);counts[n]["width_sum_m"]+=interval[1]-interval[0]
                        m.issued(now,c["command"]["long"])
                    log.write(json.dumps({"time_s":now,"observers":record})+"\n")
            results.append({"group":group,"id":name,"fixture":fixture,"onset_s":original["onset_s"],"fixed_timeout_s":original["fixed_timeout_first_s"],"pulse_timeout_s":timeout,"pulse_fit":observers["pulse"].fit,"observers":{n:{**counts[n],"first_alert":m.first_alert} for n,m in observers.items()},"input_sha256":inputs})
            save(out/"partial_results.json",results)
    groups={}
    for group in ("test_normal","test_fault","test_shift"):
        runs=[x for x in results if x["group"]==group];g={"runs":len(runs),"fixed_timeout_alerts":sum(x["fixed_timeout_s"] is not None for x in runs),"pulse_timeout_alerts":sum(x["pulse_timeout_s"] is not None for x in runs),"observers":{}}
        for n in observers:
            ms=[x["observers"][n] for x in runs];total=sum(m["samples"] for m in ms)
            deltas=[x["observers"][n]["first_alert"]["time_s"]-x["pulse_timeout_s"] for x in runs if x["observers"][n]["first_alert"] and x["pulse_timeout_s"] is not None]
            g["observers"][n]={"alerts":sum(m["first_alert"] is not None for m in ms),"covered":sum(m["covered"] for m in ms),"samples":total,"mean_width_m":sum(m["width_sum_m"] for m in ms)/total if total else None,"difference_vs_pulse_timeout_s":[min(deltas),max(deltas)] if deltas else None}
        groups[group]=g
    report={"groups":groups,"runs":results,"physical_validation":False,"scope":"Pulse length/shape guard and drift are assumed; isolated advisory segment only. No trained diagnostic ML or reconfiguration authority."}
    save(out/"results.json",report);print(json.dumps(groups),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--plan",type=Path,default=HERE/"experiments/pulse_20261105.json");p.add_argument("--calibration",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();study(a.plan,a.calibration,a.output)
