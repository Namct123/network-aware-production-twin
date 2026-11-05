"""Fit optical-event motion bounds on normal runs, seal before held-out trials."""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import itertools
import json
import math
from pathlib import Path
from config import load_config, validate_config, exact_keys, number
from innovation import EventResidual
from sensor_model import SensorModel
from command_history import CommandHistory

HERE=Path(__file__).resolve().parent

def save(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_plan(p):
    exact_keys(p,("kind","calibration_speeds_m_s","calibration_gains","test_speeds_m_s","test_gains","test_frictions","shift_gains","start_y_m","command_distance_m","drift_m_s","confirm_samples","edge_guard_m","sample_guard_periods","fixed_timeout_slack_s","scope"),"calibration plan")
    if p["kind"]!="optical_interval_calibration_v1":raise ValueError("unsupported plan")
    for key in ("calibration_speeds_m_s","calibration_gains","test_speeds_m_s","test_gains","test_frictions","shift_gains"):
        values=p[key]
        if not isinstance(values,list) or not 1<=len(values)<=5 or len(set(values))!=len(values):raise ValueError("bounded unique condition vectors required")
        for value in values:number(value,key,0,True)
    for key in ("command_distance_m","edge_guard_m","sample_guard_periods"):number(p[key],key,0,True)
    for key in ("drift_m_s","fixed_timeout_slack_s"):number(p[key],key,0)
    number(p["start_y_m"],"start_y_m")
    if type(p["confirm_samples"]) is not int or not 1<=p["confirm_samples"]<=100:raise ValueError("bounded confirmation count required")
    if any(p["command_distance_m"]/v>10 for v in p["calibration_speeds_m_s"]+p["test_speeds_m_s"]):raise ValueError("each segment must finish within 10 simulated seconds")
    groups=conditions(p)
    if sum(len(fixtures) for _,fixtures in groups)>100:raise ValueError("at most 100 conditions per plan")
    return p

def conditions(p):
    training=[{"speed":v,"gain":g,"friction":1.,"fault":"none"} for v,g in itertools.product(p["calibration_speeds_m_s"],p["calibration_gains"])]
    test=[{"speed":v,"gain":g,"friction":f,"fault":"none"} for v,g,f in itertools.product(p["test_speeds_m_s"],p["test_gains"],p["test_frictions"])]
    faults=[{**c,"fault":fault} for c in test for fault in ("target_missing","drive_stall")]
    shifted=[{"speed":v,"gain":g,"friction":1.,"fault":"none"} for v,g in itertools.product(p["test_speeds_m_s"],p["shift_gains"])]
    if {tuple(sorted(c.items())) for c in training}&{tuple(sorted(c.items())) for c in test}:raise ValueError("train/test conditions overlap")
    return [("calibration",training),("test_normal",test),("test_fault",faults),("test_shift",shifted)]

def fit_bounds(events,p):
    bounds=[]
    for event in events:
        if event is None:raise ValueError("Every calibration run needs an observed transition; no truth fallback")
        distance,travel,period,speed=event["sensor_distance_m"],event["command_distance_m"],event["period_s"],event["command_speed_m_s"]
        if not all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in (distance,travel,period,speed)):
            raise ValueError("positive finite observed transit inputs required")
        guard=p["sample_guard_periods"]*period*speed
        if distance<=p["edge_guard_m"] or travel<=guard:raise ValueError("degenerate transit bounds")
        bounds.append([(distance-p["edge_guard_m"])/(travel+guard),(distance+p["edge_guard_m"])/(travel-guard)])
    if not bounds:raise ValueError("calibration events required")
    return {"gain_bounds":[min(b[0] for b in bounds),max(b[1] for b in bounds)],"drift_m_s":p["drift_m_s"],"confirm_samples":p["confirm_samples"]}

def simulate(folder,base,c,p,settings=None):
    from run_cell import Cell
    cfg=deepcopy(base);cfg["geometry"]["product_initial_xyz_m"]=[cfg["geometry"]["lane_x_m"],p["start_y_m"],cfg["mechanics"]["belt_surface_z_m"]+.031]
    cfg["motion"]["long_speed_m_s"]=c["speed"]
    cfg["plant"]["belt_speed_scale"]["long"]=c["gain"]
    cfg["plant"]["product_friction"][0]=c["friction"];validate_config(cfg)
    cell=Cell(cfg);sensors=SensorModel(config=cfg)
    # Estimator receives the shared nominal model, not hidden actual gain/friction.
    nominal=deepcopy(base);nominal["motion"]["long_speed_m_s"]=c["speed"]
    monitors={name:EventResidual(nominal,value) for name,value in (settings or {}).items()}
    folder.mkdir();save(folder/"plant_fixture.json",c)
    save(folder/"effective_plant_config.json",cfg)
    # Save the actual compiled model using the official exporter.
    import mujoco
    mujoco.mj_saveLastXML(str(folder/"effective_model.xml"),cell.model)
    history=CommandHistory();anchor=None;target=None;previous=None;onset=None;timeout=None
    count={name:{"anchored_samples":0,"covered_samples":0,"width_sum_m":0.} for name in monitors}
    period=cfg["timing"]["physics_step_s"]*cfg["timing"]["sample_steps"]
    duration=p["command_distance_m"]/c["speed"]
    with (folder/"observations.jsonl").open("w",encoding="utf-8",newline="\n") as obs,(folder/"issued_commands.jsonl").open("w",encoding="utf-8",newline="\n") as commands,(folder/"evaluator_only.jsonl").open("w",encoding="utf-8",newline="\n") as truth,(folder/"residuals.jsonl").open("w",encoding="utf-8",newline="\n") as residuals:
        for _ in range(math.floor(duration/period)+1):
            state=cell.observe();now=state["time_s"];frame,_=sensors.sample(state)
            if anchor is None and previous is True and frame.values["ps1"] is False:
                anchor=now
                if c["fault"]!="none":onset=now
            if c["fault"]=="target_missing" and onset is not None:
                frame=replace(frame,values={**frame.values,"ps2":False})
            if anchor is not None and target is None and frame.values["ps2"]:
                target=now
                integral=history.interval(anchor,target)
                event={"sensor_distance_m":base["geometry"]["ps_y_m"]["ps2"]-base["geometry"]["ps_y_m"]["ps1"]-base["geometry"]["product_size_m"][1],"command_distance_m":integral["distance_m"],"period_s":period,"command_speed_m_s":c["speed"],"anchor_s":anchor,"target_s":target}
            if anchor is not None and target is None and timeout is None:
                distance=base["geometry"]["ps_y_m"]["ps2"]-base["geometry"]["ps_y_m"]["ps1"]-base["geometry"]["product_size_m"][1]
                if now+1e-9>=anchor+distance/c["speed"]+p["fixed_timeout_slack_s"]:timeout=now
            results={name:m.observe(frame,now) for name,m in monitors.items()}
            for name,record in results.items():
                interval=record["predicted_center_m"]
                if interval is not None:
                    count[name]["anchored_samples"]+=1
                    count[name]["covered_samples"]+=int(interval[0]<=state["product_xyz_m"][1]<=interval[1])
                    count[name]["width_sum_m"]+=interval[1]-interval[0]
            issued={"front":0.,"long":c["speed"],"targets":{},"vacuum":False,"hold":False}
            actual={**issued,"long":0. if c["fault"]=="drive_stall" and onset is not None else issued["long"]}
            obs.write(json.dumps(frame.as_dict())+"\n");commands.write(json.dumps({"time_s":now,"command":issued})+"\n")
            truth.write(json.dumps({"time_s":now,"product_xyz_m":state["product_xyz_m"],"applied_command":actual})+"\n")
            residuals.write(json.dumps({"time_s":now,"monitors":results})+"\n")
            for m in monitors.values():m.issued(now,issued["long"])
            history.record(now,issued["long"]);cell.apply(actual);previous=frame.values["ps1"]
            cell.step()
    summaries={}
    for name,m in monitors.items():
        n=count[name]["anchored_samples"]
        summaries[name]={**count[name],"mean_width_m":count[name]["width_sum_m"]/n if n else None,"first_alert":m.first_alert,"detection_delay_s":m.first_alert["time_s"]-onset if m.first_alert and onset is not None else None}
    result={"fixture":c,"observed_transit":event if target is not None else None,"anchor_s":anchor,"onset_s":onset,"last_sample_s":now,"fixed_timeout_first_s":timeout,"monitors":summaries,"scope":"isolated open-loop tracking fixture, not a complete production cycle"}
    save(folder/"summary.json",result);return result

def study(plan_path,out):
    p=validate_plan(json.loads(Path(plan_path).read_text(encoding="utf-8")))
    if p["kind"]!="optical_interval_calibration_v1":raise ValueError("unsupported plan")
    groups=conditions(p);base=load_config(HERE/"configs/reconfigurable_cell_20261030.json")
    out=Path(out);out.mkdir(parents=True,exist_ok=False);save(out/"plan.json",p)
    save(out/"source_manifest.json",{"sha256":{str(x.relative_to(HERE)):digest(x) for x in HERE.rglob('*') if x.is_file() and x.suffix in ('.py','.json') and '__pycache__' not in x.parts},"plan_sha256":digest(plan_path)})
    results=[];events=[]
    for i,c in enumerate(groups[0][1]):
        name=f"calibration_{i:02}";print(name,flush=True)
        row=simulate(out/name,base,c,p);results.append({"group":"calibration","id":name,**row});events.append(row["observed_transit"])
        save(out/"partial_results.json",results)
    learned=fit_bounds(events,p)
    sealed={"settings":learned,"calibration_ids":[r["id"] for r in results],"source":"optical transitions and issued integrals only; no plant pose or held-out fixture gain","physical_validation":False}
    save(out/"sealed_calibration.json",sealed);seal=digest(out/"sealed_calibration.json")
    settings={"calibrated_events":learned,"old_narrow_assumption":{"gain_bounds":[.95,1.05],"drift_m_s":.005,"confirm_samples":2},"profile_engineering_bounds":{"gain_bounds":[.8,1.2],"drift_m_s":.02,"confirm_samples":2}}
    save(out/"monitor_settings.json",settings)
    for group,fixtures in groups[1:]:
        for i,c in enumerate(fixtures):
            if digest(out/"sealed_calibration.json")!=seal:raise ValueError("calibration changed during held-out evaluation")
            name=f"{group}_{i:02}";print(name,flush=True)
            row=simulate(out/name,base,c,p,settings)
            results.append({"group":group,"id":name,"calibration_sha256":seal,**row});save(out/"partial_results.json",results)
    report={"kind":p["kind"],"calibration_sha256":seal,"sealed_calibration":sealed,"runs":results,"physical_validation":False,"ml_trained":False,"scope":"Empirical optical parameter identification, deterministic held-out grid; no confidence/probability guarantee, network impairment or closed-loop reconfiguration. All failures retained; no tuning from held-out outcomes."}
    save(out/"results.json",report);print(json.dumps({"runs":len(results),"learned":learned,"output":str(out)}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--plan",type=Path,default=HERE/"experiments/interval_calibration_20261105.json");p.add_argument("--output",type=Path,required=True);a=p.parse_args();study(a.plan,a.output)
