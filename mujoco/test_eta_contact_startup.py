import unittest
from study_contact_startup import pulse_summary,protocol_digest
from unittest.mock import Mock

class ContactAuditTests(unittest.TestCase):
 def records(self,initial=False):
  obs=[{'source_time_s':t,'values':{'ps1':u,'ps2':d}} for t,u,d in [(0.,initial,False),(.1,True,False),(.5,False,False),(.9,False,True)]]
  truth=[{'time_s':o['source_time_s'],'product_xyz_m':[0.,o['source_time_s']*.15,0.]} for o in obs]
  return obs,truth
 def test_initial_high_is_not_a_pulse_and_no_future_target_is_invented(self):
  o,t=self.records(True);self.assertEqual(pulse_summary(o,t,.06,.06,.02,0.,.01)['status'],'initial_pulse_unresolved')
  o,t=self.records();o[-1]['values']['ps2']=False
  self.assertEqual(pulse_summary(o,t,.06,.06,.02,0.,.01)['status'],'target_not_observed')
 def test_constant_speed_oracle_and_alignment(self):
  a,b=Mock(),Mock()
  a.read_bytes.return_value=b'{"x":1}\r\n';b.read_bytes.return_value=b'{"x":1}\n'
  self.assertEqual(protocol_digest(a),protocol_digest(b))
  o,t=self.records();r=pulse_summary(o,t,.06,.06,.02,0.,.01)
  self.assertEqual(r['status'],'resolved');self.assertAlmostEqual(r['pulse_residual_s'],0.);self.assertAlmostEqual(r['relative_speed_increase'],0.)
  t[0]['time_s']=.001
  with self.assertRaises(ValueError):pulse_summary(o,t,.06,.06,.02,0.,.01)

if __name__=='__main__':unittest.main()
