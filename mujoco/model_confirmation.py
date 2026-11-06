"""Conditional position qualification; never creates missing actuation evidence."""
import math

def qualify(record,observer,now,stopped,settle,zone,config,prerequisites_verified=False):
    if type(prerequisites_verified) is not bool:raise ValueError("explicit verified-prerequisites flag required")
    if not math.isfinite(now) or not math.isfinite(settle) or settle<=0 or len(zone)!=2 or not all(math.isfinite(v) for v in zone) or not zone[0]<zone[1]:raise ValueError("finite ordered qualification inputs required")
    if stopped is not None and (not math.isfinite(stopped) or stopped<0):raise ValueError("valid observed stop time required")
    result={"conditional_position_ok":False,"release_eligible":False,"interval_now_m":None,"reason":"not_settled"}
    if stopped is None or now-stopped+1e-9<settle:return result
    if not record["usable_for_monitoring"] or observer.fit is None:return {**result,"reason":"unusable_observations"}
    low,high=record["predicted_center_m"];source=record["prediction_time_s"]
    if not all(math.isfinite(v) for v in (low,high,source,now)) or low>high or source>now:raise ValueError("ordered finite prediction required")
    h=observer.core.commands
    stopped_history=h.interval(stopped,now)
    if stopped_history["distance_m"]>0 or stopped_history["end_speed_m_s"]>0:return {**result,"reason":"stop_not_maintained"}
    past=h.interval(source,now);lo,hi=observer.fit["gain_bounds"];e=config["estimator"]
    allowance=e["drift_m_s"]*(now-source)+e["command_response_uncertainty_s"]*past["speed_variation_m_s"]+past["stops"]*e["stop_coast_m"]
    bounds=[low+lo*past["distance_m"]-allowance,high+hi*past["distance_m"]+allowance]
    inside=zone[0]<=bounds[0] and bounds[1]<=zone[1]
    return {"conditional_position_ok":inside,"release_eligible":inside and prerequisites_verified,"interval_now_m":bounds,
            "reason":"interval_outside_zone" if not inside else "model_or_actuation_assumptions_unverified" if not prerequisites_verified else "qualified"}
