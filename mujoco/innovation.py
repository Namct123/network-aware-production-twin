"""Observation-only downstream event residual. Never consumes plant pose/fault labels.

Bounds are engineering assumptions, not calibrated confidence intervals.
The anchor is the upstream falling edge: product centre = beam + half length.
"""
from copy import deepcopy
import math
from command_history import CommandHistory

class EventResidual:
    def __init__(self, config, settings):
        self.config=deepcopy(config); self.settings=deepcopy(settings)
        if set(settings)!={"gain_bounds","drift_m_s","confirm_samples"}: raise ValueError("invalid residual settings")
        gains=settings["gain_bounds"]
        if not isinstance(gains,list) or len(gains)!=2 or not all(type(v) in (int,float) and math.isfinite(v) for v in gains) or not 0<gains[0]<=gains[1]:
            raise ValueError("ordered positive gain bounds required")
        drift=settings["drift_m_s"]
        if type(drift) not in (int,float) or not math.isfinite(drift) or drift<0: raise ValueError("nonnegative drift required")
        if type(settings["confirm_samples"]) is not int or not 1<=settings["confirm_samples"]<=100: raise ValueError("confirmation count required")
        self.commands=CommandHistory();self.anchor=None;self.previous_up=None;self.previous_down=None
        self.last_source=None;self.last_received=None;self.last_sequence=None;self.seen_target=False;self.streak=0;self.first_alert=None

    def issued(self, now, speed):
        if self.last_received is None or now!=self.last_received:raise ValueError("command must follow the current observation tick")
        self.commands.record(now,speed)

    def observe(self, frame, now):
        if type(now) not in (int,float) or not math.isfinite(now) or now<0:raise ValueError("finite receiver time required")
        if self.last_received is not None and now<=self.last_received:raise ValueError("increasing receiver time required")
        self.last_received=now
        base={"time_s":now,"status":"no_anchor","predicted_center_m":None,"residual_m":None,"finding":None,"alert":False,
              "scope":"advisory_engineering_bounds_not_probability_or_fault_isolation"}
        if frame is None:
            self.streak=0;self.previous_up=self.previous_down=None
            return {**base,"status":"no_packet"}
        age=now-frame.source_time_s
        valid=(now>=frame.received_time_s and age>=-1e-9 and age<=self.config["timing"]["max_age_s"]+1e-9
               and (self.last_source is None or frame.source_time_s>self.last_source)
               and (self.last_sequence is None or frame.sequence>self.last_sequence))
        if not valid:
            self.streak=0;self.previous_up=self.previous_down=None
            return {**base,"status":"invalid_or_stale_frame"}
        continuous=(self.last_source is None or (frame.source_time_s-self.last_source<=self.config["timing"]["max_sample_gap_s"]+1e-9 and frame.sequence==self.last_sequence+1))
        self.last_source=frame.source_time_s;self.last_sequence=frame.sequence
        if not continuous:
            self.streak=0;self.previous_up=self.previous_down=None
        good=lambda key:frame.quality.get(key)=="good" and type(frame.values.get(key)) is bool
        up=frame.values.get("ps1") if good("ps1") else None
        down=frame.values.get("ps2") if good("ps2") else None
        g=self.config["geometry"];e=self.config["estimator"];half=g["product_size_m"][1]/2
        t=frame.source_time_s
        # Anchor only from a measured falling edge, never a controller estimate corrected by the target itself.
        if self.anchor is None and continuous and self.previous_up is True and up is False:
            self.anchor=(t,g["ps_y_m"]["ps1"]+half);self.seen_target=False
        finding=None
        if self.anchor is not None:
            anchor_time,y=self.anchor
            integral=self.commands.interval(anchor_time,t)
            dt=t-anchor_time;period=self.config["timing"]["physics_step_s"]*self.config["timing"]["sample_steps"]
            # Edge localization includes sampling travel and commanded response variation.
            tol=(e["anchor_tolerance_m"]+integral["max_speed_m_s"]*period*self.settings["gain_bounds"][1]
                 +e["command_response_uncertainty_s"]*integral["speed_variation_m_s"])
            widening=tol+self.settings["drift_m_s"]*dt+integral["stops"]*e["stop_coast_m"]
            low=y+self.settings["gain_bounds"][0]*integral["distance_m"]-widening
            high=y+self.settings["gain_bounds"][1]*integral["distance_m"]+widening
            target=g["ps_y_m"]["ps2"]-half
            residual=[target-high,target-low]
            base.update(status="within_assumed_model",predicted_center_m=[low,high],residual_m=residual)
            if not good("ps2"):
                base["status"]="target_unavailable";self.streak=0
            else:
                rising=continuous and self.previous_down is False and down is True
                if rising:
                    self.seen_target=True
                    if residual[0]>e["anchor_tolerance_m"]:finding="target_earlier_than_interval"
                    elif residual[1]<-e["anchor_tolerance_m"]:finding="target_later_than_interval"
                if not self.seen_target and down is False and low>target+e["anchor_tolerance_m"]:
                    finding="expected_target_edge_missing"
                self.streak=self.streak+1 if finding else 0
                # A single sampled edge cannot be repeated for persistence confirmation.
                alert=bool(finding) and (rising or self.streak>=self.settings["confirm_samples"])
                base.update(finding=finding,alert=alert,status="prediction_observation_mismatch" if alert else "within_assumed_model")
                if alert and self.first_alert is None:self.first_alert={"time_s":now,"finding":finding}
        self.previous_up=up;self.previous_down=down
        return base
