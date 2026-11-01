"""Request, comparison and job-lifecycle checks without a MuJoCo installation."""
from copy import deepcopy
import json
import math
import tempfile
import threading
import unittest
from unittest.mock import patch

from experiments import Experiments, BusyError, paired_comparison, trial_config, validate_request, write_json

REQUEST={'profile':'simulation','speed':.16,'fault':'ps2_stuck_low','delay_ms':0,
         'jitter_ms':0,'loss_pct':0,'seed':0,'bin':1,'predictive':True,
         'assume_open_loop':True,'compare':True}


class ExperimentTests(unittest.TestCase):
    def test_request_rejects_paths_commands_unknowns_and_nonfinite(self):
        self.assertEqual(validate_request(REQUEST),REQUEST)
        for key,value in [('profile','../../simulation'),('fault','none; exit'),('speed',True),
                          ('speed',math.nan),('speed',.25),('loss_pct',101),('seed',1.2),
                          ('bin',0),('compare',1),('delay_ms',-1)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                validate_request({**REQUEST,key:value})
        with self.assertRaises(ValueError): validate_request({**REQUEST,'command':'whoami'})

    def test_pair_differs_only_in_prediction_enable(self):
        request={**REQUEST,'delay_ms':20,'jitter_ms':10,'loss_pct':5,'seed':42}
        base,pred=trial_config(request,False),trial_config(request,True)
        self.assertFalse(base['prediction']['enabled'])
        base['prediction']['enabled']=True
        self.assertEqual(base,pred)
        self.assertEqual(pred['network']['seed'],42)
        self.assertEqual(pred['network']['drop_probability'],.05)
        self.assertEqual(REQUEST['delay_ms'],0)

    def test_comparison_does_not_claim_speedup_for_holds_or_failed_placement(self):
        a={'controller_state':'HOLD','hold_time_s':6.76,'hold_reason':'timeout:TRACK:ps2',
           'simulation_time_s':7.08,'placement_pass_evaluator_only':None}
        b={**a,'hold_time_s':6.72,'hold_reason':'predictive_stop_margin'}
        self.assertAlmostEqual(paired_comparison(a,b)['earlier_hold_s'],.04)
        self.assertIsNone(paired_comparison(a,b)['cycle_time_delta_s'])
        self.assertIsNone(paired_comparison(a,{**b,'hold_reason':'telemetry_timeout'})['earlier_hold_s'])
        done={**a,'controller_state':'DONE','placement_pass_evaluator_only':True}
        self.assertIsNone(paired_comparison(done,{**done,'placement_pass_evaluator_only':False})['cycle_time_delta_s'])

    def test_disabled_busy_and_failed_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            disabled=Experiments(directory=folder)
            with self.assertRaises(BusyError):disabled.submit(REQUEST)
            manager=Experiments(True,directory=folder)
            manager.active='existing'
            with self.assertRaises(BusyError):manager.submit(REQUEST)
            manager.active=None
            finished=threading.Event()
            original=manager.execute
            def execute(job):
                try:original(job)
                finally:finished.set()
            with patch.object(manager,'execute',side_effect=execute),patch('experiments.shutil.which',return_value=None):
                status=manager.submit(REQUEST)
                self.assertTrue(finished.wait(5))
            row=manager.status(status['id'])
            self.assertEqual(row['state'],'failed')
            self.assertIn('WSL',row['error'])
            self.assertIsNone(manager.active)
            self.assertEqual(manager.recent()[0]['id'],status['id'])
            stale={**row,'state':'running'}
            write_json(manager.folder(row['id'])/'job.json',stale)
            self.assertEqual(manager.status(row['id'])['state'],'interrupted')
            with self.assertRaises(ValueError):manager.folder('../escape')


if __name__=='__main__':
    unittest.main()
