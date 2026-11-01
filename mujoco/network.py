"""Seeded simulation-only transport: delay, uniform jitter, loss and receiver order."""

from dataclasses import replace
import heapq
import random
from config import exact_keys, number, validate_outages


class Network:
    def __init__(self, parameters):
        exact_keys(parameters, ("delay_s", "jitter_s", "drop_probability", "seed",*(['outage_windows_s'] if 'outage_windows_s' in parameters else [])), "network")
        validate_outages(parameters.get('outage_windows_s',[]))
        for key in ("delay_s", "jitter_s", "drop_probability"):
            number(parameters[key], key, 0)
        if parameters["drop_probability"] > 1 or type(parameters["seed"]) is not int or parameters["seed"] < 0:
            raise ValueError("invalid network probability/seed")
        self.parameters = parameters.copy()
        self.rng = random.Random(parameters["seed"])
        self.pending = []
        self.last_sequence = -1
        self.last_sent = -1
        self.stats = {"sent": 0, "dropped": 0, "delivered": 0, "accepted": 0, "out_of_order_ignored": 0, "coalesced": 0}

    def send(self, frame, now):
        if frame.source_time_s > now or frame.sequence <= self.last_sent:
            raise ValueError("send requires ordered unique source samples, not future data")
        self.last_sent = frame.sequence
        self.stats["sent"] += 1
        if self.rng.random() < self.parameters["drop_probability"]:
            self.stats["dropped"] += 1
            return
        if any(a<=now<b for a,b in self.parameters.get('outage_windows_s',[])):
            self.stats['dropped']+=1
            return
        delay = max(0, self.parameters["delay_s"] + self.rng.uniform(
                    -self.parameters["jitter_s"], self.parameters["jitter_s"]))
        heapq.heappush(self.pending, (now+delay, frame.sequence, frame))

    def receive(self, now):
        latest = None
        while self.pending and self.pending[0][0] <= now+1e-10:
            _, _, frame = heapq.heappop(self.pending)
            self.stats["delivered"] += 1
            if frame.sequence <= self.last_sequence:
                self.stats["out_of_order_ignored"] += 1
                continue
            self.last_sequence = frame.sequence
            if latest is not None:
                self.stats["coalesced"] += 1
            latest = replace(frame, received_time_s=now)
        if latest is not None:
            self.stats["accepted"] += 1
        return latest
