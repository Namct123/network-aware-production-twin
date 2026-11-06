"""Factorial clock/age-gate ablation with a frozen constant residual predictor."""
import argparse
from copy import deepcopy
from dataclasses import replace
import itertools
import json
from pathlib import Path
from calibrate_residual import simulate,save,digest
from config import load_config,validate_config,exact_keys,number
from eta_monitor import EtaEventMonitor
from event_window import EventWindow
from signals import SignalFrame
from study_pulse import rows
HERE=Path(__file__).resolve().parent


def replay(obs,commands,config,model,settings,policy,case,anchor):
    exact_keys(policy,("clock","age_gate"),"clock policy");exact_keys(case,("delay_ticks","gap_after_pulse_s"),"network case")
    if policy["clock"] not in ("source","receiver") or type(policy["age_gate"]) is not bool:raise ValueError("explicit clock and age gate required")
    delay=case["delay_ticks"];gap=case["gap_after_pulse_s"]
    if type(delay) is not int or not 0<=delay<=100:raise ValueError("bounded delay required")
    if gap is not None:
        if not isinstance(gap,list) or len(gap)!=2:raise ValueError("gap pair required")
        for v in gap:number(v,"gap offset",0)
        if gap[1]<gap[0]:raise ValueError("ordered gap required")
    if not obs or len(obs)!=len(commands) or any(o["source_time_s"]!=c["time_s"] for o,c in zip(obs,commands)):raise ValueError("aligned nonempty source recordings required")
    speeds={c["command"]["long"] for c in commands}
    if len(speeds)!=1 or min(speeds)<=0:raise ValueError("constant forward command required")
    cfg=deepcopy(config);period=cfg["timing"]["physics_step_s"]*cfg["timing"]["sample_steps"]
    if not policy["age_gate"]:cfg["timing"]["max_age_s"]=max(cfg["timing"]["max_age_s"],commands[-1]["time_s"]+(delay+1)*period)
    validate_config(cfg)
    predictor=EtaEventMonitor(cfg,model,settings,"constant");window=None;first=None;records=[];active=unusable=fallback=0;last_source=None
    # Drain existing packets only; never invent source samples beyond the recording.
    for i in range(len(obs)+delay):
        now=commands[i]["time_s"] if i<len(commands) else commands[-1]["time_s"]+(i-len(commands)+1)*period
        j=i-delay;frame=None
        if 0<=j<len(obs):
            o=obs[j];t=o["source_time_s"]
            if gap is None or not anchor+gap[0]-1e-9<=t<=anchor+gap[1]+1e-9:frame=replace(SignalFrame(**o),received_time_s=now)
        p=predictor.observe(frame,now)
        record={"time_s":now,"source_time_s":frame.source_time_s if frame else None,"comparison_time_s":None,"basis":None,"finding":None,"alert":False,"eta_interval_s":p["eta_interval_s"],"data_issue":p["data_issue"]}
        if p["basis"]=="eta_constant":
            if window is None:window=EventWindow(p["eta_interval_s"],predictor.pulse.fit["at_s"],settings["confirm_samples"])
            clock=frame.source_time_s if policy["clock"]=="source" else now
            outcome=window.observe(clock,frame.values["ps2"])
            record.update(outcome,comparison_time_s=clock,basis="eta_constant");active+=1;last_source=frame.source_time_s
            if outcome["alert"] and first is None:first={"time_s":now,"source_time_s":frame.source_time_s,"comparison_time_s":clock,"finding":outcome["finding"],"window_upper_s":window.interval[1]}
        else:
            if window is not None:window.observe(None,None,eligible=False)
            if p["basis"]=="engineering_pulse_fallback":fallback+=1
            elif predictor.pulse.fit is not None:unusable+=1
        records.append(record);predictor.issued(now,next(iter(speeds)))
    return {"first_alert":first,"active_ticks":active,"unusable_after_fit_ticks":unusable,"fallback_ticks":fallback,"never_fit":predictor.pulse.fit is None,"eta_interval_s":window.interval if window else None,"last_eligible_source_s":last_source,"unsupported_missing_finding":bool(first and first["finding"]=="expected_target_edge_missing" and first["source_time_s"]<=first["window_upper_s"]+1e-9),"drained_tail_packets":delay},records


def study(plan_path,out):
    p=json.loads(plan_path.read_text());assert p["kind"]=="network_clock_ablation_v1" and p["predictor"]=="frozen_constant_bias" and p["drain_delivery_queue"]
    fixtures=list(itertools.product(p["speeds_m_s"],p["gains"],p["start_y_m"]))
    if len(fixtures)!=12 or p["faults"]!=["none","target_missing","drive_stall"]:raise ValueError("frozen12-condition grid required")
    old=json.loads((HERE/"experiments/eta_ml_20261106.json").read_text())["splits"]
    assert not {(v,g) for v,g,y in fixtures}.intersection({(v,g) for s in old.values() for v,g in itertools.product(s["speeds"],s["gains"])})
    config=load_config(HERE/"configs/reconfigurable_cell_20261030.json");segment=json.loads((HERE/"experiments/interval_calibration_20261105.json").read_text())
    model_path=HERE/"models/eta_residual_v1.json";settings_path=HERE/"models/eta_monitor_v1.json"
    model=json.loads(model_path.read_text());settings=json.loads(settings_path.read_text());assert settings["model_sha256"]==digest(model_path)
    out.mkdir(parents=True,exist_ok=False);save(out/"frozen_protocol.json",p)
    manifest={"plan_sha256":digest(plan_path),"model_sha256":digest(model_path),"settings_sha256":digest(settings_path),"sources":{x.name:digest(x) for x in HERE.glob('*.py')},"inputs":{}}
    trials=[]
    for i,(v,g,y) in enumerate(fixtures):
        for fault in p["faults"]:
            name=f"condition_{i:02}_"+fault;print(name,flush=True)
            base=deepcopy(config);base["reconfiguration"]["degraded_long_speed_m_s"]=min(base["reconfiguration"]["degraded_long_speed_m_s"],v)
            seg={**segment,"start_y_m":y};folder=out/name
            summary=simulate(folder,base,{"speed":v,"gain":g,"friction":p["friction"],"fault":fault},seg)
            if summary["anchor_s"] is None:raise ValueError("unresolved upstream anchor; retain failed study")
            obs,commands=(rows(folder/n) for n in ("observations.jsonl","issued_commands.jsonl"))
            for n in ("observations.jsonl","issued_commands.jsonl"):manifest["inputs"][name+"/"+n]=digest(folder/n)
            for case,options in p["network_cases"].items():
                windows=[]
                for policy,opts in p["policies"].items():
                    result,trace=replay(obs,commands,config,model,settings,opts,options,summary["anchor_s"])
                    if result["eta_interval_s"]:windows.append(result["eta_interval_s"])
                    trials.append({"id":name,"fault":fault,"case":case,"policy":policy,"onset_s":summary["onset_s"],**result})
                    with (out/(name+"_"+case+"_"+policy+".jsonl")).open('w',encoding='utf-8',newline=chr(10)) as log:
                        for row in trace:log.write(json.dumps(row,allow_nan=False)+chr(10))
                assert not windows or all(w==windows[0] for w in windows),'predictions differ across ablations'
            assert digest(model_path)==manifest["model_sha256"] and digest(settings_path)==manifest["settings_sha256"]
    groups={}
    for case in p["network_cases"]:
        groups[case]={}
        for policy in p["policies"]:
            groups[case][policy]={}
            for fault in p["faults"]:
                rs=[v for v in trials if (v["case"],v["policy"],v["fault"])==(case,policy,fault)]
                groups[case][policy][fault]={"runs":len(rs),"findings":sum(v["first_alert"] is not None for v in rs),"eligible_prediction_runs":sum(v["active_ticks"]>0 for v in rs),"data_rejected_runs":sum(v["never_fit"] or v["unusable_after_fit_ticks"]>0 for v in rs),"fallback_runs":sum(v["fallback_ticks"]>0 for v in rs),"unsupported_missing_findings":sum(v["unsupported_missing_finding"] for v in rs),"normal_budget_met":sum(v["first_alert"] is not None for v in rs)<=p["normal_finding_budget_per_case"] if fault=="none" else None}
    pairs=sum(all(manifest["inputs"][f"condition_{i:02}_target_missing/"+n]==manifest["inputs"][f"condition_{i:02}_drive_stall/"+n] for n in ("observations.jsonl","issued_commands.jsonl")) for i in range(12))
    report={"kind":p["kind"],"recordings":36,"replays":len(trials),"conditions":12,"groups":groups,"runs":trials,"identical_fault_pairs":pairs,"physical_validation":False,"parameter_tuning":False,"normal_finding_budget_per_case":p["normal_finding_budget_per_case"],"scope":p["scope"]}
    save(out/"manifest.json",manifest);save(out/"results.json",report);print(json.dumps({"groups":groups,"replays":len(trials)}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,default=HERE/'experiments/network_clock_ablation_20261106.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args();study(a.plan,a.output)
