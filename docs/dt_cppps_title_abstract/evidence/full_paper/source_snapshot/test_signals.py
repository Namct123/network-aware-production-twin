"""Run: python mujoco/test_signals.py (no MuJoCo dependency)."""

import json
from pathlib import Path
import tempfile
import unittest

from signals import SignalFrame
from sensor_model import SensorModel
from record_signals import replay


def plant(t=0.0, a1=0.0, a2=0.0, ps1=False, ps2=False):
    return dict(time_s=t, a1_m=a1, a2_m=a2, ps1=ps1, ps2=ps2,
                product_xyz_m=[99, 99, 99], vacuum_command=True, x_m=99, y_m=99)


class SignalsTest(unittest.TestCase):
    def test_no_truth_or_commands_leak(self):
        frame, edges = SensorModel().sample(plant())
        self.assertEqual(edges, [])
        self.assertTrue(frame.values["a1_retracted"])
        self.assertFalse(frame.values["ps1"])
        self.assertEqual(frame.quality["ps1"], "good")
        self.assertIsNone(frame.values["vacuum_ok"])
        self.assertEqual(frame.quality["vacuum_ok"], "unavailable")
        for name in ("product_xyz_m", "x_m", "y_m", "vacuum_command"):
            self.assertNotIn(name, frame.values)

    def test_end_switches_follow_physical_stroke(self):
        sensor = SensorModel()
        sensor.sample(plant())
        partial, edges = sensor.sample(plant(.02, a1=.110, a2=.060, ps1=True))
        self.assertTrue(partial.values["a1_extended"])
        self.assertFalse(partial.values["a2_extended"])
        self.assertIn(("ps1", "rising"), [(e["signal"], e["edge"]) for e in edges])
        full, _ = sensor.sample(plant(.04, a2=.075))
        self.assertTrue(full.values["a2_extended"])
        self.assertFalse(full.values["a2_retracted"])

    def test_stale_is_not_false_and_does_not_change_original(self):
        frame, _ = SensorModel().sample(plant())
        stale = frame.aged(.2, .1)
        self.assertFalse(stale.values["ps1"])
        self.assertEqual(stale.quality["ps1"], "stale")
        self.assertEqual(stale.quality["vacuum_ok"], "unavailable")
        self.assertEqual(frame.quality["ps1"], "good")
        self.assertEqual(frame.aged(.1, .1).quality["ps1"], "good")
        delayed = SignalFrame(0, 0, .5, {"ps1": False}, {"ps1": "good"})
        self.assertEqual(delayed.aged(.5, .1).quality["ps1"], "stale")

    def test_reset_and_invalid_times_are_rejected(self):
        sensor = SensorModel()
        sensor.sample(plant())
        for bad in (0, -.1, float("nan")):
            with self.assertRaises(ValueError):
                sensor.sample(plant(bad))
        with self.assertRaises(ValueError):
            SensorModel(tolerance_m=.1)
        with self.assertRaises(ValueError):
            SignalFrame(0, 1, 0, {"ps1": False}, {"ps1": "good"})
        with self.assertRaises(ValueError):
            SignalFrame(0, 0, 0, {"ps1": None}, {"ps1": "good"})

    def test_replay_roundtrip_gaps_and_reordering(self):
        sensor = SensorModel()
        frames = [sensor.sample(plant(t, ps1=t > 0))[0] for t in (0, .02, .04)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signals.jsonl"
            path.write_text("\n".join(json.dumps(f.as_dict()) for f in frames), encoding="utf-8")
            self.assertEqual(replay(path)["samples"], 3)
            self.assertEqual(replay(path)["observed_transitions"], 1)
            path.write_text("\n".join(json.dumps(f.as_dict()) for f in frames[::2]), encoding="utf-8")
            self.assertEqual(replay(path)["sequence_gaps"], 1)
            path.write_text("\n".join(json.dumps(f.as_dict()) for f in reversed(frames)), encoding="utf-8")
            with self.assertRaises(ValueError):
                replay(path)


if __name__ == "__main__":
    unittest.main()
