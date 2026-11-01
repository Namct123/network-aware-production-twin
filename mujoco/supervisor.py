"""Receding-horizon CONTINUE/HOLD selection, without ground-truth access."""

import math
from dataclasses import replace
from predictor import Predictor


class Supervisor:
    def __init__(self, config, predictor=None):
        self.enabled=config["prediction"]["enabled"]
        self.model_description='1D counterfactual stop surrogate, not full MuJoCo rollouts'
        if predictor is not None: self.predictor=predictor
        elif config['prediction'].get('backend')=='mujoco_belt':
            from physics_predictor import MuJoCoBeltPredictor
            self.predictor=MuJoCoBeltPredictor(config)
            self.model_description='independent MuJoCo belt/block contact forecast, not full-cell rollouts'
        else: self.predictor=Predictor(config)
        self.records=[]

    def tick(self, controller, now):
        if not self.enabled or controller.phase!="TRACK" or controller.command["long"]<=0:
            return None
        estimate=controller.estimator.estimate
        if estimate.reason!="tracking" or estimate.anchors<1 or controller.last_time is None:
            return None
        try:
            if controller.estimator.history_mode:
                estimate=replace(estimate,velocity_m_s=controller.prediction_speed_bound_m_s)
            result=self.predictor.rollout(estimate,controller.last_time,now)
        except (ValueError,OverflowError) as error:
            result={"status":"invalid_estimate","action":"HOLD","reason":"prediction_invalid_estimate",
                    "completed_scenarios":0,"expected_scenarios":0,"rollout_steps":0,
                    "compute_ms":None,"margins_m":{},"error":str(error)}
        result.update(time_s=now,estimate_source_sequence=controller.estimate_sequence)
        if controller.estimator.history_mode:
            result['evaluated_speed_bound_m_s']=estimate.velocity_m_s
        self.records.append(result)
        if result["action"]=="HOLD":
            controller.hold(result["reason"],now)
        return result

    def summary(self):
        durations=sorted(r["compute_ms"] for r in self.records if r["compute_ms"] is not None)
        return {"enabled":self.enabled,"calls":len(self.records),
                "completed_scenarios":sum(r["completed_scenarios"] for r in self.records),
                "rollout_steps":sum(r["rollout_steps"] for r in self.records),
                "deadline_misses":sum(r["status"]=="deadline_exceeded" for r in self.records),
                "invalid_inputs":sum(r["status"]=="invalid_estimate" for r in self.records),
                "hold_selections":sum(r["action"]=="HOLD" for r in self.records),
                "compute_p95_ms":durations[math.ceil(.95*len(durations))-1] if durations else None,
                "compute_max_ms":max(durations) if durations else None,
                "model":self.model_description}
