from pathlib import Path
from types import SimpleNamespace
import unittest
from command_history import CommandHistory
from config import load_config
from study_closed_loop_segment import select_speed,transit_expired

class ClosedLoopTests(unittest.TestCase):
 def test_adaptive_timeout_respects_commanded_slowdown(self):
  h=CommandHistory();h.record(0,.2);h.record(.5,.08)
  observer=SimpleNamespace(fit={"gain_point":1.},core=SimpleNamespace(anchor=(0.,0.),commands=h))
  self.assertTrue(transit_expired("sequential",observer,1.3,.2,.2))
  self.assertFalse(transit_expired("age_rule",observer,1.3,.2,.2))
  self.assertFalse(transit_expired("predictive",observer,1.3,.2,.2))
 def test_unusable_prediction_never_selects_motion(self):
  cfg=load_config(Path(__file__).parent/"configs/reconfigurable_cell_20261030.json")
  plan={"rule_cap_m_s":.12,"warning_age_s":.02}
  observer=SimpleNamespace(fit={"gain_point":1.})
  speed,reason,_=select_speed("predictive",.2,{"observation_age_s":.04,"usable_for_monitoring":False},observer,1,.035,plan,cfg)
  self.assertEqual(speed,0);self.assertEqual(reason,"unusable_pulse_evidence")
  self.assertEqual(select_speed("age_rule",.2,{"observation_age_s":.04},observer,1,.035,plan,cfg)[0],.12)

if __name__=="__main__":unittest.main()
