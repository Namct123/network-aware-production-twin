"""Adaptive algebra, conservative latching, and fixed-policy compatibility."""
from pathlib import Path
import json
import unittest
from config import load_config,validate_config
from command_history import CommandHistory
from estimator import Estimate
from reconfiguration import Reconfiguration
from sequence import Sequence
from signals import SignalFrame
from speed_policy import speed_limit
from check_robustness import prepare,HERE

PROFILE=Path(__file__).parent/'configs/adaptive_cell_20261031.json'

class AdaptiveTest(unittest.TestCase):
    def test_cap_decreases_with_observation_age_and_gap(self):
        c=load_config(PROFILE)
        a=speed_limit(c,Estimate(),0,.02,None)
        b=speed_limit(c,Estimate(),.02,.02,None)
        d=speed_limit(c,Estimate(),.04,.02,None)
        self.assertEqual(a['cap_m_s'],.24)
        self.assertAlmostEqual(b['cap_m_s'],.14)
        self.assertLess(d['cap_m_s'],c['motion']['test_speed_range_m_s'][0])
        self.assertLessEqual(speed_limit(c,Estimate(),.02,.04,None)['cap_m_s'],b['cap_m_s'])
        self.assertLessEqual(b['cap_m_s']*b['pickup_denominator_s'],b['pickup_budget_m'])

    def test_current_uncertainty_and_already_issued_travel_reduce_stop_budget(self):
        c=load_config(PROFILE); h=CommandHistory(); h.record(0,.16)
        e=Estimate(.20,.16,.005,1,'tracking')
        a=speed_limit(c,e,0,.02,h.interval(0,0))
        e.uncertainty_m=.03
        b=speed_limit(c,e,0,.02,h.interval(0,0))
        d=speed_limit(c,e,.04,.02,h.interval(0,.04))
        self.assertLess(b['cap_m_s'],a['cap_m_s'])
        self.assertLessEqual(d['cap_m_s'],b['cap_m_s'])
        self.assertLess(d['remaining_stop_margin_m'],b['remaining_stop_margin_m'])

    def test_latched_cap_cannot_speed_up_after_link_recovers(self):
        c=load_config(PROFILE); ctl=Sequence(config=c); ctl._enter('TRACK',0); p=Reconfiguration(c)
        f=lambda seq,t,age: SignalFrame(seq,t-age,t,{'ps1':False},{'ps1':'good'})
        r=p.tick(ctl,f(0,.1,.02),{'findings':[]},.1)
        self.assertEqual(ctl.phase,'TRACK'); self.assertAlmostEqual(ctl.command['long'],.14)
        ctl.command['long']=.22
        p.tick(ctl,f(1,.12,0),{'findings':[]},.12)
        # Fresh reception can still reveal a longer source-sample gap.
        self.assertLessEqual(ctl.command['long'],.14)
        self.assertEqual(p.mode,'DEGRADED')

    def test_no_feasible_tested_speed_holds_without_losing_vacuum(self):
        c=load_config(PROFILE); ctl=Sequence(config=c); ctl._enter('TRACK',0); ctl.command['vacuum']=True
        p=Reconfiguration(c)
        f=SignalFrame(0,.06,.1,{'ps1':False},{'ps1':'good'})
        p.tick(ctl,f,{'findings':[]},.1)
        self.assertEqual(ctl.reason,'adaptive_no_admissible_speed')
        self.assertTrue(ctl.command['vacuum'])

    def test_missing_history_does_not_silently_use_true_velocity(self):
        c=load_config(PROFILE); ctl=Sequence(config=c); ctl._enter('TRACK',0)
        ctl.estimator.estimate=Estimate(.1,.16,.003,1,'tracking')
        p=Reconfiguration(c)
        p.tick(ctl,SignalFrame(0,.1,.1,{'ps1':False},{'ps1':'good'}),{'findings':[]},.1)
        self.assertEqual(ctl.reason,'adaptive_invalid_inputs')

    def test_bad_settings_and_three_policy_plan(self):
        for k,v in [('age_guard_s',-1),('pick_reserve_m',.02),('speed_step_m_s',0),('enabled',1)]:
            c=load_config(PROFILE); c['reconfiguration']['adaptive'][k]=v
            with self.assertRaises(ValueError): validate_config(c)
        c=load_config(PROFILE)
        plan=json.loads((HERE/'experiments/adaptive_speed_smoke.json').read_text())
        jobs=prepare(c,plan)
        self.assertEqual(len(jobs),9)
        self.assertFalse(jobs[1]['config']['reconfiguration']['adaptive']['enabled'])
        self.assertTrue(jobs[2]['config']['reconfiguration']['adaptive']['enabled'])
        self.assertEqual(jobs[0]['config']['plant'],jobs[2]['config']['plant'])

if __name__=='__main__': unittest.main()
