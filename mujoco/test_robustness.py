"""Study validation and honest aggregation, without running a simulator."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from check_robustness import prepare,assess,aggregate,error_coverage,HERE
from config import load_config

class RobustnessTest(unittest.TestCase):
    def inputs(self):
        return (load_config(HERE/'configs/reconfigurable_cell_20261030.json'),
                json.loads((HERE/'experiments/robustness_smoke.json').read_text()))

    def test_pairs_share_parameters_and_leave_base_unchanged(self):
        base,plan=self.inputs(); original=deepcopy(base)
        jobs=prepare(base,plan)
        self.assertEqual(len(jobs),6); self.assertEqual(base,original)
        a,b=deepcopy(jobs[0]['config']),deepcopy(jobs[1]['config'])
        a['reconfiguration']['enabled']=True
        self.assertEqual(a,b)

    def test_reject_bad_plan_before_any_run(self):
        base,plan=self.inputs()
        for patch in ('duplicate','path','value','seed','name'):
            p=deepcopy(plan)
            if patch=='duplicate': p['scenarios'].append(p['scenarios'][0])
            if patch=='path': p['scenarios'][0]['patch']={'estimator.pick_uncertainty_limit_m':1}
            if patch=='value': p['scenarios'][0]['patch']={'network.drop_probability':2}
            if patch=='seed': p['seeds']=[True]
            if patch=='name': p['scenarios'][0]['name']='../escape'
            with self.assertRaises(ValueError): prepare(base,p)

    def test_hold_is_not_placement_and_unsupported_hold_fails(self):
        summary={'controller_state':'HOLD','placement_pass_evaluator_only':None,'hold_product_supported_evaluator_only':True}
        rows=[{'mode':'DEGRADED','phase':'TRACK','selected_long_speed_m_s':.12}]
        self.assertTrue(assess(summary,rows,True,.12)['verification_pass'])
        summary['hold_product_supported_evaluator_only']=False
        self.assertFalse(assess(summary,rows,True,.12)['verification_pass'])
        summary['hold_product_supported_evaluator_only']=True
        rows[0]['selected_long_speed_m_s']=.2
        self.assertFalse(assess(summary,rows,True,.12)['verification_pass'])

    def test_cycle_mean_excludes_holds_and_exceptions(self):
        rows=[{'scenario':'s','policy':'enabled','fault':'none','controller_state':'DONE','simulation_time_s':10,'verification_pass':True},
              {'scenario':'s','policy':'enabled','fault':'none','controller_state':'HOLD','simulation_time_s':1,'verification_pass':True},
              {'scenario':'s','policy':'enabled','fault':'none','exception':'error','verification_pass':False}]
        g=next(g for g in aggregate(rows) if g['policy']=='enabled')
        self.assertEqual(g['mean_completed_cycle_s'],10)
        self.assertEqual(g['verification_failures'],1)
        self.assertEqual(g['hold_without_injected_sensor_fault'],1)

    def test_error_bound_coverage_is_observed_and_checks_alignment(self):
        truth=[{'sequence':i,'y_estimation_error_m':e} for i,e in enumerate([None,.01,.03])]
        decisions=[{'sequence':i,'estimate':{'uncertainty_m':.02}} for i in range(3)]
        r=error_coverage(truth,decisions)
        self.assertEqual(r['error_bound_samples'],2)
        self.assertEqual(r['error_bound_observed_coverage'],.5)
        self.assertAlmostEqual(r['error_bound_max_excess_m'],.01)
        with self.assertRaises(ValueError): error_coverage(truth,decisions[:-1])

if __name__=='__main__': unittest.main()
