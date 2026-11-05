"""Scheduled network replay with explicit evidence validity and alarm attribution."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from config import load_config,exact_keys,number
from pulse_observer import PulseObserver
from signals import SignalFrame
from calibrate_residual import save,digest
from study_pulse import rows

HERE=Path(__file__).resolve().parent

def replay(obs,commands,settings,guard,case):
    if len(obs)!=len(commands) or not obs:raise ValueError("nonempty aligned recordings required")
    exact_keys(case,("delay_ticks","drop_source_s"),"network fixture")
    if type(case["delay_ticks"]) is not int or not 0<=case["delay_ticks"]<=100:raise ValueError("bounded nonnegative delay required")
    drop=case["drop_source_s"]
    if drop is not None:
        if not isinstance(drop,list) or len(drop)!=2:raise ValueError("drop interval required")
        for t in drop:number(t,"drop time",0)
        if drop[1]<drop[0]:raise ValueError("ordered drop interval required")
    speed=commands[0]["command"]["long"]
    if speed<=0 or any(c["command"]["long"]!=speed or c["time_s"]!=o["source_time_s"] for o,c in zip(obs,commands)):raise ValueError("constant forward source-clock recording required")
    observer=PulseObserver(load_config(HERE/"configs/reconfigurable_cell_20261030.json"),settings,guard)
    result={"first_residual_s":None,"first_timeout_s":None,"first_combined":None,"unusable_after_fit_ticks":0,"usable_ticks":0,"never_fit":True}
    seen=False;records=[];delivered=0;dropped=0
    for i,c in enumerate(commands):
        now=c["time_s"];j=i-case["delay_ticks"];frame=None
        if j>=0:
            o=obs[j];drop=case["drop_source_s"]
            if drop is not None and drop[0]-1e-9<=o["source_time_s"]<=drop[1]+1e-9:dropped+=1
            else:
                frame=replace(SignalFrame(**o),received_time_s=now);delivered+=1
        record=observer.observe(frame,now);fit=observer.fit;timeout=False;kind=None
        if fit is not None:
            result["never_fit"]=False
            if not record["usable_for_monitoring"]:
                result["unusable_after_fit_ticks"]+=1;kind="transport_or_edge_history_unusable"
            else:
                result["usable_ticks"]+=1
                if frame.values["ps2"]:seen=True
                g=observer.core.config["geometry"];d=g["ps_y_m"]["ps2"]-g["ps_y_m"]["ps1"]-g["product_size_m"][1]
                deadline=fit["at_s"]+d/(c["command"]["long"]*fit["gain_point"])+.2
                # Absence only established through the delivered source timestamp, not receiver wall clock.
                timeout=not seen and frame.source_time_s+1e-9>=deadline
                if record["alert"]:
                    kind="model_residual"
                    if result["first_residual_s"] is None:result["first_residual_s"]=now
                if timeout:
                    if result["first_timeout_s"] is None:result["first_timeout_s"]=now
                    if kind is None:kind="pulse_timeout_only"
        elif frame is not None and now-frame.source_time_s>observer.core.config["timing"]["max_age_s"]+1e-9:
            kind="stale_transport_no_fit"
        if kind and result["first_combined"] is None:result["first_combined"]={"time_s":now,"evidence":kind}
        records.append({"time_s":now,"observer":record,"timeout":timeout,"evidence":kind})
        observer.issued(now,c["command"]["long"])
    result.update(delivered=delivered,dropped=dropped,delayed_tail_not_observed=min(case["delay_ticks"],len(obs)))
    return result,records

def study(source,plan_path,out):
    p=json.loads(plan_path.read_text());original=json.loads((source/"results.json").read_text());oldplan=json.loads((source/"plan.json").read_text())
    settings={"gain_bounds":[.8,1.2],"drift_m_s":oldplan["segment_plan"]["drift_m_s"],"confirm_samples":2}
    out.mkdir(parents=True,exist_ok=False);save(out/"plan.json",p)
    manifest={"plan_sha256":digest(plan_path),"sources":{n:digest(HERE/n) for n in ("study_pulse_network.py","pulse_observer.py","innovation.py","command_history.py","signals.py")},"inputs":{}}
    allruns=[]
    for trial in original["runs"]:
        folder=source/trial["id"];obs=rows(folder/"observations.jsonl");commands=rows(folder/"issued_commands.jsonl")
        for name in ("observations.jsonl","issued_commands.jsonl"):manifest["inputs"][trial["id"]+"/"+name]=digest(folder/name)
        for case,options in p["cases"].items():
            summary,records=replay(obs,commands,settings,oldplan["length_guard_m"],options)
            allruns.append({"trial":trial["id"],"group":trial["group"],"case":case,**summary})
            with (out/(trial["id"]+"_"+case+".jsonl")).open("w",encoding="utf-8",newline="\n") as f:
                for row in records:f.write(json.dumps(row)+"\n")
    groups={}
    for case in p["cases"]:
        groups[case]={}
        for group in ("test_normal","test_fault","test_shift"):
            rs=[r for r in allruns if r["case"]==case and r["group"]==group]
            groups[case][group]={"runs":len(rs),"model_alerts":sum(r["first_residual_s"] is not None for r in rs),"timeout_alerts":sum(r["first_timeout_s"] is not None for r in rs),"combined_alerts":sum(r["first_combined"] is not None for r in rs),"never_fit":sum(r["never_fit"] for r in rs),"history_rejected_runs":sum(r["unusable_after_fit_ticks"]>0 for r in rs)}
    save(out/"manifest.json",manifest);save(out/"results.json",{"groups":groups,"runs":allruns,"scope":p["scope"],"physical_validation":False})
    print(json.dumps(groups),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--plan",type=Path,default=HERE/"experiments/pulse_network_20261105.json");p.add_argument("--output",type=Path,required=True);a=p.parse_args();study(a.source,a.plan,a.output)
