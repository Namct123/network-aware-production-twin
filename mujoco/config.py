"""Single SI configuration boundary; reject typos and impossible configurations."""

from copy import deepcopy
import json
import math
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent / "configs/simulation.json"
JOINTS = ("x_joint", "y_joint", "a1_joint", "a2_joint")
KEYS = {
    "profile": "name status units notes measurements",
    "geometry": "robot_origin_xy_m joint_limits_m ps_y_m optical_xz_m product_size_m product_initial_xyz_m lane_x_m long_belt_y_m bin_centers_xy_m bin_inner_size_xy_m placement_z_m hold_z_m hold_lane_tolerance_m front_belt_xy_m",
    "plant": "product_mass_kg product_friction belt_friction cup_friction vacuum_adhesion_n belt_speed_scale joint_damping position_kp dampratio link_inertials",
    "motion": "front_speed_m_s long_speed_m_s test_speed_range_m_s rates_m_s home_xy_m a2_pick_m feed_distance_m feed_startup_s axis_settle_s a2_settle_s grip_wait_s release_wait_s",
    "sensors": "end_switch_tolerance_m optical_detection_range_m",
    "estimator": "stop_coast_m anchor_tolerance_m drift_m_s transit_speed_range_m_s pick_uncertainty_limit_m",
    "timing": "physics_step_s sample_steps max_age_s max_sample_gap_s silence_timeout_s cylinder_timeout_s track_timeout_max_s track_travel_budget_m run_budget_s hold_settle_s",
    "network": "delay_s jitter_s drop_probability seed",
    "prediction": "enabled horizon_s step_s wall_budget_s speed_offsets_m_s position_offsets reaction_delays_s stop_margin_m",
}


def number(value, name, minimum=None, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name}: expected a finite SI number, not bool/string/NaN")
    if minimum is not None and (value < minimum or positive and value <= minimum):
        raise ValueError(f"{name}: outside allowed range")
    return value


def validate_outages(windows,run_budget=None):
    if not isinstance(windows,list) or len(windows)>20: raise ValueError('0..20 outage windows required')
    end=-1
    for w in windows:
        if not isinstance(w,list) or len(w)!=2: raise ValueError('outage window requires [start,end] seconds')
        a,b=w; number(a,'outage start',0); number(b,'outage end',0)
        if a>=b or a<end or (run_budget is not None and b>run_budget): raise ValueError('outage windows must be ordered, nonoverlapping and within run budget')
        end=b


def vector(value, size, name, positive=False):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{name}: expected a list of {size} numbers")
    for item in value:
        number(item, name, 0 if positive else None, positive)


def ordered(value, name):
    vector(value, 2, name)
    if value[0] >= value[1]:
        raise ValueError(f"{name}: lower bound must be below upper bound")


def exact_keys(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{name}: expected exactly {sorted(keys)}")


def validate_config(c):
    # Profiles from the previous schema-1 implementation remain usable; the new
    # supervisor is disabled unless explicitly enabled in a resolved profile.
    if isinstance(c,dict) and "prediction" not in c:
        c=deepcopy(c)
        c["prediction"]=json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))["prediction"]
    exact_keys(c, ["schema_version", *KEYS, *[k for k in ('mechanics','health','reconfiguration','recovery') if k in c]], "config")
    if type(c["schema_version"]) is not int or c["schema_version"] != 1:
        raise ValueError("unsupported schema_version")
    for section, keys in KEYS.items():
        optional={'estimator':('command_history_enabled','command_gain_range','command_response_uncertainty_s'),
                  'motion':('long_speed_schedule',),'network':('outage_windows_s',),'prediction':('backend','native_threads')}.get(section,())
        exact_keys(c[section], [*keys.split(),*[k for k in optional if k in c[section]]], section)
    meta = c["profile"]
    if not all(isinstance(meta[k], str) and meta[k] for k in ("name", "status", "units", "notes")):
        raise ValueError("profile text fields must be nonempty strings")
    if meta["status"] not in {"unmeasured", "partial", "measured_unvalidated"}:
        raise ValueError("profile status cannot certify calibration/validation")
    if meta["units"] != "SI: m, s, kg, N" or not isinstance(meta["measurements"], list):
        raise ValueError("SI units and a measurements provenance list are required")
    g, m, p, s, e, t, n = (c[k] for k in ("geometry", "motion", "plant", "sensors", "estimator", "timing", "network"))
    for key in ("robot_origin_xy_m", "optical_xz_m", "home_xy_m"):
        vector((m if key == "home_xy_m" else g)[key], 2, key)
    for key in ("product_size_m", "product_initial_xyz_m"):
        vector(g[key], 3, key, positive=key == "product_size_m")
    for key in ("long_belt_y_m", "placement_z_m", "hold_z_m"):
        ordered(g[key], key)
    if not isinstance(g["front_belt_xy_m"], list) or len(g["front_belt_xy_m"]) != 2:
        raise ValueError("front belt requires X and Y support intervals")
    for bounds in g["front_belt_xy_m"]:
        ordered(bounds, "front_belt_xy_m")
    vector(g["bin_inner_size_xy_m"], 2, "bin_inner_size_xy_m", positive=True)
    number(g["lane_x_m"], "lane_x_m")
    number(g["hold_lane_tolerance_m"], "hold_lane_tolerance_m", 0, True)
    exact_keys(g["joint_limits_m"], JOINTS, "joint_limits_m")
    for joint in JOINTS:
        ordered(g["joint_limits_m"][joint], joint)
        if not g["joint_limits_m"][joint][0] <= 0 <= g["joint_limits_m"][joint][1]:
            raise ValueError("current model requires zero inside each joint range")
    if any(g["joint_limits_m"][j][0] != 0 for j in ("a1_joint", "a2_joint")):
        raise ValueError("cylinder retracted reference must be zero")
    exact_keys(g["ps_y_m"], ("ps1", "ps2"), "ps_y_m")
    ps1, ps2 = (number(g["ps_y_m"][k], k) for k in ("ps1", "ps2"))
    if not g["long_belt_y_m"][0] < ps1 < ps2 < g["long_belt_y_m"][1]:
        raise ValueError("ordered optical sensors must be within the long belt")
    if not isinstance(g["bin_centers_xy_m"], list) or len(g["bin_centers_xy_m"]) != 6:
        raise ValueError("this CAD adapter supports exactly six bins")
    for point in g["bin_centers_xy_m"]:
        vector(point, 2, "bin_centers_xy_m")
    for axis, origin, home, lane in zip(("x_joint", "y_joint"), g["robot_origin_xy_m"],
                                       m["home_xy_m"], (g["lane_x_m"], ps2)):
        low, high = g["joint_limits_m"][axis]
        targets = [point[0 if axis == "x_joint" else 1] - origin for point in g["bin_centers_xy_m"]]
        if not all(low <= q <= high for q in [home, lane-origin, *targets]):
            raise ValueError(f"{axis}: home/lane/bin unreachable with these origins and limits")
    if any(a >= b for a, b in zip(g["product_size_m"][:2], g["bin_inner_size_xy_m"])):
        raise ValueError("product must fit the bin interior")
    for key in ("product_friction", "belt_friction", "cup_friction"):
        vector(p[key], 3, key)
        if any(v < 0 for v in p[key]):
            raise ValueError("friction must be nonnegative")
    exact_keys(p["belt_speed_scale"], ("front", "long"), "belt_speed_scale")
    for v in p["belt_speed_scale"].values():
        number(v, "belt_speed_scale", 0, True)
    for section, key in ((p, "product_mass_kg"), (p, "vacuum_adhesion_n"), (p, "dampratio")):
        number(section[key], key, 0, True)
    number(p["joint_damping"], "joint_damping", 0)
    exact_keys(p["link_inertials"], ("x_beam_link", "y_carriage_link", "cup_link", "pusher_link"), "link_inertials")
    for body, values in p["link_inertials"].items():
        exact_keys(values, ("mass_kg", "com_m", "diagonal_kg_m2"), body)
        number(values["mass_kg"], body+".mass_kg", 0, True)
        vector(values["com_m"], 3, body+".com_m")
        vector(values["diagonal_kg_m2"], 3, body+".diagonal_kg_m2", positive=True)
        inertia = values["diagonal_kg_m2"]
        if 2*max(inertia) > sum(inertia)+1e-12:
            raise ValueError(f"{body}: principal inertia violates triangle inequality")
    for section, key in ((p, "position_kp"), (m, "rates_m_s")):
        exact_keys(section[key], JOINTS, key)
        for value in section[key].values():
            number(value, key, 0, True)
    ordered(m["test_speed_range_m_s"], "test_speed_range_m_s")
    ordered(e["transit_speed_range_m_s"], "transit_speed_range_m_s")
    if m["test_speed_range_m_s"][0] <= 0 or e["transit_speed_range_m_s"][0] <= 0:
        raise ValueError("speed ranges must be positive")
    for key, value in m.items():
        if key not in {"rates_m_s", "home_xy_m", "test_speed_range_m_s", "long_speed_schedule"}:
            number(value, key, 0)
    if m["front_speed_m_s"] <= 0 or not m["test_speed_range_m_s"][0] <= m["long_speed_m_s"] <= m["test_speed_range_m_s"][1]:
        raise ValueError("invalid nominal belt speeds")
    if not 0 < m["a2_pick_m"] <= g["joint_limits_m"]["a2_joint"][1]:
        raise ValueError("A2 pick target exceeds stroke")
    for section in (s, e, t):
        for key, value in section.items():
            if section is e and key=='command_history_enabled':
                if type(value) is not bool: raise ValueError('command_history_enabled must be bool')
                continue
            if isinstance(value, list):
                continue
            number(value, key, 0)
    if s["end_switch_tolerance_m"] <= 0 or s["optical_detection_range_m"] <= 0:
        raise ValueError("positive sensor thresholds required")
    if any(2*s["end_switch_tolerance_m"] >= g["joint_limits_m"][j][1] for j in ("a1_joint", "a2_joint")):
        raise ValueError("end switch windows overlap")
    if type(t["sample_steps"]) is not int or t["sample_steps"] <= 0 or t["physics_step_s"] <= 0:
        raise ValueError("positive integer sampling steps and positive physics timestep required")
    period = t["sample_steps"]*t["physics_step_s"]
    if any(t[k] <= 0 for k in ("max_age_s", "silence_timeout_s", "cylinder_timeout_s", "run_budget_s", "track_timeout_max_s")):
        raise ValueError("timeouts must be positive")
    if t["max_sample_gap_s"] < period or t["silence_timeout_s"] < period:
        raise ValueError("freshness/silence limits conflict with sample period")
    if t["track_travel_budget_m"] <= ps2-g["long_belt_y_m"][0]:
        raise ValueError("track travel budget cannot reach PS2 from the transfer lane")
    if t["track_travel_budget_m"] >= g["long_belt_y_m"][1]-g["long_belt_y_m"][0]-g["product_size_m"][1]/2:
        raise ValueError("track travel budget exceeds modeled belt support")
    for key in ("delay_s", "jitter_s"):
        number(n[key], key, 0)
        if n[key] > t["run_budget_s"]:
            raise ValueError("network delay/jitter exceeds run budget")
    number(n["drop_probability"], "drop_probability", 0)
    if n["drop_probability"] > 1 or type(n["seed"]) is not int or n["seed"] < 0:
        raise ValueError("invalid network loss/seed")
    validate_outages(n.get('outage_windows_s',[]),t['run_budget_s'])
    pred=c["prediction"]
    if pred.get('backend','numeric_1d') not in {'numeric_1d','mujoco_belt'}: raise ValueError('unsupported prediction backend')
    if type(pred.get('native_threads',1)) is not int or not 1<=pred.get('native_threads',1)<=16: raise ValueError('native_threads must be an integer in 1..16')
    if type(pred["enabled"]) is not bool:
        raise ValueError("prediction.enabled must be bool")
    for key in ("horizon_s","step_s","wall_budget_s"):
        number(pred[key],"prediction."+key,0,True)
    number(pred["stop_margin_m"],"prediction.stop_margin_m",0)
    for key in ("speed_offsets_m_s","position_offsets","reaction_delays_s"):
        values=pred[key]
        if not isinstance(values,list) or not values or len(values)>20:
            raise ValueError("prediction scenario axes require 1..20 entries")
        for value in values:
            number(value,key,0 if key=="reaction_delays_s" else None)
        if len(set(values))!=len(values):
            raise ValueError("duplicate prediction scenarios")
    if not {-1,1}.issubset(pred["position_offsets"]):
        raise ValueError("prediction must include both uncertainty extremes -1 and +1")
    if pred["horizon_s"] < period+max(pred["reaction_delays_s"])+pred["step_s"]:
        raise ValueError("prediction horizon must include one control tick and modeled stop")
    scenarios=2*len(pred["speed_offsets_m_s"])*len(pred["position_offsets"])*len(pred["reaction_delays_s"])
    if scenarios>1000 or pred["horizon_s"]/pred["step_s"]>1000:
        raise ValueError("prediction workload exceeds static scenario/step cap")
    if e.get('command_history_enabled',False):
        if not {'command_gain_range','command_response_uncertainty_s'}<=e.keys():
            raise ValueError('history mode requires gain bounds and response uncertainty')
        ordered(e['command_gain_range'],'command_gain_range')
        if not 0<e['command_gain_range'][0]<=1<=e['command_gain_range'][1]:
            raise ValueError('positive command gain bounds must include the initial nominal gain 1')
    schedule=m.get('long_speed_schedule',[])
    if not isinstance(schedule,list) or len(schedule)>100: raise ValueError('speed schedule requires 0..100 entries')
    last=-1.0
    for entry in schedule:
        exact_keys(entry,('track_time_s','speed_m_s'),'long_speed_schedule')
        at=number(entry['track_time_s'],'track_time_s',0); v=number(entry['speed_m_s'],'speed_m_s',0)
        if at<=last or at>=t['run_budget_s'] or (v!=0 and not m['test_speed_range_m_s'][0]<=v<=m['test_speed_range_m_s'][1]):
            raise ValueError('speed schedule must be ordered, bounded and within configured speed range')
        last=at
    if schedule and not e.get('command_history_enabled',False):
        raise ValueError('speed schedules require command-history estimation')
    if 'health' in c:
        h=c['health']; exact_keys(h,('enabled','max_high_running_s','edge_slack_m'),'health')
        if type(h['enabled']) is not bool: raise ValueError('health.enabled must be bool')
        number(h['max_high_running_s'],'max_high_running_s',0,True)
        number(h['edge_slack_m'],'edge_slack_m',0)
    if 'reconfiguration' in c:
        r=c['reconfiguration']
        exact_keys(r,('enabled','warning_age_s','warning_ticks','degraded_long_speed_m_s',*(['adaptive'] if 'adaptive' in r else [])),'reconfiguration')
        if type(r['enabled']) is not bool: raise ValueError('reconfiguration.enabled must be bool')
        number(r['warning_age_s'],'warning_age_s',0,True)
        if not period<=r['warning_age_s']<min(t['max_age_s'],t['silence_timeout_s']):
            raise ValueError('warning age must be at least one sample and below hard age/silence limits')
        if type(r['warning_ticks']) is not int or not 1<=r['warning_ticks']<=100:
            raise ValueError('warning_ticks must be an integer in 1..100')
        number(r['degraded_long_speed_m_s'],'degraded_long_speed_m_s',0,True)
        if not m['test_speed_range_m_s'][0]<=r['degraded_long_speed_m_s']<=m['long_speed_m_s']:
            raise ValueError('degraded speed must be within tested range and cannot exceed nominal speed')
        if r['enabled'] and (not e.get('command_history_enabled') or not c.get('health',{}).get('enabled')):
            raise ValueError('reconfiguration requires command history and signal health')
        if 'adaptive' in r:
            a=r['adaptive']; exact_keys(a,('enabled','age_guard_s','pick_reserve_m','speed_step_m_s'),'adaptive')
            if type(a['enabled']) is not bool: raise ValueError('adaptive.enabled must be bool')
            number(a['age_guard_s'],'age_guard_s',0)
            number(a['pick_reserve_m'],'pick_reserve_m',0)
            number(a['speed_step_m_s'],'speed_step_m_s',0,True)
            if a['speed_step_m_s']>m['test_speed_range_m_s'][0]: raise ValueError('speed step exceeds minimum tested speed')
            if a['pick_reserve_m']>=e['pick_uncertainty_limit_m']-e['anchor_tolerance_m']-e['stop_coast_m']:
                raise ValueError('adaptive pickup budget must remain positive')
            if a['enabled'] and (not e.get('command_history_enabled') or not c.get('health',{}).get('enabled')):
                raise ValueError('adaptive requires command history and signal health')
    if 'recovery' in c:
        r=c['recovery']; exact_keys(r,('enabled','fresh_samples','settle_wait_s','max_hold_age_s'),'recovery')
        if type(r['enabled']) is not bool: raise ValueError('recovery.enabled must be bool')
        if type(r['fresh_samples']) is not int or not 2<=r['fresh_samples']<=100: raise ValueError('fresh_samples requires integer 2..100')
        number(r['settle_wait_s'],'settle_wait_s',0)
        number(r['max_hold_age_s'],'max_hold_age_s',0,True)
        if r['settle_wait_s']>=r['max_hold_age_s']: raise ValueError('settle wait must be below review hold-age limit')
        if r['enabled'] and not c.get('health',{}).get('enabled'): raise ValueError('recovery assessment requires signal health')
    if 'mechanics' in c:
        from parametric_cell import validate_mechanics
        validate_mechanics(c)
    return c


def load_config(path=None):
    def reject_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate configuration key: {key}")
            result[key] = value
        return result
    with Path(path or DEFAULT_CONFIG).open(encoding="utf-8-sig") as stream:
        return validate_config(json.load(stream, object_pairs_hook=reject_pairs))


def resolved_config(config=None, speed=None):
    c = deepcopy(config) if config is not None else load_config()
    if speed is not None:
        c["motion"]["long_speed_m_s"] = speed
    return validate_config(c)
