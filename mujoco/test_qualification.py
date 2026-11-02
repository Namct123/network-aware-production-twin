"""Plan rejection and benchmark accounting without MuJoCo timing assumptions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from config import load_config
from qualify import validate,benchmark,statistics

HERE=Path(__file__).parent

class QualificationTest(unittest.TestCase):
    def setUp(self):
        self.base=load_config(HERE/'configs/reconfigurable_cell_20261030.json')
        self.plan=json.loads((HERE/'experiments/qualification_20261102.json').read_text())

    def test_plan_prepares_all_jobs_without_mutating_profile(self):
        before=deepcopy(self.base); jobs=validate(self.base,self.plan)
        self.assertEqual(len(jobs),24); self.assertEqual(before,self.base)

    def test_bad_plan_rejected_before_experiments(self):
        for key,value in [('repeats',True),('warmup',-1),('functional_budget_s',float('nan'))]:
            plan=deepcopy(self.plan); plan['benchmark'][key]=value
            with self.assertRaises(ValueError):validate(self.base,plan)
        plan=deepcopy(self.plan); plan['benchmark']['cases'][0]['position_fraction']=2
        with self.assertRaises(ValueError):validate(self.base,plan)
        plan=deepcopy(self.plan); plan['study']['scenarios'][0]['patch']={'unknown.path':2}
        with self.assertRaises(ValueError):validate(self.base,plan)

    def test_warmup_separate_and_external_timing_saved(self):
        class Fake:
            def __init__(self,config):pass
            def rollout(self,estimate,source,now):
                return {'compute_ms':0,'status':'complete','action':'CONTINUE','completed_scenarios':54,
                        'expected_scenarios':54,'rollout_steps':10,'margins_m':{'CONTINUE':.1}}
        settings=deepcopy(self.plan['benchmark']); settings.update(repeats=2,warmup=1)
        settings['cases']=settings['cases'][:1]
        with tempfile.TemporaryDirectory() as tmp:
            result=benchmark(self.base,settings,Path(tmp),{'fake':Fake})
            self.assertEqual(len(result['rows']),6)
            self.assertTrue(all(g['samples']==2 for g in result['groups']))
            self.assertEqual(len(result['initialization']),2)
            self.assertTrue((Path(tmp)/'timing.csv').is_file())

    def test_deadline_uses_external_clock_and_keeps_incomplete_samples(self):
        rows=[{'backend':'m','budget_kind':'configured','phase':'warmup','external_ms':999,'budget_ms':20,'status':'complete','action':'HOLD'},
              {'backend':'m','budget_kind':'configured','phase':'measured','external_ms':21,'budget_ms':20,'status':'deadline_exceeded','action':'HOLD'},
              {'backend':'m','budget_kind':'configured','phase':'measured','external_ms':3,'budget_ms':20,'status':'complete','action':'CONTINUE'}]
        group=statistics(rows)[0]
        self.assertEqual(group['samples'],2); self.assertEqual(group['deadline_misses'],1)
        self.assertEqual(group['incomplete'],1); self.assertEqual(group['median_ms'],12)

if __name__=='__main__':unittest.main()
