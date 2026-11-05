from copy import deepcopy
import unittest
from config import load_config
from pathlib import Path
from signals import SignalFrame
from innovation import EventResidual

class InnovationTests(unittest.TestCase):
    def setUp(self):
        self.config=load_config(Path(__file__).parent/"configs/reconfigurable_cell_20261030.json")
        self.config["geometry"]["ps_y_m"]={"ps1":0,"ps2":.2}
        self.config["timing"]["max_sample_gap_s"]=3
        self.settings={"gain_bounds":[.95,1.05],"drift_m_s":.001,"confirm_samples":2}
    def frame(self,t,seq,up,down):
        v={"ps1":up,"ps2":down}
        return SignalFrame(seq,t,t,v,{k:"unavailable" if x is None else "good" for k,x in v.items()})
    def anchor(self,settings=None):
        m=EventResidual(self.config,settings or self.settings)
        m.observe(self.frame(0,0,True,False),0);m.issued(0,.1)
        m.observe(self.frame(.02,1,False,False),.02);m.issued(.02,.1)
        return m
    def test_missing_edge_persistence_and_early_edge(self):
        m=self.anchor()
        self.assertFalse(m.observe(self.frame(1.8,2,False,False),1.8)["alert"]);m.issued(1.8,.1)
        self.assertTrue(m.observe(self.frame(1.82,3,False,False),1.82)["alert"])
        m=self.anchor();r=m.observe(self.frame(.04,2,False,True),.04)
        self.assertEqual(r["finding"],"target_earlier_than_interval");self.assertTrue(r["alert"])
    def test_wider_bounds_do_not_shrink_and_no_truth_input(self):
        narrow=self.anchor();s=deepcopy(self.settings);s["gain_bounds"]=[.8,1.2];s["drift_m_s"]=.02;wide=self.anchor(s)
        a=narrow.observe(self.frame(1,2,False,False),1)["predicted_center_m"]
        b=wide.observe(self.frame(1,2,False,False),1)["predicted_center_m"]
        self.assertLessEqual(b[0],a[0]);self.assertGreaterEqual(b[1],a[1])
        with self.assertRaises(ValueError):narrow.issued(2,.1)
    def test_missing_stale_and_unanchored_are_not_normal_or_fault(self):
        m=EventResidual(self.config,self.settings)
        self.assertEqual(m.observe(self.frame(0,0,False,False),0)["status"],"no_anchor")
        m=self.anchor();r=m.observe(self.frame(.04,2,False,None),.04)
        self.assertEqual(r["status"],"target_unavailable");self.assertFalse(r["alert"])
        r=m.observe(self.frame(.06,3,False,False),.3)
        self.assertEqual(r["status"],"invalid_or_stale_frame");self.assertFalse(r["alert"])
    def test_settings_and_received_clock_boundary(self):
        for gains in ([1,.5],[0,1],[True,1],[float("nan"),1]):
            s={**self.settings,"gain_bounds":gains}
            with self.assertRaises(ValueError):EventResidual(self.config,s)
        m=self.anchor()
        f=SignalFrame(2,.04,.06,{"ps1":False,"ps2":False},{"ps1":"good","ps2":"good"})
        self.assertEqual(m.observe(f,.05)["status"],"invalid_or_stale_frame")

if __name__=="__main__":unittest.main()
