"""One-product belt estimate from ordered optical rising edges, not plant pose."""

from dataclasses import asdict, dataclass
import math
from config import resolved_config


@dataclass
class Estimate:
    y_m: float | None = None
    velocity_m_s: float | None = None
    uncertainty_m: float | None = None
    anchors: int = 0
    reason: str = "not_observed"

    def as_dict(self):
        return asdict(self)


class BeltEstimator:
    def __init__(self, ps1_y=None, ps2_y=None, half_length=None,
                 nominal_speed=None, stop_coast=None, config=None):
        c = resolved_config(config)
        self.parameters = c["estimator"]
        ps1_y = c["geometry"]["ps_y_m"]["ps1"] if ps1_y is None else ps1_y
        ps2_y = c["geometry"]["ps_y_m"]["ps2"] if ps2_y is None else ps2_y
        half_length = c["geometry"]["product_size_m"][1]/2 if half_length is None else half_length
        nominal_speed = c["motion"]["long_speed_m_s"] if nominal_speed is None else nominal_speed
        stop_coast = self.parameters["stop_coast_m"] if stop_coast is None else stop_coast
        if not all(math.isfinite(v) for v in
                   (ps1_y, ps2_y, half_length, nominal_speed, stop_coast)):
            raise ValueError("finite geometry and speeds required")
        if ps2_y <= ps1_y or half_length <= 0 or nominal_speed <= 0 or stop_coast < 0:
            raise ValueError("invalid forward-belt configuration")
        self.positions = {"ps1": ps1_y, "ps2": ps2_y}
        self.half_length = half_length
        self.nominal_speed = nominal_speed
        self.stop_coast = stop_coast
        self.estimate = Estimate()
        self.previous = {"ps1": None, "ps2": None}
        self.time = None
        self.first_time = None
        self.command = None
        self.constant_speed = True

    def update(self, frame, belt_command):
        t = frame.source_time_s
        if not math.isfinite(belt_command) or belt_command < 0:
            raise ValueError("forward finite commanded belt speed required")
        if self.time is not None and t <= self.time:
            raise ValueError("estimator needs increasing source timestamps")
        dt = 0 if self.time is None else t - self.time
        est = self.estimate
        if est.y_m is not None:
            if belt_command > 0:
                velocity = est.velocity_m_s if est.anchors == 2 else belt_command
                est.y_m += velocity * dt
                # ponytail: engineering error allowance, not a statistical guarantee;
                # replace with calibrated uncertainty propagation after plant measurements.
                est.uncertainty_m += self.parameters["drift_m_s"] * dt
            elif self.command is not None and self.command > 0:
                est.y_m += self.stop_coast
                est.uncertainty_m += self.stop_coast
        if self.first_time is not None and self.command is not None:
            self.constant_speed &= abs(belt_command - self.command) < 1e-9
        for name in ("ps1", "ps2"):
            valid = frame.quality.get(name) == "good"
            value = frame.values.get(name) if valid else None
            rising = value is True and self.previous[name] is False
            self.previous[name] = value
            if not rising:
                continue
            if name == "ps1":
                if est.anchors:
                    est.reason = "unexpected_ps1_retrigger"
                    continue
                self.first_time = t
                self.constant_speed = True
                est.anchors = 1
                est.velocity_m_s = belt_command or self.nominal_speed
            else:
                if est.anchors != 1 or self.first_time is None:
                    est.reason = "ps2_without_ps1"
                    continue
                if not self.constant_speed or belt_command <= 0:
                    est.reason = "speed_changed_between_anchors"
                    continue
                interval = t - self.first_time
                if interval <= 0:
                    est.reason = "inconsistent_optical_edges"
                    continue
                speed = (self.positions["ps2"] - self.positions["ps1"]) / interval
                if not self.parameters["transit_speed_range_m_s"][0] <= speed <= self.parameters["transit_speed_range_m_s"][1]:
                    est.reason = "implausible_transit_speed"
                    continue
                est.velocity_m_s = speed
                est.anchors = 2
            # A rising edge detects the leading face, not the product center.
            # Half a sample of motion compensates the unknown crossing phase.
            est.y_m = self.positions[name] - self.half_length + est.velocity_m_s * dt / 2
            est.uncertainty_m = self.parameters["anchor_tolerance_m"] + est.velocity_m_s * dt / 2
            est.reason = "tracking"
        self.command = belt_command
        self.time = t
        return est
