"""Check rollout bounds, deadlines and supervisory decisions without MuJoCo."""

from copy import deepcopy
import math
import unittest
from config import load_config, validate_config
from estimator import Estimate
from predictor import Predictor
from sequence import Sequence
from sensor_model import SensorModel
from supervisor import Supervisor


class PredictionTest(unittest.TestCase):
    def config(self):
        c=load_config(); c["prediction"]["enabled"]=True
        c["prediction"]["wall_budget_s"]=1.0  # Functional checks do not benchmark host scheduling.
        return c

    def test_all_scenarios_complete_and_input_is_not_mutated(self):
        e=Estimate(.0,.16,.003,1,"tracking"); original=deepcopy(e)
        r=Predictor(self.config()).rollout(e,1,1)
        self.assertEqual(r["action"],"CONTINUE")
        self.assertEqual(r["completed_scenarios"],54)
        self.assertEqual(r["rollout_steps"],54*26)
        self.assertEqual(e,original)

    def test_horizon_rollout_matches_analytic_stop_distance(self):
        c=self.config(); e=Estimate(.10,.16,.003,1,"tracking")
        r=Predictor(c).rollout(e,1,1)
        expected=.214-(.10+.003+.18*(.02+.02)+.002)
        self.assertAlmostEqual(r["margins_m"]["CONTINUE"],expected)
        self.assertGreater(r["margins_m"]["HOLD"],r["margins_m"]["CONTINUE"])

    def test_future_one_tick_motion_can_be_rejected_while_hold_fits(self):
        e=Estimate(.197,.16,.006,1,"tracking")
        r=Predictor(self.config()).rollout(e,1,1)
        self.assertEqual(r["action"],"CONTINUE")
        e.y_m=.200
        r=Predictor(self.config()).rollout(e,1,1)
        self.assertEqual(r["action"],"HOLD")
        self.assertEqual(r["reason"],"predictive_stop_margin")
        self.assertGreaterEqual(r["margins_m"]["HOLD"],0)

    def test_unrecoverable_margin_and_age_are_explicit(self):
        r=Predictor(self.config()).rollout(Estimate(.213,.16,.006,1,"tracking"),1,1)
        self.assertEqual(r["reason"],"predictive_no_admissible_continue")
        p=Predictor(self.config()); e=Estimate(.10,.16,.003,1,"tracking")
        self.assertLess(p.rollout(e,1,1.05)["margins_m"]["CONTINUE"],p.rollout(e,1,1)["margins_m"]["CONTINUE"])

    def test_deadline_expiry_cannot_select_from_an_optimistic_prefix(self):
        class Clock:
            def __init__(self): self.t=0
            def __call__(self): self.t+=.01; return self.t
        c=self.config(); c["prediction"]["wall_budget_s"]=.015
        r=Predictor(c,clock=Clock()).rollout(Estimate(.0,.16,.003,1,"tracking"),0,0)
        self.assertEqual(r["status"],"deadline_exceeded")
        self.assertEqual(r["action"],"HOLD")
        self.assertLess(r["completed_scenarios"],r["expected_scenarios"])

    def test_config_rejects_unsafe_horizon_and_missing_uncertainty_extremes(self):
        for patch in ({"horizon_s":.01},{"position_offsets":[0,1]},{"enabled":1},{"step_s":0}):
            c=self.config(); c["prediction"].update(patch)
            with self.assertRaises(ValueError): validate_config(c)
        old=load_config(); del old["prediction"]
        self.assertFalse(validate_config(old)["prediction"]["enabled"])

    def test_invalid_estimates_do_not_silently_generate_scenarios(self):
        for e in (Estimate(),Estimate(math.nan,.16,.01),Estimate(.1,-.1,.01)):
            with self.assertRaises(ValueError): Predictor(self.config()).rollout(e,0,0)

    def test_supervisor_uses_only_controller_belief_and_keeps_vacuum(self):
        c=self.config(); ctl=Sequence(config=c,assume_open_loop=True)
        ctl.phase="TRACK"; ctl.command.update(long=.16,vacuum=True)
        ctl.last_time=1; ctl.estimate_sequence=50
        ctl.estimator.estimate=Estimate(.200,.16,.006,1,"tracking")
        supervisor=Supervisor(c); r=supervisor.tick(ctl,1)
        self.assertEqual(r["action"],"HOLD")
        self.assertEqual(ctl.phase,"HOLD")
        self.assertTrue(ctl.command["vacuum"])
        self.assertEqual(supervisor.summary()["hold_selections"],1)

    def test_disabled_and_unobserved_states_do_not_plan(self):
        c=load_config(); ctl=Sequence(config=c)
        self.assertIsNone(Supervisor(c).tick(ctl,0))
        c=self.config(); ctl=Sequence(config=c); ctl.phase="TRACK"; ctl.command["long"]=.16
        self.assertIsNone(Supervisor(c).tick(ctl,0))

    def test_invalid_estimate_latches_hold_instead_of_crashing_controller(self):
        c=self.config(); ctl=Sequence(config=c)
        ctl.phase="TRACK"; ctl.command["long"]=.16; ctl.last_time=0
        ctl.estimator.estimate=Estimate(math.nan,.16,.003,1,"tracking")
        s=Supervisor(c); r=s.tick(ctl,0)
        self.assertEqual(r["reason"],"prediction_invalid_estimate")
        self.assertEqual(ctl.phase,"HOLD")
        self.assertEqual(s.summary()["invalid_inputs"],1)
        self.assertIsNone(ctl.estimator.estimate.as_dict()["y_m"])

    def test_delayed_estimator_uses_historical_belt_command(self):
        c=self.config(); ctl=Sequence(config=c); sensor=SensorModel(config=c)
        ctl.phase="TRACK"; ctl.command["long"]=.16
        def sample(t,ps1=False):
            return sensor.sample(dict(time_s=t,ps1=ps1,ps2=False,a1_m=0,a2_m=0))[0]
        ctl.tick(sample(0),.02,source_belt_command=.16)
        ctl.tick(sample(.02,True),.04,source_belt_command=.16)
        old_y=ctl.estimator.estimate.y_m
        ctl.phase="ALIGN"; ctl.entered=0; ctl.duration=100; ctl.command["long"]=0
        ctl.tick(sample(.04),.06,source_belt_command=.16)
        self.assertAlmostEqual(ctl.estimator.estimate.y_m-old_y,.16*.02)


if __name__=="__main__": unittest.main()
