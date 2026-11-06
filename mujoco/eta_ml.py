"""Small learned residual ETA model; inputs frozen at upstream pulse end."""
import numpy as np
from command_history import CommandHistory
from signals import SignalFrame

def optical_example(observations,commands,config):
    if not observations or len(observations)!=len(commands):raise ValueError("aligned complete recordings required")
    if commands[0]["command"]["long"]<=0 or any(c["command"]["long"]!=commands[0]["command"]["long"] for c in commands):raise ValueError("constant forward command required for this model")
    history=CommandHistory();previous=False;start=None;example=None;target=None;last=None
    length=config["geometry"]["product_size_m"][1]
    distance=config["geometry"]["ps_y_m"]["ps2"]-config["geometry"]["ps_y_m"]["ps1"]-length
    for o,c in zip(observations,commands):
        f=SignalFrame(**o);t=f.source_time_s
        if t!=c["time_s"] or any(f.quality.get(k)!="good" for k in ("ps1","ps2")):raise ValueError("good source-clock optical records required")
        if last is not None and (f.sequence!=last.sequence+1 or not 0<t-last.source_time_s<=config["timing"]["max_sample_gap_s"]+1e-9):raise ValueError("contiguous pulse required")
        up=f.values["ps1"]
        if up and not previous and example is None:start=t
        if not up and previous and start is not None and example is None:
            window=history.interval(start,t);speed=c["command"]["long"]
            if speed<=0 or window["distance_m"]<=0:raise ValueError("forward resolved pulse required")
            pulse=t-start;gain=length/window["distance_m"]
            example={"features":[pulse,speed,pulse*speed],"available_at_s":t,"pulse_eta_s":t+distance/(speed*gain),"nominal_eta_s":t+distance/speed}
        if example is not None and f.values["ps2"]:
            target=t;break
        history.record(t,c["command"]["long"]);previous=up;last=f
    if example is None or target is None or target<=example["available_at_s"]:raise ValueError("observed target label required; no truth fallback")
    return {**example,"target_at_s":target,"residual_s":target-example["pulse_eta_s"]}

def fit(examples,penalty):
    x=np.asarray([e["features"] for e in examples],dtype=float);y=np.asarray([e["residual_s"] for e in examples],dtype=float)
    if x.ndim!=2 or x.shape[1]!=3 or len(x)<4 or not np.isfinite(x).all() or not np.isfinite(y).all() or not np.isfinite(penalty) or penalty<=0:raise ValueError("finite training rows and positive ridge penalty required")
    mean=x.mean(axis=0);scale=x.std(axis=0);scale=np.where(scale>1e-12,scale,1.)
    design=np.column_stack((np.ones(len(x)),(x-mean)/scale));reg=np.diag([0.,penalty,penalty,penalty])
    weights=np.linalg.solve(design.T@design+reg,design.T@y)
    return {"kind":"ridge_eta_residual_v1","feature_names":["pulse_duration_s","issued_speed_m_s","pulse_command_distance_m"],"penalty":penalty,"mean":mean.tolist(),"scale":scale.tolist(),"weights":weights.tolist(),"feature_min":x.min(axis=0).tolist(),"feature_max":x.max(axis=0).tolist(),"training_rows":len(x),"constant_bias_s":float(y.mean()),"authority":"advisory_only"}

def predict(model,example):
    x=np.asarray(example["features"],dtype=float)
    if x.shape!=(3,) or not np.isfinite(x).all():raise ValueError("three finite causal features required")
    z=np.r_[1.,(x-np.asarray(model["mean"]))/np.asarray(model["scale"])]
    estimate=example["pulse_eta_s"]+float(z@np.asarray(model["weights"]))
    return {"eta_s":max(example["available_at_s"],estimate),"inside_training_feature_box":bool(np.all(x>=model["feature_min"]) and np.all(x<=model["feature_max"]))}


def predict_from_pulse(model,pulse_fit,issued_speed,distance):
    """Live advisory boundary: only a completed upstream fit, no target label."""
    duration=pulse_fit["at_s"]-pulse_fit["pulse_start_s"]
    gain=pulse_fit["gain_point"]
    if not all(type(v) in (int,float) and np.isfinite(v) and v>0 for v in (duration,gain,issued_speed,distance)):
        raise ValueError("positive finite pulse and geometry required")
    example={"features":[duration,issued_speed,duration*issued_speed],"available_at_s":pulse_fit["at_s"],
             "pulse_eta_s":pulse_fit["at_s"]+distance/(issued_speed*gain)}
    return {**predict(model,example),"features_available_at_s":pulse_fit["at_s"],"authority":"advisory_only"}
