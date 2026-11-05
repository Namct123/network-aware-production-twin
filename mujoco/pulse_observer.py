"""Per-cycle gain from an upstream optical pulse; no downstream/pose fitting."""
from copy import deepcopy
import math
from innovation import EventResidual

def pulse_bounds(length,guard,travel,speed,period):
    if not all(type(x) in (int,float) and math.isfinite(x) for x in (length,guard,travel,speed,period)):
        raise ValueError("finite pulse inputs required")
    if not 0<=guard<length or min(travel,speed,period)<=0 or travel<=speed*period:raise ValueError("unresolved pulse")
    return [(length-guard)/(travel+speed*period),(length+guard)/(travel-speed*period)]

class PulseObserver:
    def __init__(self,config,settings,length_guard_m):
        self.core=EventResidual(config,settings);self.guard=length_guard_m
        if type(length_guard_m) not in (int,float) or not math.isfinite(length_guard_m) or not 0<=length_guard_m<config["geometry"]["product_size_m"][1]:raise ValueError("invalid length guard")
        self.previous=None;self.start=None;self.fit=None;self.first_alert=None;self.history_complete=False
    def issued(self,now,speed):self.core.issued(now,speed)
    def observe(self,frame,now):
        c=self.core;valid=frame is not None
        if valid:
            valid=(frame.quality.get("ps1")=="good" and type(frame.values.get("ps1")) is bool and frame.received_time_s<=now
                   and 0<=now-frame.source_time_s<=c.config["timing"]["max_age_s"]+1e-9
                   and (c.last_source is None or 0<frame.source_time_s-c.last_source<=c.config["timing"]["max_sample_gap_s"]+1e-9)
                   and (c.last_sequence is None or frame.sequence==c.last_sequence+1))
        if not valid:
            self.start=None;self.previous=None
            if self.fit is not None:self.history_complete=False
        elif self.fit is None:
            up=frame.values["ps1"]
            if self.previous is False and up is True:self.start=frame.source_time_s
            if self.previous is True and up is False and self.start is not None:
                window=c.commands.interval(self.start,frame.source_time_s)
                period=c.config["timing"]["physics_step_s"]*c.config["timing"]["sample_steps"]
                try:
                    bounds=pulse_bounds(c.config["geometry"]["product_size_m"][1],self.guard,window["distance_m"],window["max_speed_m_s"],period)
                    c.settings={**c.settings,"gain_bounds":bounds}
                    self.history_complete=True
                    self.fit={"at_s":frame.source_time_s,"pulse_start_s":self.start,"gain_bounds":bounds,"gain_point":c.config["geometry"]["product_size_m"][1]/window["distance_m"]}
                except ValueError:self.start=None
            self.previous=up
        result=c.observe(frame,now)
        if self.fit is None:result.update(status="pulse_unavailable",predicted_center_m=None,residual_m=None,alert=False,finding=None)
        elif result["alert"] and self.first_alert is None:self.first_alert={"time_s":now,"finding":result["finding"]}
        if self.fit is not None and frame is not None and frame.quality.get("ps2")!="good":self.history_complete=False
        usable=bool(valid and self.fit is not None and self.history_complete and frame.quality.get("ps2")=="good" and result["predicted_center_m"] is not None)
        return {**result,"pulse_fit":deepcopy(self.fit),"usable_for_monitoring":usable,
                "edge_history_complete":self.history_complete,"prediction_time_s":frame.source_time_s if result["predicted_center_m"] is not None and frame is not None else None,
                "observation_age_s":now-frame.source_time_s if frame is not None else None}
