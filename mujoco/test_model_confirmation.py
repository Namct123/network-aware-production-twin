from types import SimpleNamespace
from pathlib import Path
import unittest
from config import load_config
from command_history import CommandHistory
from model_confirmation import qualify

class ConfirmationTests(unittest.TestCase):
 def test_interval_and_verified_evidence_are_both_required(self):
  c=load_config(Path(__file__).parent/"configs/reconfigurable_cell_20261030.json");h=CommandHistory()
  o=SimpleNamespace(fit={"gain_bounds":[.8,1.2]},core=SimpleNamespace(commands=h))
  record={"usable_for_monitoring":True,"predicted_center_m":[.02,.03],"prediction_time_s":1.}
  result=qualify(record,o,1.,.5,.3,[.01,.035],c)
  self.assertTrue(result["conditional_position_ok"]);self.assertFalse(result["release_eligible"])
  self.assertTrue(qualify(record,o,1.,.5,.3,[.01,.035],c,True)["release_eligible"])
  self.assertFalse(qualify(record,o,1.,.5,.3,[.025,.035],c,True)["conditional_position_ok"])
  h.record(0,.1);h.record(.5,0.)
  self.assertTrue(qualify(record,o,1.,.5,.3,[.01,.035],c)["conditional_position_ok"])
  h.record(.7,.1)
  self.assertEqual(qualify(record,o,1.,.5,.3,[.01,.035],c)["reason"],"stop_not_maintained")

if __name__=="__main__":unittest.main()
