import itertools
import unittest
from audit_pulse_model import sampling_window

class SamplingModelTests(unittest.TestCase):
 def test_quantized_edge_bound_at_all_error_extremes(self):
  rise,fall,L,d,T=.4,.8,.06,.2,.02;w=sampling_window(rise,fall,L,d,T)
  self.assertAlmostEqual(w['radius_s'],.08666666666666667)
  for er,ef,et in itertools.product([0.,T],repeat=3):
   observed_target=fall-ef+d*(fall-ef-rise+er)/L+et
   self.assertLessEqual(w['interval_s'][0]-1e-12,observed_target);self.assertLessEqual(observed_target,w['interval_s'][1]+1e-12)
 def test_unresolved_or_nonfinite_pulse_is_rejected(self):
  for values in [(0.,.02,.06,.2,.02),(0.,1.,0.,.2,.02),(0.,1.,.06,.2,float('nan'))]:
   with self.assertRaises(ValueError):sampling_window(*values)

if __name__=='__main__':unittest.main()
