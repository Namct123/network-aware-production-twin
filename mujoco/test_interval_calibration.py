import json
from pathlib import Path
import unittest
from calibrate_residual import conditions,fit_bounds,validate_plan

class CalibrationTests(unittest.TestCase):
    def setUp(self):self.plan=json.loads((Path(__file__).parent/"experiments/interval_calibration_20261105.json").read_text())
    def test_disjoint_normal_conditions_and_fixed_matrix(self):
        groups=conditions(self.plan)
        self.assertEqual([len(g[1]) for g in groups],[9,8,16,4])
        self.assertEqual(validate_plan(self.plan),self.plan)
        for bad in [{**self.plan,"command_distance_m":float("nan")},{**self.plan,"confirm_samples":True},{**self.plan,"test_gains":[1,1]}]:
            with self.assertRaises(ValueError):validate_plan(bad)
        self.assertTrue(all(c["fault"]=="none" for c in groups[0][1]))
        overlap={**self.plan,"test_speeds_m_s":[.12],"test_gains":[.88],"test_frictions":[1.]}
        with self.assertRaises(ValueError):conditions(overlap)
    def test_fit_only_observed_transition_and_integral(self):
        event={"sensor_distance_m":.2,"command_distance_m":.2,"period_s":.02,"command_speed_m_s":.16}
        result=fit_bounds([event],self.plan)
        self.assertLess(result["gain_bounds"][0],1);self.assertGreater(result["gain_bounds"][1],1)
        self.assertEqual(result,fit_bounds([{**event,"hidden_gain":99,"pose":999}],self.plan))
        for events in [[],[None],[{**event,"command_distance_m":0}]]:
            with self.assertRaises(ValueError):fit_bounds(events,self.plan)

if __name__=="__main__":unittest.main()
