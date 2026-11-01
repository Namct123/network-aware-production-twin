"""Small estimator/controller checks; no simulator or extra dependency needed."""

import unittest
from estimator import BeltEstimator
from sensor_model import SensorModel
from sequence import Sequence


def sample(sensor, t, ps1=False, ps2=False, a1=0.0, a2=0.0):
    return sensor.sample(dict(time_s=t, ps1=ps1, ps2=ps2, a1_m=a1, a2_m=a2))[0]


class TwinTest(unittest.TestCase):
    def test_two_edges_speed_center_and_stop(self):
        estimator, sensor = BeltEstimator(), SensorModel()
        for i in range(77):
            frame = sample(sensor, i*.02, ps1=i == 2, ps2=i == 76)
            e = estimator.update(frame, .16)
        self.assertEqual(e.anchors, 2)
        self.assertAlmostEqual(e.velocity_m_s, .235/1.48)
        self.assertAlmostEqual(e.y_m, .170-.011+e.velocity_m_s*.01)
        before, allowance = e.y_m, e.uncertainty_m
        e = estimator.update(sample(sensor, 1.54), 0)
        self.assertAlmostEqual(e.y_m, before+.002)
        self.assertGreater(e.uncertainty_m, allowance)
        e = estimator.update(sample(sensor, 1.56), 0)
        self.assertAlmostEqual(e.y_m, before+.002)  # Coast must be added only once.

    def test_no_ps1_no_synthetic_position(self):
        estimator, sensor = BeltEstimator(), SensorModel()
        estimator.update(sample(sensor, 0), .16)
        e = estimator.update(sample(sensor, .02, ps2=True), .16)
        self.assertIsNone(e.y_m)
        self.assertEqual(e.reason, "ps2_without_ps1")

    def test_simultaneous_edges_are_rejected_without_division_by_zero(self):
        estimator, sensor = BeltEstimator(), SensorModel()
        estimator.update(sample(sensor, 0), .16)
        e = estimator.update(sample(sensor, .02, ps1=True, ps2=True), .16)
        self.assertEqual(e.reason, "inconsistent_optical_edges")
        self.assertNotEqual(e.anchors, 2)

    def test_uncertainty_grows_and_speed_change_is_rejected(self):
        estimator, sensor = BeltEstimator(), SensorModel()
        estimator.update(sample(sensor, 0), .16)
        e = estimator.update(sample(sensor, .02, ps1=True), .16)
        original = e.uncertainty_m
        for i in range(2, 77):
            e = estimator.update(sample(sensor, i*.02, ps2=i == 76), .20)
        self.assertEqual(e.anchors, 1)
        self.assertGreater(e.uncertainty_m, original)
        self.assertEqual(e.reason, "speed_changed_between_anchors")

    def test_stale_true_is_not_a_new_anchor(self):
        estimator, sensor = BeltEstimator(), SensorModel()
        estimator.update(sample(sensor, 0), .16)
        stale = sample(sensor, .02, ps1=True).aged(.5, .1)
        estimator.update(stale, .16)
        e = estimator.update(sample(sensor, .04, ps1=True), .16)
        self.assertEqual(e.anchors, 0)

    def test_push_timeout_latches_hold(self):
        controller, sensor = Sequence(assume_open_loop=True), SensorModel()
        for i in range(230):
            t = i*.02
            frame = sample(sensor, t, a1=0 if controller.phase != "PUSH" else .05)
            controller.tick(frame, t)
            if controller.phase == "HOLD":
                break
        self.assertEqual(controller.phase, "HOLD")
        self.assertEqual(controller.reason, "timeout:PUSH:a1_extended")
        self.assertTrue(controller.command["hold"])
        controller.tick(sample(sensor, t+.02, a1=.110), t+.02)
        self.assertEqual(controller.phase, "HOLD")

    def test_stale_and_out_of_order_hold(self):
        sensor = SensorModel()
        first = sample(sensor, 0)
        controller = Sequence()
        controller.tick(first, .2)
        self.assertEqual(controller.reason, "invalid_or_stale:ps1")
        controller = Sequence()
        controller.tick(first, 0)
        controller.tick(first, .02)
        self.assertEqual(controller.reason, "nonmonotonic_sample")

    def test_missing_ps2_deadline_scales_with_speed(self):
        controller, sensor = Sequence(belt_speed=.24, assume_open_loop=True), SensorModel()
        controller.tick(sample(sensor, 0), 0)
        controller._enter("TRACK", 0)
        for i in range(1, 101):
            controller.tick(sample(sensor, i*.02), i*.02)
            if controller.phase == "HOLD":
                break
        self.assertEqual(controller.reason, "timeout:TRACK:ps2")
        self.assertLessEqual(i*.02, .44/.24+.02)

    def test_strict_motion_gate_and_hold_preserves_vacuum(self):
        controller, sensor = Sequence(), SensorModel()
        controller.tick(sample(sensor, 0), 0)
        controller._enter("TRACK", .0)
        for i in range(1, 80):
            frame = sample(sensor, i*.02, ps1=i == 2, ps2=i == 76)
            controller.tick(frame, i*.02)
            if controller.phase == "HOLD":
                break
        self.assertEqual(controller.reason, "unconfirmed_xy_a2_midstroke_and_vacuum")
        loaded = Sequence(assume_open_loop=True)
        loaded.command["vacuum"] = True
        loaded.hold("test", 0)
        self.assertTrue(loaded.command["vacuum"])
        self.assertEqual(loaded.command["long"], 0)


if __name__ == "__main__":
    unittest.main()
