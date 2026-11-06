"""Single-product causal ETA event monitor; advisory only, no actuator authority."""
from copy import deepcopy
import math
from eta_ml import predict,predict_from_pulse
from pulse_observer import PulseObserver


def calibration_context(config):
    g=config["geometry"]
    return {"product_length_m":g["product_size_m"][1],"sensor_gap_m":g["ps_y_m"]["ps2"]-g["ps_y_m"]["ps1"],
            "sample_period_s":config["timing"]["physics_step_s"]*config["timing"]["sample_steps"]}


def calibration_settings(model, examples, pulse_settings, length_guard_m, config):
    """Use only a separate normal calibration set, never held-out fault labels."""
    errors={name:[] for name in ("pulse","constant","ml")}
    for e in examples:
        estimates={"pulse":e["pulse_eta_s"],"constant":max(e["available_at_s"],e["pulse_eta_s"]+model["constant_bias_s"]),"ml":predict(model,e)["eta_s"]}
        for name,value in estimates.items():errors[name].append(abs(value-e["target_at_s"]))
    if not examples:raise ValueError("separate normal calibration rows required")
    return {"kind":"eta_event_monitor_v1","radii_s":{n:max(v) for n,v in errors.items()},"calibration_rows":len(examples),
            "calibration_context":calibration_context(config),"confirm_samples":pulse_settings["confirm_samples"],"pulse_settings":deepcopy(pulse_settings),"length_guard_m":length_guard_m,
            "scope":"Empirical calibration maxima; no statistical guarantee. Constant forward single-product cycle, advisory only."}


class EtaEventMonitor:
    def __init__(self,config,model,settings,method="ml"):
        if method not in ("pulse","constant","ml") or settings.get("kind")!="eta_event_monitor_v1":raise ValueError("supported ETA method/settings required")
        if set(settings["radii_s"])!={"pulse","constant","ml"} or not all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in settings["radii_s"].values()):raise ValueError("finite nonnegative calibrated radii required")
        if type(settings["confirm_samples"]) is not int or not 1<=settings["confirm_samples"]<=100:raise ValueError("bounded confirmation count required")
        expected=settings["calibration_context"];actual=calibration_context(config)
        if set(expected)!=set(actual) or not all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in expected.values()):raise ValueError("explicit positive calibration context required")
        self.context_matches=all(math.isclose(actual[k],v,rel_tol=0,abs_tol=1e-12) for k,v in expected.items())
        self.pulse=PulseObserver(config,settings["pulse_settings"],settings["length_guard_m"])
        self.model=deepcopy(model);self.settings=deepcopy(settings);self.method=method
        self.speed=None;self.constant=True;self.prediction=None;self.outside=False
        self.previous_down=None;self.seen=False;self.streak=0;self.first_alert=None

    def issued(self,now,speed):
        self.pulse.issued(now,speed)
        if self.speed is None:self.speed=speed
        elif speed!=self.speed:self.constant=False

    def observe(self,frame,now):
        pulse=self.pulse.observe(frame,now)
        result={"time_s":now,"source_time_s":frame.source_time_s if frame else None,"authority":"advisory_only",
                "requested_method":self.method,"basis":None,"status":"evidence_unavailable","finding":None,"alert":False,
                "eta_interval_s":None,"outside_training_feature_box":self.outside,"fallback_reason":None,"data_issue":None}
        # A missing sample cannot establish absence through receiver wall time.
        if not pulse["usable_for_monitoring"]:
            self.previous_down=None;self.streak=0
            issue=("no_packet" if frame is None else "stale_packet" if now-frame.source_time_s>self.pulse.core.config["timing"]["max_age_s"]+1e-9 else "signal_quality_unavailable" if any(frame.quality.get(k)!="good" for k in ("ps1","ps2")) else "edge_history_incomplete" if self.pulse.fit is not None else "upstream_pulse_not_ready")
            return {**result,"status":pulse["status"] if self.pulse.fit is None else "history_or_transport_unusable","data_issue":issue}
        down=frame.values["ps2"];t=frame.source_time_s
        if self.prediction is None and self.context_matches and self.constant and self.speed is not None and self.speed>0:
            g=self.pulse.core.config["geometry"];d=g["ps_y_m"]["ps2"]-g["ps_y_m"]["ps1"]-g["product_size_m"][1]
            learned=predict_from_pulse(self.model,self.pulse.fit,self.speed,d)
            self.outside=not learned["inside_training_feature_box"]
            point=self.pulse.fit["at_s"]+d/(self.speed*self.pulse.fit["gain_point"])
            eta={"pulse":point,"constant":max(self.pulse.fit["at_s"],point+self.model["constant_bias_s"]),"ml":learned["eta_s"]}[self.method]
            radius=self.settings["radii_s"][self.method]
            self.prediction=[max(self.pulse.fit["at_s"],eta-radius),eta+radius]
        reason="profile_outside_calibration" if not self.context_matches else "command_changed" if not self.constant else "outside_training_feature_box" if self.outside else None
        result.update(outside_training_feature_box=self.outside,fallback_reason=reason)
        if reason is not None:
            # ponytail: reuse engineering pulse bounds; do not invent a second fallback model.
            result.update(basis="engineering_pulse_fallback",status=pulse["status"],finding=pulse["finding"],alert=pulse["alert"])
        elif self.prediction is not None:
            result.update(basis="eta_"+self.method,status="within_empirical_envelope",eta_interval_s=list(self.prediction))
            if down and self.previous_down is None:
                self.seen=True;result["status"]="target_present_without_resolved_edge"
            else:
                rising=self.previous_down is False and down
                finding=None
                if rising:
                    self.seen=True
                    if t<self.prediction[0]-1e-9:finding="target_earlier_than_eta_envelope"
                    elif t>self.prediction[1]+1e-9:finding="target_later_than_eta_envelope"
                if not self.seen and not down and t>self.prediction[1]+1e-9:finding="expected_target_edge_missing"
                self.streak=self.streak+1 if finding else 0
                alert=bool(finding) and (rising or self.streak>=self.settings["confirm_samples"])
                result.update(finding=finding,alert=alert,status="prediction_observation_mismatch" if alert else result["status"])
        self.previous_down=down
        if result["alert"] and self.first_alert is None:
            self.first_alert={"time_s":now,"source_time_s":t,"basis":result["basis"],"finding":result["finding"]}
        return result
