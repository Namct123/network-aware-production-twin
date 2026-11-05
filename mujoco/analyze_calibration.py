"""Recompute logged event decisions and add a disclosed post-hoc drift-matched ablation."""
import argparse
import hashlib
import json
from pathlib import Path
from config import load_config
from innovation import EventResidual
from signals import SignalFrame

HERE=Path(__file__).resolve().parent

def rows(p):return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines()]

def analyze(source,output):
    output=Path(output)
    if output.exists():raise FileExistsError("Do not overwrite analysis")
    data=json.loads((source/"results.json").read_text(encoding="utf-8"))
    settings=json.loads((source/"monitor_settings.json").read_text(encoding="utf-8"))
    plan=json.loads((source/"plan.json").read_text(encoding="utf-8"))
    settings["posthoc_same_drift"]={"gain_bounds":[.8,1.2],"drift_m_s":plan["drift_m_s"],"confirm_samples":plan["confirm_samples"]}
    inputs={};allrows=[];replayed=0
    def track(p):inputs[str(p.relative_to(source))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ("results.json","monitor_settings.json","sealed_calibration.json","plan.json"):track(source/name)
    for run in data["runs"]:
        if run["group"]=="calibration":continue
        folder=source/run["id"]
        for name in ("observations.jsonl","issued_commands.jsonl","evaluator_only.jsonl","residuals.jsonl"):track(folder/name)
        observations=rows(folder/"observations.jsonl");commands=rows(folder/"issued_commands.jsonl");truth=rows(folder/"evaluator_only.jsonl");old=rows(folder/"residuals.jsonl")
        if not len(observations)==len(commands)==len(truth)==len(old):raise ValueError("unaligned files")
        monitors={n:EventResidual(load_config(HERE/"configs/reconfigurable_cell_20261030.json"),s) for n,s in settings.items()}
        counts={n:{"samples":0,"covered":0,"width_sum_m":0.} for n in monitors}
        for o,c,t,record in zip(observations,commands,truth,old):
            if not o["received_time_s"]==c["time_s"]==t["time_s"]==record["time_s"]:raise ValueError("clock mismatch")
            for n,m in monitors.items():
                result=m.observe(SignalFrame(**o),c["time_s"])
                if n in record["monitors"]:
                    if result!=record["monitors"][n]:raise ValueError("causal replay mismatch")
                    replayed+=1
                interval=result["predicted_center_m"]
                if interval is not None:
                    counts[n]["samples"]+=1;counts[n]["covered"]+=int(interval[0]<=t["product_xyz_m"][1]<=interval[1]);counts[n]["width_sum_m"]+=interval[1]-interval[0]
                m.issued(c["time_s"],c["command"]["long"])
        allrows.append({"id":run["id"],"group":run["group"],"onset_s":run["onset_s"],"timeout_s":run["fixed_timeout_first_s"],"monitors":{n:{**counts[n],"first_alert":m.first_alert} for n,m in monitors.items()}})
    groups={}
    for group in ("test_normal","test_fault","test_shift"):
        runs=[r for r in allrows if r["group"]==group]
        g={"runs":len(runs),"fixed_timeout_alerts":sum(r["timeout_s"] is not None for r in runs),"monitors":{}}
        for n in settings:
            ms=[r["monitors"][n] for r in runs];samples=sum(m["samples"] for m in ms)
            delays=[r["monitors"][n]["first_alert"]["time_s"]-r["onset_s"] for r in runs if r["onset_s"] is not None and r["monitors"][n]["first_alert"] is not None]
            g["monitors"][n]={"alerts":sum(m["first_alert"] is not None for m in ms),"covered_samples":sum(m["covered"] for m in ms),"samples":samples,"mean_width_m":sum(m["width_sum_m"] for m in ms)/samples if samples else None,"delay_range_s":[min(delays),max(delays)] if delays else None}
        groups[group]=g
    result={"groups":groups,"runs":allrows,"exact_replayed_monitor_samples":replayed,"sha256":inputs,"analysis_source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"posthoc_disclosure":"same_drift ablation added AFTER pilot to separate manually selected drift allowance from fitted gain bounds; not a preregistered comparison or calibration input","scope":"Deterministic virtual grid, sample coverage not probability; cannot distinguish missing sensor from stalled drive; no ML/full-cycle/control authority"}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"groups":groups,"replayed_samples":replayed}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();analyze(a.source,a.output)
