import unittest
import numpy as np
from eta_ml import fit,predict,optical_example,predict_from_pulse
from config import load_config
from pathlib import Path
from signals import SignalFrame

class EtaMLTests(unittest.TestCase):
 def test_fit_predict_and_no_label_access_at_inference(self):
  rows=[{"features":[i,i*.1,i*i*.01],"residual_s":.02*i+.1} for i in range(12)]
  m=fit(rows,.01)
  e={"features":[4.,.4,.16],"available_at_s":1.,"pulse_eta_s":2.}
  a=predict(m,e);b=predict(m,{**e,"target_at_s":999,"hidden_gain":999})
  self.assertEqual(a,b);self.assertAlmostEqual(a["eta_s"],2.18,places=2)
  self.assertTrue(a["inside_training_feature_box"])
  with self.assertRaises(ValueError):predict(m,{**e,"features":[float("nan"),0,0]})
  with self.assertRaises(ValueError):fit(rows,0)
 def test_target_label_changes_cannot_change_frozen_features(self):
  c=load_config(Path(__file__).parent/"configs/reconfigurable_cell_20261030.json")
  def example(target):
   obs=[];commands=[]
   for i in range(100):
    t=i*.02;v={"ps1":1<=i<20,"ps2":i>=target}
    obs.append(SignalFrame(i,t,t,v,{k:"good" for k in v}).as_dict());commands.append({"time_s":t,"command":{"long":.16}})
   return optical_example(obs,commands,c)
  a,b=example(80),example(90)
  self.assertEqual(a["features"],b["features"]);self.assertEqual(a["pulse_eta_s"],b["pulse_eta_s"])
  self.assertNotEqual(a["residual_s"],b["residual_s"])
 def test_live_prediction_needs_no_downstream_label(self):
  rows=[{"features":[i+.1,.16,.16*(i+.1)],"residual_s":.01*i} for i in range(6)]
  m=fit(rows,1.)
  result=predict_from_pulse(m,{"at_s":.4,"pulse_start_s":.02,"gain_point":1.},.16,.2)
  self.assertEqual(result["authority"],"advisory_only");self.assertGreaterEqual(result["eta_s"],.4)
 def test_scaling_uses_only_training_rows(self):
  rows=[{"features":[i,1.,2.],"residual_s":i*.01} for i in range(4)]
  m=fit(rows,1.);self.assertEqual(m["mean"],[1.5,1.,2.]);self.assertEqual(m["scale"][1:], [1.,1.])
  self.assertFalse(predict(m,{"features":[100.,1,2],"available_at_s":0.,"pulse_eta_s":1.})["inside_training_feature_box"])

if __name__=="__main__":unittest.main()
