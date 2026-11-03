"""Study design checks are independent of MuJoCo and do not tune physics."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from config import load_config
from study_model_boundary import jobs,pair,summarize,variant

HERE=Path(__file__).resolve().parent


class ModelBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.base=load_config(HERE/'configs/reconfigurable_cell_20261030.json')
        self.plan=json.loads((HERE/'experiments/model_boundary_20261103.json').read_text())

    def test_fixed_factorial_grid_and_no_input_mutation(self):
        before=deepcopy(self.base);grid=jobs(self.base,self.plan)
        self.assertEqual(len(grid),144)
        self.assertEqual(len({tuple(r.values()) for r in grid}),144)
        c=variant(self.base,self.plan,.25)
        self.assertEqual(c['plant']['belt_friction'][0],self.base['plant']['belt_friction'][0]*.25)
        self.assertEqual(c['plant']['product_friction'][1:],self.base['plant']['product_friction'][1:])
        self.assertEqual(c['estimator'],self.base['estimator']);self.assertEqual(self.base,before)
        self.assertEqual(c['prediction']['wall_budget_s'],5)

    def test_invalid_or_unbounded_plan_rejected(self):
        for key,value in [('speed_m_s',[True]),('age_s',[-.1]),('sliding_friction_scale',[0]),('distance_to_limit_m',[0,0]),('uncertainty_m',float('nan')),('native_threads',False),('functional_budget_s',.001)]:
            p=deepcopy(self.plan);p[key]=value
            with self.assertRaises(ValueError,msg=key):jobs(self.base,p)
        p=deepcopy(self.plan);p['speed_m_s']=list(range(30))
        with self.assertRaisesRegex(ValueError,'500'):jobs(self.base,p)

    def test_incomplete_cases_excluded_and_disagreements_kept(self):
        a={'action':'CONTINUE'};b={'action':'HOLD'}
        self.assertEqual(pair(a,b),'reduced_continue_contact_hold')
        self.assertEqual(pair(b,a),'reduced_hold_contact_continue')
        rows=[{'complete':True,'forward_pair':pair(a,b),'full_pair':pair(a,b),'contact_forward':b,'contact_full':b,'forward_margin_delta_m':-.003},
              {'complete':False,'error':'fixture failure'}]
        r=summarize(rows,2)
        self.assertEqual(r['complete'],1);self.assertEqual(r['incomplete_or_error'],1)
        self.assertEqual(r['forward_decision_pairs'],{'reduced_continue_contact_hold':1})
        self.assertEqual(r['forward_margin_difference_m']['min'],-.003)


if __name__=='__main__':unittest.main()
