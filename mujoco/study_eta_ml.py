"""Train/select/calibrate/test ETA residuals without pose labels or trial mixing."""
import argparse
import itertools
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
from config import load_config
from calibrate_residual import save,digest,simulate
from study_pulse import rows
from eta_ml import optical_example,fit,predict

HERE=Path(__file__).resolve().parent

def metrics(model,examples,radius=None):
    errors={"nominal":[],"pulse":[],"constant_bias":[],"ml":[]};coverage=0;outside=0
    for e in examples:
        pred=predict(model,e);outside+=not pred["inside_training_feature_box"]
        for n,value in [("nominal",e["nominal_eta_s"]),("pulse",e["pulse_eta_s"]),("constant_bias",e["pulse_eta_s"]+model["constant_bias_s"]),("ml",pred["eta_s"])]:errors[n].append(abs(value-e["target_at_s"]))
        if radius is not None:coverage+=abs(pred["eta_s"]-e["target_at_s"])<=radius+1e-12
    return {"n":len(examples),"mae_ms":{n:float(np.mean(v))*1000 for n,v in errors.items()},"max_error_ms":{n:float(np.max(v))*1000 for n,v in errors.items()},"ml_interval_covered":coverage if radius is not None else None,"outside_training_feature_box":int(outside)}

def study(plan_path,out):
    p=json.loads(plan_path.read_text());base=load_config(HERE/"configs/reconfigurable_cell_20261030.json")
    segment=json.loads((HERE/"experiments/interval_calibration_20261105.json").read_text())
    if p["kind"]!="eta_residual_ml_v1" or list(p["splits"])!=["train","validation","calibration","test","shift"]:raise ValueError("ordered disjoint ML splits required")
    seen=set();fixtures={}
    for split,s in p["splits"].items():
        fixtures[split]=list(itertools.product(s["speeds"],s["gains"],s["frictions"]))
        for condition in fixtures[split]:
            if condition in seen:raise ValueError("condition leakage across splits")
            seen.add(condition)
    if len(seen)>100:raise ValueError("bounded study required")
    out.mkdir(parents=True,exist_ok=False);save(out/"protocol.json",p);save(out/"source_manifest.json",{"source_sha256":{x.name:digest(x) for x in HERE.glob('*.py')},"plan_sha256":digest(plan_path)})
    examples={};model=None;radius=None;seal=None;selection=[];inputs={}
    for split,conditions in fixtures.items():
        examples[split]=[]
        for i,(v,g,f) in enumerate(conditions):
            name=f"{split}_{i:02}";print(name,flush=True);folder=out/name
            fixture_base=deepcopy(base)
            fixture_base["reconfiguration"]["degraded_long_speed_m_s"]=min(base["reconfiguration"]["degraded_long_speed_m_s"],v)
            simulate(folder,fixture_base,{"speed":v,"gain":g,"friction":f,"fault":"none"},segment)
            example=optical_example(rows(folder/"observations.jsonl"),rows(folder/"issued_commands.jsonl"),base)
            examples[split].append({"id":name,**example})
            for n in ("observations.jsonl","issued_commands.jsonl"):inputs[name+"/"+n]=digest(folder/n)
        save(out/(split+"_examples.json"),examples[split])
        if split=="validation":
            for penalty in p["ridge_lambdas"]:
                candidate=fit(examples["train"],penalty);selection.append({"penalty":penalty,"validation_mae_ms":metrics(candidate,examples["validation"])["mae_ms"]["ml"]})
            best=min(selection,key=lambda x:(x["validation_mae_ms"],x["penalty"]))
            model=fit(examples["train"],best["penalty"]);save(out/"sealed_model.json",model);seal=digest(out/"sealed_model.json")
        if split=="calibration":
            radius=max(abs(predict(model,e)["eta_s"]-e["target_at_s"]) for e in examples[split]);save(out/"sealed_error_envelope.json",{"radius_s":radius,"n":len(examples[split]),"scope":"empirical max calibration residual, no probability guarantee"})
            envelope_seal=digest(out/"sealed_error_envelope.json")
        if split in ("test","shift") and (digest(out/"sealed_model.json")!=seal or digest(out/"sealed_error_envelope.json")!=envelope_seal):raise ValueError("model/calibration modified after sealing")
    report={"kind":p["kind"],"model_sha256":seal,"error_envelope_sha256":envelope_seal,"selected_model":model,"selection":selection,"error_radius_s":radius,"splits":{n:metrics(model,e,radius) for n,e in examples.items()},"input_sha256":inputs,"ml_trained":True,"physical_validation":False,"posthoc_disclosure":"Train-only constant-bias baseline added after initial pilot; no change to ridge features, training rows, lambda selection or test outcomes.","scope":"Supervised Ridge residual ETA regression on normal deterministic virtual trajectories; not a fault classifier, not deployed into policy/PLC. Condition-disjoint grid does not establish statistical generalization."}
    save(out/"results.json",report);print(json.dumps(report["splits"]),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--plan",type=Path,default=HERE/"experiments/eta_ml_20261106.json");p.add_argument("--output",type=Path,required=True);a=p.parse_args();study(a.plan,a.output)
