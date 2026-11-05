import unittest
from signals import SignalFrame
from study_pulse_network import replay

class NetworkPulseTests(unittest.TestCase):
 def test_network_rejection_and_receiver_causality(self):
  obs=[];cmd=[]
  for i in range(120):
   t=i*.02;v={"ps1":1<=i<20,"ps2":False}
   obs.append(SignalFrame(i,t,t,v,{k:"good" for k in v}).as_dict());cmd.append({"time_s":t,"command":{"long":.16}})
  settings={"gain_bounds":[.8,1.2],"drift_m_s":.005,"confirm_samples":2}
  normal,log=replay(obs,cmd,settings,.004,{"delay_ticks":0,"drop_source_s":None})
  self.assertFalse(normal["never_fit"]);self.assertIsNotNone(normal["first_timeout_s"])
  slow,log=replay(obs,cmd,settings,.004,{"delay_ticks":6,"drop_source_s":None})
  self.assertTrue(slow["never_fit"]);self.assertTrue(all(not r["observer"]["usable_for_monitoring"] for r in log))
  gap,log=replay(obs,cmd,settings,.004,{"delay_ticks":0,"drop_source_s":[1.,1.06]})
  self.assertGreater(gap["unusable_after_fit_ticks"],0)
  self.assertTrue(all(not r["observer"]["usable_for_monitoring"] for r in log if r["time_s"]>=1.))
  with self.assertRaises(ValueError):replay(obs,cmd,settings,.004,{"delay_ticks":-1,"drop_source_s":None})

if __name__=="__main__":unittest.main()
