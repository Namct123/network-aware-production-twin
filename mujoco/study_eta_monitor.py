"""Frozen ETA monitoring, paired normal/fault segments and scheduled packet replay."""
import argparse
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from calibrate_residual import save,digest,simulate
from config import load_config,exact_keys,number
from eta_monitor import EtaEventMonitor
from signals import SignalFrame
from study_pulse import rows

HERE=Path(__file__).resolve().parent


def replay(obs,commands,config,model,settings,method,case,anchor):
    exact_keys(case,("delay_ticks","gap_after_pulse_s","target_unavailable_after_pulse_s"),"ETA network case")
    if type(case["delay_ticks"]) is not int or not 0<=case["delay_ticks"]<=100:raise ValueError("bounded delay required")
    gap=case["gap_after_pulse_s"];lost=case["target_unavailable_after_pulse_s"]
    if gap is not None:
        if not isinstance(gap,list) or len(gap)!=2:raise ValueError("gap pair required")
        for v in gap:number(v,"gap offset",0)
        if gap[1]<gap[0]:raise ValueError("ordered gap required")
    if lost is not None:number(lost,"quality loss offset",0)
    if not obs or len(obs)!=len(commands) or any(o["source_time_s"]!=c["time_s"] for o,c in zip(obs,commands)):raise ValueError("aligned recordings required")
    monitor=EtaEventMonitor(config,model,settings,method);records=[];active=late_checks=fallback=unusable=0
    for i,c in enumerate(commands):
        now=c["time_s"];j=i-case["delay_ticks"];frame=None
        if j>=0:
            o=obs[j];t=o["source_time_s"]
            if not (gap is not None and anchor+gap[0]-1e-9<=t<=anchor+gap[1]+1e-9):
                frame=replace(SignalFrame(**o),received_time_s=now)
                if lost is not None and t>=anchor+lost-1e-9:
                    frame=replace(frame,values={**frame.values,"ps2":None},quality={**frame.quality,"ps2":"unavailable"})
        record=monitor.observe(frame,now)
        if record["basis"] is not None:
            active+=1;fallback+=record["basis"]=="engineering_pulse_fallback"
            interval=record["eta_interval_s"]
            late_checks+=interval is not None and frame.source_time_s>interval[1]+1e-9
        elif monitor.pulse.fit is not None:unusable+=1
        records.append(record);monitor.issued(now,c["command"]["long"])
    return {"first_alert":monitor.first_alert,"active_ticks":active,"late_check_ticks":late_checks,"fallback_ticks":fallback,
            "unusable_after_fit_ticks":unusable,"never_fit":monitor.pulse.fit is None,"absence_confirmation_opportunity":late_checks>=settings["confirm_samples"],"delayed_tail_not_observed":min(case["delay_ticks"],len(obs)),"outside_training_feature_box":monitor.outside},records


def study(source,plan_path,out):
    plan=json.loads(plan_path.read_text());config=load_config(HERE/"configs/reconfigurable_cell_20261030.json")
    if plan["kind"]!="eta_event_monitor_study_v1" or plan["methods"]!=["pulse","constant","ml"]:raise ValueError("frozen three-method comparison required")
    model_path=HERE/"models/eta_residual_v1.json";settings_path=HERE/"models/eta_monitor_v1.json"
    model=json.loads(model_path.read_text());settings=json.loads(settings_path.read_text())
    if settings["model_sha256"]!=digest(model_path):raise ValueError("model/settings pairing changed")
    out.mkdir(parents=True,exist_ok=False);save(out/"plan.json",plan);save(out/"frozen_settings.json",settings)
    manifest={"source_files":{p.name:digest(p) for p in HERE.glob('*.py')},"model_sha256":digest(model_path),"settings_sha256":digest(settings_path),"plan_sha256":digest(plan_path),"inputs":{}}
    segment=json.loads((HERE/"experiments/interval_calibration_20261105.json").read_text())
    trials=[]
    for group in ("test","shift"):
        for e in json.loads((source/(group+"_examples.json")).read_text()):
            original=source/e["id"];fixture=json.loads((original/"plant_fixture.json").read_text())
            for fault in (["none","target_missing","drive_stall"] if group=="test" else ["none"]):
                name=e["id"]+"_"+fault;folder=original;onset=None
                if fault!="none":
                    folder=out/name;base=deepcopy(config)
                    base["reconfiguration"]["degraded_long_speed_m_s"]=min(base["reconfiguration"]["degraded_long_speed_m_s"],fixture["speed"])
                    summary=simulate(folder,base,{**fixture,"fault":fault},segment);onset=summary["onset_s"]
                obs,commands=(rows(folder/n) for n in ("observations.jsonl","issued_commands.jsonl"))
                for n in ("observations.jsonl","issued_commands.jsonl"):manifest["inputs"][name+"/"+n]=digest(folder/n)
                for case,options in plan["cases"].items():
                    for method in plan["methods"]:
                        result,records=replay(obs,commands,config,model,settings,method,options,e["available_at_s"])
                        trials.append({"id":name,"group":group,"fault":fault,"case":case,"method":method,"onset_s":onset,**result})
                        with (out/(name+"_"+case+"_"+method+".jsonl")).open("w",encoding="utf-8",newline="\n") as log:
                            for row in records:log.write(json.dumps(row,allow_nan=False)+"\n")
    groups={}
    for case in plan["cases"]:
        groups[case]={}
        for method in plan["methods"]:
            groups[case][method]={}
            for group,fault in [("test","none"),("test","target_missing"),("test","drive_stall"),("shift","none")]:
                rs=[v for v in trials if (v["case"],v["method"],v["group"],v["fault"])==(case,method,group,fault)]
                groups[case][method][group+"_"+fault]={"runs":len(rs),"alerts":sum(v["first_alert"] is not None for v in rs),"active_runs":sum(v["active_ticks"]>0 for v in rs),"data_rejected_runs":sum(v["unusable_after_fit_ticks"]>0 or v["never_fit"] for v in rs),"fallback_runs":sum(v["fallback_ticks"]>0 for v in rs),"never_fit":sum(v["never_fit"] for v in rs),"no_alert_without_confirmation_window":sum(v["first_alert"] is None and not v["absence_confirmation_opportunity"] for v in rs) if fault!="none" else None}
    differences=[]
    for v in trials:
        if v["method"]!="ml" or v["fault"]=="none" or not v["first_alert"] or v["first_alert"]["basis"]!="eta_ml":continue
        other=next(x for x in trials if (x["id"],x["case"],x["method"])==(v["id"],v["case"],"constant"))
        if other["first_alert"] and other["first_alert"]["basis"]=="eta_constant":differences.append({"id":v["id"],"case":v["case"],"ml_minus_constant_s":v["first_alert"]["time_s"]-other["first_alert"]["time_s"]})
    # Equal input hashes are observable ambiguity, not successful fault isolation.
    identical_pairs=sum(all(manifest["inputs"][f"test_{i:02}_target_missing/"+n]==manifest["inputs"][f"test_{i:02}_drive_stall/"+n] for n in ("observations.jsonl","issued_commands.jsonl")) for i in range(9))
    report={"groups":groups,"runs":trials,"paired_alert_differences":differences,"identical_missing_stall_pairs":identical_pairs,"recordings":31,"replays":len(trials),"new_mujoco_segments":18,"physical_validation":False,"parameter_tuning":False,"scope":plan["scope"]}
    save(out/"manifest.json",manifest);save(out/"results.json",report)
    print(json.dumps({"groups":groups,"replays":len(trials),"identical_pairs":identical_pairs}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--plan",type=Path,default=HERE/"experiments/eta_monitor_20261106.json");p.add_argument("--output",type=Path,required=True);a=p.parse_args();study(a.source,a.plan,a.output)
