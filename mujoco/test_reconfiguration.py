"""Policy priority, latching and configuration checks without plant truth."""
from copy import deepcopy
from pathlib import Path
import unittest
from config import load_config,validate_config
from reconfiguration import Reconfiguration
from sequence import Sequence
from signals import SignalFrame

PROFILE=Path(__file__).parent/'configs/reconfigurable_cell_20261030.json'

def observation(seq,t,age=0):
    return SignalFrame(seq,t-age,t,{'ps1':False},{'ps1':'good'})

def health(*codes):
    return {'findings':[{'code':c} for c in codes]}

class ReconfigurationTest(unittest.TestCase):
    def setup_policy(self):
        c=load_config(PROFILE); ctl=Sequence(config=c,assume_open_loop=True)
        ctl._enter('TRACK',0)
        return ctl,Reconfiguration(c)

    def test_persistent_warning_caps_speed_and_stays_degraded_when_link_recovers(self):
        ctl,p=self.setup_policy()
        p.tick(ctl,observation(0,.10,.02),health(),.10)
        self.assertEqual(p.mode,'NORMAL')
        r=p.tick(ctl,observation(1,.12,.02),health(),.12)
        self.assertEqual(p.mode,'DEGRADED'); self.assertTrue(r['speed_cap_applied'])
        self.assertEqual(ctl.command['long'],.12)
        ctl.command['long']=.22  # An external speed schedule may request more.
        p.tick(ctl,observation(2,.14),health(),.14)
        self.assertEqual(ctl.command['long'],.12)
        self.assertEqual(p.mode,'DEGRADED')

    def test_one_warning_does_not_latch_and_no_speed_increase(self):
        ctl,p=self.setup_policy()
        p.tick(ctl,observation(0,.1,.02),health(),.1)
        p.tick(ctl,observation(1,.12),health(),.12)
        self.assertEqual(p.mode,'NORMAL')
        p.mode='DEGRADED'; ctl.command['long']=.10
        p.tick(ctl,observation(2,.14),health(),.14)
        self.assertEqual(ctl.command['long'],.10)

    def test_suspect_sensor_holds_without_clearing_vacuum_or_restarting(self):
        ctl,p=self.setup_policy(); ctl.command['vacuum']=True
        r=p.tick(ctl,observation(0,.1),health('expected_edge_missing'),.1)
        self.assertEqual(ctl.phase,'HOLD'); self.assertTrue(ctl.command['vacuum'])
        self.assertEqual(r['selected_long_speed_m_s'],0)
        reason=ctl.reason
        p.tick(ctl,observation(1,.12),health(),.12)
        self.assertEqual(ctl.reason,reason); self.assertEqual(ctl.phase,'HOLD')
        ctl.phase='TRACK'; ctl.command['long']=.16
        p.tick(ctl,observation(2,.14),health(),.14)
        self.assertEqual(ctl.reason,'reconfiguration_reset_required')

    def test_missing_health_holds_and_disabled_policy_changes_nothing(self):
        ctl,p=self.setup_policy()
        p.tick(ctl,observation(0,.1),None,.1)
        self.assertEqual(ctl.reason,'reconfiguration_health_unavailable')
        c=load_config(PROFILE); c['reconfiguration']['enabled']=False
        p=Reconfiguration(c); ctl=Sequence(config=c); ctl._enter('TRACK',0)
        self.assertIsNone(p.tick(ctl,None,health('telemetry_silence'),.1))
        self.assertEqual(ctl.phase,'TRACK')

    def test_front_feed_and_targets_are_unchanged_by_speed_degradation(self):
        ctl,p=self.setup_policy(); ctl._enter('FEED',0); before=deepcopy(ctl.command)
        p.tick(ctl,observation(0,.1,.02),health(),.1)
        p.tick(ctl,observation(1,.12,.02),health(),.12)
        self.assertEqual(ctl.command,before)
        self.assertEqual(p.mode,'DEGRADED')

    def test_settings_reject_typos_blind_mode_and_unsafe_thresholds(self):
        for section,key,value in [('reconfiguration','warning_age_s',.1),('reconfiguration','warning_ticks',True),
                                  ('reconfiguration','degraded_long_speed_m_s',.24),('health','enabled',False),
                                  ('estimator','command_history_enabled',False)]:
            c=load_config(PROFILE); c[section][key]=value
            with self.assertRaises(ValueError): validate_config(c)

if __name__=='__main__': unittest.main()
