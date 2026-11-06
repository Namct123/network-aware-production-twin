"""Plant-independent event-window monitor; caller supplies validated source evidence."""
import math

class EventWindow:
    def __init__(self,interval,available_at_s,confirm_samples=2):
        if len(interval)!=2 or not all(type(v) in (int,float) and math.isfinite(v) for v in [*interval,available_at_s]) or not 0<=available_at_s<=interval[0]<=interval[1]:raise ValueError("finite causal event window required")
        if type(confirm_samples) is not int or not 1<=confirm_samples<=100:raise ValueError("bounded confirmation count required")
        self.interval=list(interval);self.available=available_at_s;self.confirm=confirm_samples
        self.previous=None;self.seen=False;self.streak=0;self.last_source=None;self.valid=True

    def observe(self,source_time_s,active,eligible=True):
        if type(eligible) is not bool:raise ValueError("explicit evidence eligibility required")
        result={"status":"within_empirical_envelope","finding":None,"alert":False}
        if not eligible:self.valid=False
        if not self.valid:
            self.previous=None;self.streak=0
            return {**result,"status":"evidence_unavailable"}
        if type(source_time_s) not in (int,float) or not math.isfinite(source_time_s) or source_time_s<self.available or (self.last_source is not None and source_time_s<=self.last_source) or type(active) is not bool:raise ValueError("increasing source time and resolved binary event required")
        self.last_source=source_time_s
        if active and self.previous is None:
            self.seen=True;result["status"]="target_present_without_resolved_edge"
        else:
            rising=self.previous is False and active;finding=None
            if rising:
                self.seen=True
                if source_time_s<self.interval[0]-1e-9:finding="target_earlier_than_eta_envelope"
                elif source_time_s>self.interval[1]+1e-9:finding="target_later_than_eta_envelope"
            if not self.seen and not active and source_time_s>self.interval[1]+1e-9:finding="expected_target_edge_missing"
            self.streak=self.streak+1 if finding else 0
            alert=bool(finding) and (rising or self.streak>=self.confirm)
            result.update(finding=finding,alert=alert,status="prediction_observation_mismatch" if alert else result["status"])
        self.previous=active
        return result
