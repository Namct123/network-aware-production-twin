"""Causal replay of event prediction vs observations; truth enters scoring only."""
import argparse
import hashlib
import json
from pathlib import Path
from innovation import EventResidual
from signals import SignalFrame

HERE=Path(__file__).resolve().parent

def rows(path):return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def replay(folder,settings,slack):
    config=json.loads((folder/"effective_config.json").read_text(encoding="utf-8"))
    observations=rows(folder/"observations.jsonl");decisions=rows(folder/"decisions.jsonl")
    monitor=EventResidual(config,settings);records=[];timeout=None
    if len(observations)!=len(decisions):raise ValueError("unaligned logs")
    for o,d in zip(observations,decisions):
        if abs(o["received_time_s"]-d["time_s"])>1e-9:raise ValueError("clock mismatch")
        f=SignalFrame(**o)
        record=monitor.observe(f,d["time_s"])
        if monitor.anchor is not None and not monitor.seen_target and timeout is None:
            distance=config["geometry"]["ps_y_m"]["ps2"]-config["geometry"]["ps_y_m"]["ps1"]-config["geometry"]["product_size_m"][1]
            deadline=monitor.anchor[0]+distance/config["motion"]["long_speed_m_s"]+slack
            if d["time_s"]>=deadline:timeout=d["time_s"]
        records.append(record)
        # Issue the current command AFTER evaluating the observation at the same tick.
        monitor.issued(d["time_s"],d["command"]["long"])
        if d["phase"]=="HOLD":break
    return records,monitor.first_alert,timeout

def study(source,plan,out):
    plan_path=Path(plan);p=json.loads(plan_path.read_text(encoding="utf-8"))
    if p["kind"]!="locked_residual_replay_v1":raise ValueError("unsupported plan")
    if Path(source).name!=p["source"]:raise ValueError("plan/source mismatch")
    out=Path(out);out.mkdir(parents=True,exist_ok=False);write(out/"plan.json",p)
    paths=[plan_path,HERE/"innovation.py",HERE/"study_residual.py",HERE/"command_history.py",HERE/"signals.py"]
    summaries=[]
    for folder in sorted(Path(source).iterdir()):
        if not folder.is_dir():continue
        result={"trial":folder.name,"variants":{}}
        paths.extend(folder/n for n in ("effective_config.json","observations.jsonl","decisions.jsonl","truth_evaluator_only.jsonl","summary.json"))
        # Evaluator-only reads: never passed to replay/monitor.
        truth=rows(folder/"truth_evaluator_only.jsonl")
        for variant,settings in p["variants"].items():
            records,alert,timeout=replay(folder,settings,p["fixed_timeout_slack_s"])
            if len(truth)<len(records):raise ValueError("missing truth")
            supported=covered=0
            with (out/(folder.name+"_"+variant+".jsonl")).open("w",encoding="utf-8") as f:
                for record,t in zip(records,truth):
                    if abs(record["time_s"]-t["time_s"])>1e-9:raise ValueError("truth clock mismatch")
                    interval=record["predicted_center_m"]
                    if interval is not None:
                        supported+=1;covered+=int(interval[0]<=t["product_xyz_m"][1]<=interval[1])
                    f.write(json.dumps(record,allow_nan=False)+"\n")
            result["variants"][variant]={"first_alert":alert,"fixed_timeout_first_s":timeout,"samples":len(records),"anchored_samples":supported,"truth_covered_samples":covered,"last_time_s":records[-1]["time_s"]}
        summaries.append(result);write(out/"partial_results.json",summaries)
    report={"kind":p["kind"],"trials":summaries,"physical_validation":False,"authority":"offline_advisory_only","interpretation":"No alert before old HOLD is censored, not proof of absence. Repeated deterministic simulations are not independent accuracy observations. Coverage is sample-wise in simulation, not a confidence level."}
    write(out/"results.json",report)
    write(out/"manifest.json",{"sha256":{str(x.relative_to(HERE.parent)) if x.is_relative_to(HERE.parent) else x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}})
    print(json.dumps({"trials":len(summaries),"variants":len(p["variants"]),"output":str(out)}))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--plan",type=Path,default=HERE/"experiments/residual_20261105.json");p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();study(a.source,a.plan,a.output)
