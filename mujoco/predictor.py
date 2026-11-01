"""Bounded 1D counterfactual rollouts from estimates; never clones plant truth."""

from itertools import product
import math
import time


class Predictor:
    def __init__(self, config, clock=None):
        self.parameters=config["prediction"].copy()
        self.period=config["timing"]["physics_step_s"]*config["timing"]["sample_steps"]
        self.limit=(config["geometry"]["long_belt_y_m"][1]
                    -config["geometry"]["product_size_m"][1]/2-self.parameters["stop_margin_m"])
        self.coast=config["estimator"]["stop_coast_m"]
        self.drift=config["estimator"]["drift_m_s"]
        self.clock=clock or time.perf_counter

    def rollout(self, estimate, source_time_s, now_s):
        values=(estimate.y_m,estimate.velocity_m_s,estimate.uncertainty_m,source_time_s,now_s)
        if any(v is None or not math.isfinite(v) for v in values):
            raise ValueError("finite timestamped position/speed/uncertainty required")
        if now_s<source_time_s or estimate.velocity_m_s<0 or estimate.uncertainty_m<0:
            raise ValueError("invalid forward estimate or age")
        p=self.parameters
        start=self.clock()
        age=now_s-source_time_s
        uncertainty=estimate.uncertainty_m+self.drift*age
        axes=list(product(p["position_offsets"],p["speed_offsets_m_s"],p["reaction_delays_s"]))
        expected=2*len(axes)
        completed=steps=0
        margins={}
        for policy,advance in (("HOLD",0.0),("CONTINUE",self.period)):
            worst=math.inf
            for offset,dv,reaction in axes:
                speed=max(0.0,estimate.velocity_m_s+dv)
                initial=estimate.y_m+offset*uncertainty+speed*age
                cutoff=advance+reaction
                minimum=math.inf
                count=math.ceil(p["horizon_s"]/p["step_s"])
                for i in range(count+1):
                    if self.clock()-start>p["wall_budget_s"]:
                        return {"status":"deadline_exceeded","action":"HOLD",
                            "reason":"prediction_deadline_exceeded","completed_scenarios":completed,
                            "expected_scenarios":expected,"rollout_steps":steps,
                            "compute_ms":(self.clock()-start)*1000,"margins_m":margins}
                    t=min(i*p["step_s"],p["horizon_s"])
                    # ponytail: constant-speed motion, then a one-grid-step coast.
                    # This is a stop-distance surrogate, not MuJoCo contact dynamics.
                    coast=self.coast*min(1.0,max(0.0,(t-cutoff)/p["step_s"]))
                    y=initial+speed*min(t,cutoff)+coast
                    minimum=min(minimum,self.limit-y)
                    steps+=1
                worst=min(worst,minimum)
                completed+=1
            margins[policy]=worst
        action="CONTINUE" if margins["CONTINUE"]>=0 else "HOLD"
        reason=("predictive_continue" if action=="CONTINUE" else
                "predictive_stop_margin" if margins["HOLD"]>=0 else "predictive_no_admissible_continue")
        elapsed=self.clock()-start
        # An overrun on completion is also a missed deadline, not a successful plan.
        if elapsed>p["wall_budget_s"]:
            action,reason="HOLD","prediction_deadline_exceeded"
        return {"status":"complete" if elapsed<=p["wall_budget_s"] else "deadline_exceeded",
                "action":action,"reason":reason,"completed_scenarios":completed,
                "expected_scenarios":expected,"rollout_steps":steps,
                "compute_ms":elapsed*1000,"margins_m":margins,
                "estimate_age_s":age,"horizon_s":p["horizon_s"],
                "model":"1D kinematic stop surrogate; no physical safety guarantee"}
