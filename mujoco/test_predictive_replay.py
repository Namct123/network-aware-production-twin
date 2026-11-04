"""Forecast values remain comparable; only measured computation durations are ignored."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from config import load_config
from predictor import Predictor
from stream_archive import logical
from study_predictive_replay import HERE, injected_deadline, load_plan


class PredictiveReplayTest(unittest.TestCase):
    def test_only_duration_fields_are_excluded(self):
        original = {'core_step_ms':1.,'estimate':{'y_m':.1},
            'prediction':{'compute_ms':2.,'status':'complete','action':'CONTINUE','margins_m':{'CONTINUE':.01}}}
        changed = deepcopy(original); changed['core_step_ms']=3; changed['prediction']['compute_ms']=4
        self.assertEqual(logical(original),logical(changed))
        changed['prediction']['margins_m']['CONTINUE']=-.01
        self.assertNotEqual(logical(original),logical(changed))
        self.assertEqual(original['prediction']['compute_ms'],2.)

    def test_negative_control_injects_elapsed_time_and_restores_clock(self):
        config=load_config(HERE/'configs/reconfigurable_cell_20261030.json')
        predictor=Predictor(config); clock=predictor.clock
        result=injected_deadline(Predictor.rollout)(predictor,
            SimpleNamespace(y_m=0.,velocity_m_s=.1,uncertainty_m=.001),0.,0.)
        self.assertEqual(result['status'],'deadline_exceeded'); self.assertEqual(result['action'],'HOLD')
        self.assertEqual(result['completed_scenarios'],0); self.assertIs(predictor.clock,clock)

    def test_plan_is_bounded(self):
        plan=load_plan(HERE/'experiments/predictive_replay_20261104.json')
        self.assertEqual(len(plan['cases']),6)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'plan.json'; plan['repetitions']=100; path.write_text(json.dumps(plan))
            with self.assertRaises(ValueError): load_plan(path)


if __name__=='__main__':unittest.main()
