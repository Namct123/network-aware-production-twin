"""Same-information closed-loop stopping comparison in an isolated MuJoCo segment."""
import argparse
from copy import deepcopy
from dataclasses import replace
import itertools
import json
import math
from pathlib import Path
from config import load_config,validate_config
from calibrate_residual import save,digest
from sensor_model import SensorModel
from network import Network
from pulse_observer import PulseObserver
from predictor import Predictor
from estimator import Estimate

HERE=Path(__file__).resolve().parent

def select_speed(policy,requested,record,observer,now,limit,plan,config):
    if policy=="sequential":return requested,"nominal",[]
    age=record["observation_age_s"]
    if policy=="age_rule":
        return (min(requested,plan["rule_cap_m_s"]),"age_speed_cap",[]) if age is not None and age+1e-9>=plan["warning_age_s"] else (requested,"nominal",[])
    if policy!="predictive":raise ValueError("unknown policy")
    if observer.fit is None:return requested,"await_upstream_pulse",[]
    if not record["usable_for_monitoring"]:return 0.,"unusable_pulse_evidence",[]
    low,high=record["predicted_center_m"];glo,ghi=observer.fit["gain_bounds"]
    source=record["prediction_time_s"];past=observer.core.commands.interval(source,now)
    allowance=config["estimator"]["drift_m_s"]*(now-source)+config["estimator"]["command_response_uncertainty_s"]*past["speed_variation_m_s"]+past["stops"]*config["estimator"]["stop_coast_m"]
    low+=glo*past["distance_m"]-allowance;high+=ghi*past["distance_m"]+allowance
    trials=[];predictor=Predictor(config);predictor.limit=limit
    for speed in sorted({min(requested,v) for v in plan["speed_candidates_m_s"]},reverse=True):
        estimate=Estimate((low+high)/2,speed*ghi,(high-low)/2,1,"pulse_interval")
        forecast=predictor.rollout(estimate,now,now);trials.append({"speed":speed,"forecast":forecast})
        if forecast["status"]=="complete" and forecast["action"]=="CONTINUE":return speed,"predictive_speed_selection",trials
    return 0.,"no_admissible_speed",trials

def transit_expired(policy,observer,source_time,requested,distance,slack=.2):
    anchor=observer.core.anchor[0]
    if policy=="sequential":return source_time+1e-9>=anchor+distance/requested+slack
    gain=observer.fit["gain_point"] if observer.fit is not None else 1.
    # Adaptive reference integrates actual issued speed changes, not hidden plant speed.
    window=observer.core.commands.interval(anchor,source_time)
    return gain*window["distance_m"]+1e-9>=distance+gain*requested*slack

def trial(folder,base,fixture,policy,zone,plan):
    from run_cell import Cell
    cfg=deepcopy(base);cfg["geometry"]["product_initial_xyz_m"]=[cfg["geometry"]["lane_x_m"],plan["start_y_m"],base["geometry"]["product_initial_xyz_m"][2]]
    cfg["plant"]["belt_speed_scale"]["long"]=fixture["gain"];validate_config(cfg)
    nominal=deepcopy(base);nominal["estimator"]["drift_m_s"]=plan["drift_m_s"]
    observer=PulseObserver(nominal,{"gain_bounds":[.8,1.2],"drift_m_s":plan["drift_m_s"],"confirm_samples":2},plan["length_guard_m"])
    network=Network({"delay_s":fixture["delay"],"jitter_s":0.,"drop_probability":0.,"seed":0})
    cell=Cell(cfg);sensors=SensorModel(config=cfg)
    folder.mkdir();save(folder/"fixture.json",fixture);save(folder/"effective_plant_config.json",cfg)
    period=cfg["timing"]["physics_step_s"]*cfg["timing"]["sample_steps"]
    last_received=0.;stopped=None;confirmed=False;reason=None;previous=None;fault_on=False;deadline=None;reduced=0;max_y=-math.inf;prediction_misses=0
    with (folder/"decisions.jsonl").open("w",encoding="utf-8",newline="\n") as decisions,(folder/"evaluator_only.jsonl").open("w",encoding="utf-8",newline="\n") as truth:
        for _ in range(math.ceil(plan["run_budget_s"]/period)+1):
            state=cell.observe();now=state["time_s"];source,_=sensors.sample(state)
            if previous is True and source.values["ps1"] is False:fault_on=True
            previous=source.values["ps1"]
            if fixture["fault"]=="pickup_missing" and fault_on:source=replace(source,values={**source.values,"ps2":False})
            network.send(source,now);frame=network.receive(now);record=observer.observe(frame,now)
            if frame is not None:last_received=now
            speed=fixture["speed"];forecasts=[]
            if stopped is None:
                if now-last_received+1e-9>=cfg["timing"]["silence_timeout_s"]:reason="transport_silence"
                elif frame is not None and now-frame.source_time_s>cfg["timing"]["max_age_s"]+1e-9:reason="stale_transport"
                elif frame is not None and frame.quality["ps2"]=="good" and frame.values["ps2"]:
                    confirmed=True;reason="target_seen"
                elif observer.core.anchor is not None:
                    distance=cfg["geometry"]["ps_y_m"]["ps2"]-cfg["geometry"]["ps_y_m"]["ps1"]-cfg["geometry"]["product_size_m"][1]
                    if frame is not None and transit_expired(policy,observer,frame.source_time_s,fixture["speed"],distance,plan["timeout_slack_s"]):reason="transit_timeout"
                if reason is None:
                    speed,why,forecasts=select_speed(policy,fixture["speed"],record,observer,now,zone[1],plan,nominal)
                    if speed==0:reason=why
                if reason is not None:stopped=now
            if stopped is not None:speed=0.
            reduced+=int(0<speed<fixture["speed"])
            prediction_misses+=sum(t["forecast"]["status"]!="complete" for t in forecasts)
            command={"front":0.,"long":speed,"targets":{},"vacuum":False,"hold":speed==0}
            decisions.write(json.dumps({"time_s":now,"received":frame.as_dict() if frame else None,"observer":record,"command":command,"stop_reason":reason,"forecasts":forecasts})+"\n")
            truth.write(json.dumps({"time_s":now,"product_xyz_m":state["product_xyz_m"]})+"\n")
            # True pose is used only here, in the evaluator, never passed to select_speed.
            max_y=max(max_y,state["product_xyz_m"][1]);observer.issued(now,speed);cell.apply(command)
            if stopped is not None and now-stopped+1e-9>=plan["settle_s"]:break
            cell.step()
    y=state["product_xyz_m"][1]
    result={"policy":policy,"fixture":fixture,"zone_m":zone,"confirmed":confirmed,"stop_reason":reason,"stop_time_s":stopped,"last_time_s":now,"evaluator_final_y_m":y,"evaluator_max_y_m":max_y,"finished_in_zone":bool(confirmed and zone[0]<=y<=zone[1]),"upper_boundary_exceeded":max_y>zone[1],"undershoot":y<zone[0],"reduced_speed_ticks":reduced,"prediction_deadlines_missed":prediction_misses,"scope":plan["scope"]}
    save(folder/"summary.json",result);return result

def study(plan_path,out):
    p=json.loads(plan_path.read_text());base=load_config(HERE/"configs/reconfigurable_cell_20261030.json")
    if p["kind"]!="closed_loop_segment_v1" or p["policies"]!=["sequential","age_rule","predictive"]:raise ValueError("fixed three-policy comparison required")
    if not 0<p["run_budget_s"]<=10 or not 0<p["settle_s"]<=1:raise ValueError("bounded run required")
    fixtures=[{"speed":v,"gain":g,"delay":d,"fault":f} for v,g,d,f in itertools.product(p["speeds_m_s"],p["plant_gains"],p["delays_s"],p["faults"])]
    if len(fixtures)*len(p["policies"])*len(p["zones_m"])>200:raise ValueError("at most 200 runs")
    out.mkdir(parents=True,exist_ok=False);save(out/"plan.json",p);save(out/"manifest.json",{"source_sha256":{x.name:digest(x) for x in HERE.glob('*.py')},"plan_sha256":digest(plan_path)})
    runs=[]
    for zn,zone in p["zones_m"].items():
        if not len(zone)==2 or not zone[0]<zone[1]:raise ValueError("ordered zone required")
        for i,f in enumerate(fixtures):
            for policy in p["policies"]:
                name=f"{zn}_{i:02}_{policy}";print(name,flush=True)
                runs.append({"id":name,"zone":zn,**trial(out/name,base,f,policy,zone,p)});save(out/"partial_results.json",runs)
    groups={}
    for zn in p["zones_m"]:
        groups[zn]={}
        for fault in p["faults"]:
            groups[zn][fault]={}
            for policy in p["policies"]:
                rs=[r for r in runs if r["zone"]==zn and r["fixture"]["fault"]==fault and r["policy"]==policy]
                groups[zn][fault][policy]={"runs":len(rs),"finished":sum(r["finished_in_zone"] for r in rs),"upper_exceeded":sum(r["upper_boundary_exceeded"] for r in rs),"undershoot":sum(r["undershoot"] for r in rs),"prediction_misses":sum(r["prediction_deadlines_missed"] for r in rs)}
    save(out/"results.json",{"groups":groups,"runs":runs,"physical_validation":False,"scope":p["scope"]});print(json.dumps(groups),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--plan",type=Path,default=HERE/"experiments/closed_loop_segment_20261106.json");p.add_argument("--output",type=Path,required=True);a=p.parse_args();study(a.plan,a.output)
