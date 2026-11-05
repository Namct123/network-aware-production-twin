import unittest
from pathlib import Path
from config import load_config
from pulse_observer import pulse_bounds,PulseObserver
from signals import SignalFrame

class PulseTests(unittest.TestCase):
 def test_bounds_and_unresolved_pulse(self):
  lo,hi=pulse_bounds(.06,.004,.0608,.16,.02);self.assertLess(lo,1);self.assertGreater(hi,1)
  for distance in (0,.001,float("nan")):
   with self.assertRaises(ValueError):pulse_bounds(.06,.004,distance,.16,.02)
 def test_only_complete_contiguous_upstream_pulse_can_fit(self):
  config=load_config(Path(__file__).parent/"configs/reconfigurable_cell_20261030.json")
  settings={"gain_bounds":[.8,1.2],"drift_m_s":.005,"confirm_samples":2}
  m=PulseObserver(config,settings,.004)
  for i in range(22):
   t=i*.02;up=1<=i<20;f=SignalFrame(i,t,t,{"ps1":up,"ps2":False},{"ps1":"good","ps2":"good"})
   record=m.observe(f,t);m.issued(t,.16)
   if i<20:self.assertIsNone(record["predicted_center_m"])
  self.assertIsNotNone(m.fit);self.assertEqual(m.fit["at_s"],.4)
  m=PulseObserver(config,settings,.004)
  for seq,t,up in [(0,0,False),(1,.02,True),(5,.1,False)]:
   f=SignalFrame(seq,t,t,{"ps1":up,"ps2":False},{"ps1":"good","ps2":"good"});m.observe(f,t);m.issued(t,.16)
  self.assertIsNone(m.fit)

if __name__=="__main__":unittest.main()
