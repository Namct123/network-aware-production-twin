import json
from pathlib import Path
import unittest
from config import load_config
from signals import SignalFrame
from study_network_clock import replay
HERE=Path(__file__).parent
class NetworkClockTests(unittest.TestCase):
 def setUp(self):
  self.c=load_config(HERE/'configs/reconfigurable_cell_20261030.json');self.m=json.loads((HERE/'models/eta_residual_v1.json').read_text());self.s=json.loads((HERE/'models/eta_monitor_v1.json').read_text())
  self.obs=[];self.cmd=[]
  for i in range(150):
   t=i*.02;v={'ps1':1<=i<20,'ps2':i>=77};self.obs.append(SignalFrame(i,t,t,v,{k:'good' for k in v}).as_dict());self.cmd.append({'time_s':t,'command':{'long':.16}})
 def check(self,clock,age,delay=4,gap=None):return replay(self.obs,self.cmd,self.c,self.m,self.s,{'clock':clock,'age_gate':age},{'delay_ticks':delay,'gap_after_pulse_s':gap},.4)
 def test_same_prediction_and_different_clock_semantics(self):
  source,_=self.check('source',True);receiver,_=self.check('receiver',True)
  self.assertEqual(source['eta_interval_s'],receiver['eta_interval_s']);self.assertIsNone(source['first_alert']);self.assertIsNotNone(receiver['first_alert'])
 def test_age_gate_is_separate_from_clock_and_tail_is_drained(self):
  rejected,_=self.check('source',True,6);allowed,trace=self.check('source',False,6)
  self.assertTrue(rejected['never_fit']);self.assertFalse(allowed['never_fit']);self.assertEqual(trace[-1]['source_time_s'],self.obs[-1]['source_time_s'])
  self.assertAlmostEqual(trace[-1]['time_s']-trace[-1]['source_time_s'],.12)
 def test_gap_remains_rejected_when_age_gate_disabled(self):
  result,trace=self.check('source',False,0,[.1,.14]);self.assertIsNone(result['first_alert']);self.assertGreater(result['unusable_after_fit_ticks'],0)
  self.assertTrue(all(v['basis'] is None for v in trace if v['time_s']>.56))

if __name__=='__main__':unittest.main()
