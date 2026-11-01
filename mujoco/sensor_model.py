"""Ideal discrete sensors generated inside the plant boundary, not an estimator."""

import math
from signals import SignalFrame
from config import resolved_config


class SensorModel:
    def __init__(self, a1_limits=None, a2_limits=None, tolerance_m=None, config=None):
        c = resolved_config(config)
        a1_limits = c["geometry"]["joint_limits_m"]["a1_joint"] if a1_limits is None else a1_limits
        a2_limits = c["geometry"]["joint_limits_m"]["a2_joint"] if a2_limits is None else a2_limits
        tolerance_m = c["sensors"]["end_switch_tolerance_m"] if tolerance_m is None else tolerance_m
        self.limits = {"a1": tuple(map(float, a1_limits)), "a2": tuple(map(float, a2_limits))}
        if not math.isfinite(tolerance_m) or tolerance_m <= 0:
            raise ValueError("positive finite end-switch tolerance required")
        for low, high in self.limits.values():
            if not all(math.isfinite(v) for v in (low, high)) or high - low <= 2 * tolerance_m:
                raise ValueError("end-switch windows must be finite and non-overlapping")
        self.tolerance_m = tolerance_m
        self.sequence = 0
        self.previous = None
        self.previous_time = None

    def sample(self, plant):
        time_s = float(plant["time_s"])
        if not math.isfinite(time_s) or time_s < 0 or (
                self.previous_time is not None and time_s <= self.previous_time):
            raise ValueError("sample time must increase; create a new SensorModel after reset")
        values = {}
        for name in ("ps1", "ps2"):
            if type(plant[name]) is not bool:
                raise ValueError(f"{name} must be a digital sensor state")
            values[name] = plant[name]
        if 'transfer_present' in plant:
            if type(plant['transfer_present']) is not bool:
                raise ValueError('transfer_present must be a digital sensor state')
            values['transfer_present']=plant['transfer_present']
        for axis, (low, high) in self.limits.items():
            position = float(plant[axis + "_m"])
            if not math.isfinite(position):
                raise ValueError("nonfinite plant joint position")
            values[axis + "_retracted"] = abs(position - low) <= self.tolerance_m
            values[axis + "_extended"] = abs(position - high) <= self.tolerance_m
        # ponytail: unconfirmed hardware stays unavailable; add an adapter only
        # when encoder/home/vacuum measurements and their calibration are known.
        values.update(home_x=None, home_y1=None, home_y2=None,
                      vacuum_ok=None, belt_speed_front_m_s=None, belt_speed_long_m_s=None)
        frame = SignalFrame(self.sequence, time_s, time_s, values,
                            {name: "unavailable" if value is None else "good"
                             for name, value in values.items()})
        edges = [] if self.previous is None else [
            {"sequence": self.sequence, "source_time_s": time_s, "signal": name,
             "value": value, "edge": "rising" if value else "falling"}
            for name, value in values.items()
            if value is not None and value != self.previous[name]
        ]
        self.previous = values.copy()
        self.previous_time = time_s
        self.sequence += 1
        return frame, edges
