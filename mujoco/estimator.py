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
    command_gain: float | None = None

    def as_dict(self):
        # Keep invalid numeric values out of JSON; supervisor logs their cause
        # and latches HOLD rather than silently serializing NaN as a measurement.
        return {key:None if isinstance(value,float) and not math.isfinite(value) else value
                for key,value in asdict(self).items()}


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
        self.history_mode=self.parameters.get('command_history_enabled',False)
        self.command_gain=1.0
        self.anchor_command_distance=0.0
        self.anchor_coast=0.0

    def update(self, frame, belt_command, command_interval=None):
        t = frame.source_time_s
        if not math.isfinite(belt_command) or belt_command < 0:
            raise ValueError("forward finite commanded belt speed required")
        if self.time is not None and t <= self.time:
            raise ValueError("estimator needs increasing source timestamps")
        dt = 0 if self.time is None else t - self.time
        est = self.estimate
        if self.history_mode and dt>0:
            if command_interval is None:
                est.reason='command_history_unavailable'
                return est
            required={'start_s','end_s','distance_m','speed_variation_m_s','stops','end_speed_m_s','max_speed_m_s'}
            if set(command_interval)!=required or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in command_interval.values()):
                raise ValueError('invalid command integral')
            if abs(command_interval['start_s']-self.time)>1e-9 or abs(command_interval['end_s']-t)>1e-9:
                raise ValueError('command integral does not cover the source-time interval')
            belt_command=command_interval['end_speed_m_s']
        elif self.history_mode:
            command_interval={'distance_m':0.0,'speed_variation_m_s':0.0,'stops':0}
        if est.y_m is not None:
            if self.history_mode:
                est.y_m+=self.command_gain*command_interval['distance_m']+command_interval['stops']*self.stop_coast
                est.uncertainty_m+=(self.parameters['drift_m_s']*dt
                    +self.parameters['command_response_uncertainty_s']*command_interval['speed_variation_m_s']
                    +command_interval['stops']*self.stop_coast)
                est.velocity_m_s=self.command_gain*belt_command
                est.command_gain=self.command_gain
            elif belt_command > 0:
                velocity = est.velocity_m_s if est.anchors == 2 else belt_command
                est.y_m += velocity * dt
                # ponytail: engineering error allowance, not a statistical guarantee;
                # replace with calibrated uncertainty propagation after plant measurements.
                est.uncertainty_m += self.parameters["drift_m_s"] * dt
            elif self.command is not None and self.command > 0:
                est.y_m += self.stop_coast
                est.uncertainty_m += self.stop_coast
        if self.first_time is not None and self.command is not None:
            if self.history_mode:
                self.anchor_command_distance+=command_interval['distance_m']
                self.anchor_coast+=command_interval['stops']*self.stop_coast
            else:
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
                self.anchor_command_distance=self.anchor_coast=0.0
                est.anchors = 1
                est.velocity_m_s = belt_command or self.nominal_speed
            else:
                if est.anchors != 1 or self.first_time is None:
                    est.reason = "ps2_without_ps1"
                    continue
                if (not self.history_mode and not self.constant_speed) or belt_command <= 0:
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
                if self.history_mode:
                    if self.anchor_command_distance<=0:
                        est.reason='no_commanded_travel_between_anchors'
                        continue
                    gain=(self.positions['ps2']-self.positions['ps1']-self.anchor_coast)/self.anchor_command_distance
                    low,high=self.parameters['command_gain_range']
                    if not low<=gain<=high:
                        est.reason='implausible_command_gain'
                        continue
                    self.command_gain=gain
                    est.velocity_m_s=gain*belt_command
                    est.command_gain=gain
                else:
                    est.velocity_m_s = speed
                est.anchors = 2
            # A rising edge detects the leading face, not the product center.
            # Half a sample of motion compensates the unknown crossing phase.
            if self.history_mode:
                mean_window=self.command_gain*command_interval['distance_m']/2
                upper_window=self.parameters['command_gain_range'][1]*command_interval['distance_m']+command_interval['stops']*self.stop_coast
                est.y_m=self.positions[name]-self.half_length+mean_window
                est.uncertainty_m=self.parameters['anchor_tolerance_m']+max(mean_window,upper_window-mean_window)
                est.command_gain=self.command_gain
            else:
                est.y_m = self.positions[name] - self.half_length + est.velocity_m_s * dt / 2
                est.uncertainty_m = self.parameters["anchor_tolerance_m"] + est.velocity_m_s * dt / 2
            est.reason = "tracking"
        self.command = belt_command
        self.time = t
        return est
