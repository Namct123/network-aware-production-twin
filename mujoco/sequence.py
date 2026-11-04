"""Tick-driven single-product baseline; accepts SignalFrame, never plant state."""

import math
from copy import deepcopy
from estimator import BeltEstimator
from config import resolved_config
from clock_checks import elapsed_at_least


class Sequence:
    def __init__(self, bin_number=1, belt_speed=None, assume_open_loop=False, config=None):
        self.config = resolved_config(config, belt_speed)
        self.geometry, self.motion, self.timing = (self.config[k] for k in ("geometry", "motion", "timing"))
        belt_speed = self.motion["long_speed_m_s"]
        if type(bin_number) is not int or not 1 <= bin_number <= 6:
            raise ValueError("bin must be 1..6")
        self.estimator = BeltEstimator(config=self.config)
        self.belt_speed = belt_speed
        self.assume_open_loop = assume_open_loop
        self.bin_target = tuple(p-o for p,o in zip(self.geometry["bin_centers_xy_m"][bin_number-1],
                                                 self.geometry["robot_origin_xy_m"]))
        self.phase = "INIT"
        self.reason = ""
        self.entered = 0.0
        self.duration = 0.0
        self.last_sequence = -1
        self.last_time = None
        self.last_received = 0.0
        self.estimate_sequence = None
        self.xy = tuple(self.motion["home_xy_m"])  # Known simulation reset, not measured home.
        self.command = {"front": 0.0, "long": 0.0, "targets": {}, "vacuum": False, "hold": False}
        self.transitions = []
        self.hold_context = None
        self.admission_seen_at = None
        self.age_travel_m=0.0
        self.age_travel_bound_m=0.0
        self.prediction_speed_bound_m_s=None

    def hold(self, reason, now):
        if self.phase != "HOLD":
            self.reason = reason
            self._enter("HOLD", now)

    def _enter(self, phase, now):
        if phase=='HOLD' and self.hold_context is None:
            self.hold_context={'time_s':now,'from_phase':self.phase,'reason':self.reason,
                'last_source_time_s':self.last_time,'last_sequence':self.last_sequence,
                'estimate_source_sequence':self.estimate_sequence,'estimate':self.estimator.estimate.as_dict(),
                'command_before_hold':deepcopy(self.command)}
        self.transitions.append({"time_s": now, "from": self.phase, "to": phase, "reason": self.reason})
        self.phase, self.entered = phase, now
        c = self.command
        if phase == "FEED":
            c["front"] = self.motion["front_speed_m_s"]
        elif phase == "PUSH":
            c["front"] = 0.0
            c["targets"]["a1_joint"] = self.geometry["joint_limits_m"]["a1_joint"][1]
        elif phase == "RETRACT":
            c["targets"]["a1_joint"] = 0.0
        elif phase == "TRACK":
            c["long"] = self.belt_speed
        elif phase == "ALIGN":
            c["long"] = 0.0
            age_travel = (self.age_travel_m if self.estimator.history_mode else
                          self.estimator.estimate.velocity_m_s * max(0, now-self.last_time))
            target = (self.geometry["lane_x_m"]-self.geometry["robot_origin_xy_m"][0],
                      self.estimator.estimate.y_m + age_travel + self.estimator.stop_coast
                      - self.geometry["robot_origin_xy_m"][1])
            self._motion(target)
        elif phase in {"LOWER", "LOWER_BIN"}:
            descent = (self.config['mechanics']['bin_release_descent_m']
                       if phase == 'LOWER_BIN' and 'mechanics' in self.config else self.motion['a2_pick_m'])
            c["targets"]["a2_joint"] = descent
            self.duration = descent/self.motion["rates_m_s"]["a2_joint"] + self.motion["a2_settle_s"]
        elif phase == "GRIP":
            c["vacuum"] = True
        elif phase in {"LIFT", "RAISE"}:
            c["targets"]["a2_joint"] = 0.0
        elif phase == "MOVE":
            self._motion(self.bin_target)
        elif phase == "RELEASE":
            c["vacuum"] = False
        elif phase == "RETURN":
            self._motion(tuple(self.motion["home_xy_m"]))
        elif phase in {"HOLD", "DONE"}:
            c["front"] = c["long"] = 0.0
            c["hold"] = True  # Keep the existing vacuum command, especially with a suspended load.

    def _motion(self, target):
        if not all(self.geometry["joint_limits_m"][j][0] <= q <= self.geometry["joint_limits_m"][j][1]
                   for j,q in zip(("x_joint", "y_joint"),target)):
            self.hold("target_outside_workspace", self.entered)
            return
        self.duration = max(abs(a-b)/self.motion["rates_m_s"][j]
                            for j,a,b in zip(("x_joint", "y_joint"),target,self.xy)) + self.motion["axis_settle_s"]
        self.xy = target
        self.command["targets"].update(x_joint=target[0], y_joint=target[1])

    def tick(self, frame, now, source_belt_command=None, command_interval=None, commanded_track_distance_m=None,
             source_to_now_interval=None):
        if self.phase in {"HOLD", "DONE"}:
            return self.command
        if frame.sequence <= self.last_sequence or (
                self.last_time is not None and frame.source_time_s <= self.last_time):
            self.hold("nonmonotonic_sample", now)
            return self.command
        if self.last_time is not None and frame.source_time_s - self.last_time > self.timing["max_sample_gap_s"]:
            self.hold("sampling_gap", now)
            return self.command
        fresh = frame.aged(now, self.timing["max_age_s"])
        required = ("ps1", "ps2", "a1_retracted", "a1_extended", "a2_retracted")
        if 'mechanics' in self.config and self.phase in {'INIT','FEED'}:
            required += ('transfer_present',)
        for name in required:
            if fresh.quality.get(name) != "good":
                self.hold("invalid_or_stale:" + name, now)
                return self.command
        self.last_sequence, self.last_time = frame.sequence, frame.source_time_s
        self.last_received = frame.received_time_s
        v = fresh.values
        elapsed = now - self.entered
        if v["a1_retracted"] and v["a1_extended"]:
            self.hold("contradictory_a1_switches", now)
            return self.command
        if v["a2_retracted"] and v.get("a2_extended") is True:
            self.hold("contradictory_a2_switches", now)
            return self.command
        if self.phase in {"TRACK", "ALIGN"}:
            belt_at_source = self.command["long"] if source_belt_command is None else source_belt_command
            estimate = self.estimator.update(fresh, belt_at_source, command_interval)
            self.estimate_sequence = frame.sequence
            if estimate.reason not in {"not_observed", "tracking"}:
                self.hold(estimate.reason, now)
                return self.command
            if self.estimator.history_mode:
                if now-frame.source_time_s>1e-9 and source_to_now_interval is None:
                    self.hold('command_history_unavailable',now)
                    return self.command
                age=source_to_now_interval or {'distance_m':0,'stops':0,'speed_variation_m_s':0}
                self.age_travel_m=self.estimator.command_gain*age['distance_m']+age['stops']*self.estimator.stop_coast
                self.age_travel_bound_m=(self.config['estimator']['command_gain_range'][1]*age['distance_m']
                    +age['stops']*self.estimator.stop_coast
                    +self.config['estimator']['command_response_uncertainty_s']*age['speed_variation_m_s'])
        if self.phase == "INIT":
            if not (v["a1_retracted"] and v["a2_retracted"]) or v["ps1"] or v["ps2"] or (
                    'mechanics' in self.config and v['transfer_present']):
                self.hold("initial_state_not_confirmed", now)
            else:
                self._enter("FEED", now)
        elif self.phase == "FEED":
            # ponytail: one product at known reset x=.20; no admission sensor exists.
            # Timed feed is not valid for arbitrary arrivals or front-belt slip.
            if 'mechanics' in self.config:
                mechanics=self.config['mechanics']
                if v['transfer_present'] and self.admission_seen_at is None:
                    self.admission_seen_at=frame.source_time_s if self.estimator.history_mode else now
                if self.admission_seen_at is not None and now-self.admission_seen_at >= mechanics['admission_centering_distance_m']/self.motion['front_speed_m_s']:
                    self._enter('PUSH',now)
                elif elapsed >= min(mechanics['admission_timeout_s'],
                    (self.geometry['product_initial_xyz_m'][0]-self.geometry['front_belt_xy_m'][0][0]
                     -self.geometry['product_size_m'][0]/2-mechanics['admission_stop_margin_m']-mechanics['front_stop_coast_m'])/self.motion['front_speed_m_s']):
                    self.hold('timeout:FEED:transfer_present',now)
            elif elapsed >= self.motion["feed_distance_m"]/self.motion["front_speed_m_s"] + self.motion["feed_startup_s"]:
                self._enter("PUSH", now)
        elif self.phase in {"PUSH", "RETRACT", "LIFT", "RAISE"}:
            signal, target = {"PUSH": ("a1_extended", "RETRACT"),
                              "RETRACT": ("a1_retracted", "TRACK"),
                              "LIFT": ("a2_retracted", "MOVE"),
                              "RAISE": ("a2_retracted", "RETURN")}[self.phase]
            if v[signal]:
                self._enter(target, now)
            elif elapsed >= self.timing["cylinder_timeout_s"]:
                self.hold("timeout:" + self.phase + ":" + signal, now)
        elif self.phase == "TRACK":
            if v["ps2"]:
                e = self.estimator.estimate
                if e.anchors != 2:
                    self.hold("missing_optical_anchors", now)
                elif (e.uncertainty_m + self.estimator.stop_coast
                      + (self.age_travel_bound_m if self.estimator.history_mode else e.velocity_m_s * max(0, now-frame.source_time_s))
                      > self.config["estimator"]["pick_uncertainty_limit_m"]):
                    self.hold("pick_uncertainty_exceeded", now)
                elif not self.assume_open_loop:
                    self.hold("unconfirmed_xy_a2_midstroke_and_vacuum", now)
                else:
                    self._enter("ALIGN", now)
            # Known single-product transfer: 0.44 m travel budget must expire
            # before the product can run off the 0.47 m remaining support lane.
            # This is a model-based timeout, not a verified physical safety limit.
            elif self.estimator.history_mode and commanded_track_distance_m is None:
                self.hold('command_history_unavailable',now)
            elif ((self.estimator.history_mode and (elapsed>=self.timing['track_timeout_max_s']
                    or commanded_track_distance_m>=self.timing['track_travel_budget_m']))
                  or (not self.estimator.history_mode and elapsed >= min(self.timing["track_timeout_max_s"],
                      self.timing["track_travel_budget_m"]/self.belt_speed))):
                self.hold("timeout:TRACK:ps2", now)
        elif self.phase in {"ALIGN", "LOWER", "MOVE", "LOWER_BIN", "RETURN"}:
            if elapsed >= self.duration:
                self._enter({"ALIGN": "LOWER", "LOWER": "GRIP", "MOVE": "LOWER_BIN",
                             "LOWER_BIN": "RELEASE", "RETURN": "DONE"}[self.phase], now)
        elif self.phase == "GRIP" and elapsed >= self.motion["grip_wait_s"]:
            self._enter("LIFT", now)
        elif self.phase == "RELEASE" and elapsed >= self.motion["release_wait_s"]:
            self._enter("RAISE", now)
        return self.command

    def watchdog(self, now):
        """No new frame is different from receiving a fresh False value."""
        if self.phase not in {"HOLD", "DONE"} and elapsed_at_least(now,self.last_received,self.timing["silence_timeout_s"]):
            self.hold("telemetry_timeout", now)
