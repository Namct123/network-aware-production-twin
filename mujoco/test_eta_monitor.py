import json
from pathlib import Path
import unittest
from config import load_config
from eta_monitor import EtaEventMonitor
from study_eta_monitor import replay
from signals import SignalFrame

HERE=Path(__file__).parent
class EtaMonitorTests(unittest.TestCase):
 def setUp(self):
  self.c=load_config(HERE/"configs/reconfigurable_cell_20261030.json")
  self.model=json.loads((HERE/"models/eta_residual_v1.json").read_text())
  self.settings=json.loads((HERE/"models/eta_monitor_v1.json").read_text())
  self.case={"delay_ticks":0,"gap_after_pulse_s":None,"target_unavailable_after_pulse_s":None}
 def recording(self,target=None,pulse_end=20):
  obs=[];cmd=[]
  for i in range(150):
   t=i*.02;v={"ps1":1<=i<pulse_end,"ps2":target is not None and i>=target}
   obs.append(SignalFrame(i,t,t,v,{k:"good" for k in v}).as_dict());cmd.append({"time_s":t,"command":{"long":.16}})
  return obs,cmd
 def run_case(self,target=None,method="ml",case=None,pulse_end=20):
  o,c=self.recording(target,pulse_end)
  return replay(o,c,self.c,self.model,self.settings,method,case or self.case,pulse_end*.02)
 def test_frozen_prediction_and_observed_early_edge(self):
  _,a=self.run_case();_,b=self.run_case(65)
  frozen=next(x["eta_interval_s"] for x in a if x["eta_interval_s"] is not None)
  self.assertEqual(frozen,next(x["eta_interval_s"] for x in b if x["eta_interval_s"] is not None))
  i=round(sum(frozen)/2/.02);healthy,_=self.run_case(i)
  self.assertIsNone(healthy["first_alert"])
  early,_=self.run_case(30);self.assertEqual(early["first_alert"]["finding"],"target_earlier_than_eta_envelope")
 def test_missing_edge_is_source_timed_and_receiver_delay_is_not_model_gain(self):
  a,logs=self.run_case();b,_=self.run_case(case={**self.case,"delay_ticks":2})
  self.assertEqual(a["first_alert"]["source_time_s"],b["first_alert"]["source_time_s"])
  self.assertAlmostEqual(b["first_alert"]["time_s"]-a["first_alert"]["time_s"],.04)
  upper=next(x["eta_interval_s"][1] for x in logs if x["eta_interval_s"])
  self.assertGreater(a["first_alert"]["source_time_s"],upper)
 def test_stale_gap_and_bad_quality_cannot_be_model_detections(self):
  for case in [{**self.case,"delay_ticks":6},{**self.case,"gap_after_pulse_s":[.1,.14]},{**self.case,"target_unavailable_after_pulse_s":.1}]:
   summary,records=self.run_case(case=case)
   self.assertIsNone(summary["first_alert"])
   self.assertTrue(all(x["basis"] is None for x in records if x["time_s"]>.56))
   self.assertTrue(any(x["data_issue"] in {"stale_packet","no_packet","signal_quality_unavailable"} for x in records))
 def test_outside_domain_and_changed_commands_use_engineering_fallback(self):
  result,log=self.run_case(pulse_end=11)
  self.assertTrue(result["outside_training_feature_box"]);self.assertGreater(result["fallback_ticks"],0)
  self.assertTrue(all(x["eta_interval_s"] is None for x in log))
  o,c=self.recording();m=EtaEventMonitor(self.c,self.model,self.settings)
  for i in range(50):
   now=c[i]["time_s"];record=m.observe(SignalFrame(**o[i]),now);m.issued(now,.1 if i>=30 else .16)
  self.assertEqual(record["basis"],"engineering_pulse_fallback");self.assertEqual(record["fallback_reason"],"command_changed")
 def test_changed_geometry_refuses_old_empirical_envelope(self):
  self.c["geometry"]["ps_y_m"]["ps2"]+=.01
  result,log=self.run_case()
  active=[x for x in log if x["basis"] is not None]
  self.assertTrue(active);self.assertTrue(all(x["fallback_reason"]=="profile_outside_calibration" for x in active))
  self.assertTrue(all(x["eta_interval_s"] is None for x in active))
 def test_all_methods_have_separately_calibrated_envelopes_and_no_authority(self):
  for method in ["pulse","constant","ml"]:
   _,logs=self.run_case(method=method)
   r=next(x for x in logs if x["eta_interval_s"])
   self.assertAlmostEqual(r["eta_interval_s"][1]-r["eta_interval_s"][0],2*self.settings["radii_s"][method])
   self.assertEqual(r["authority"],"advisory_only")
  with self.assertRaises(ValueError):EtaEventMonitor(self.c,self.model,{**self.settings,"radii_s":{"pulse":1,"constant":1,"ml":float("nan")}})

if __name__=="__main__":unittest.main()
