import unittest
from event_window import EventWindow

class EventWindowTests(unittest.TestCase):
 def test_labels_do_not_change_monitor_semantics(self):
  # Contract reuse only; these labels are not evidence from three physical machines.
  outcomes=[]
  for label in ["workpiece_arrived","cylinder_extended","robot_at_target"]:
   m=EventWindow([1.,1.2],.4,2)
   outcomes.append([m.observe(t,v) for t,v in [(.4,False),(1.,False),(1.1,True)]])
  self.assertEqual(outcomes[0],outcomes[1]);self.assertEqual(outcomes[1],outcomes[2]);self.assertFalse(any(x["alert"] for x in outcomes[0]))
 def test_causal_edge_and_two_source_samples_after_upper_endpoint(self):
  m=EventWindow([1.,1.2],.4,2);m.observe(.4,False)
  self.assertFalse(m.observe(1.2,False)["alert"]);self.assertFalse(m.observe(1.21,False)["alert"])
  self.assertTrue(m.observe(1.22,False)["alert"])
  early=EventWindow([1.,1.2],.4);early.observe(.4,False)
  self.assertEqual(early.observe(.5,True)["finding"],"target_earlier_than_eta_envelope")
  with self.assertRaises(ValueError):early.observe(.5,True)
  with self.assertRaises(ValueError):EventWindow([.1,.2],.4)
 def test_lost_evidence_requires_new_instance_and_cannot_establish_health(self):
  m=EventWindow([1.,1.2],.4);m.observe(.4,False)
  self.assertEqual(m.observe(None,None,False)["status"],"evidence_unavailable")
  self.assertEqual(m.observe(2.,False)["status"],"evidence_unavailable")
  fresh=EventWindow([1.,1.2],.4)
  self.assertEqual(fresh.observe(.5,True)["status"],"target_present_without_resolved_edge")

if __name__=="__main__":unittest.main()
