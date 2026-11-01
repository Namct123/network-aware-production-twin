"""Controller-facing digital signals; no simulator ground truth or commands."""

from dataclasses import asdict, dataclass, replace
import math


@dataclass(frozen=True)
class SignalFrame:
    sequence: int
    source_time_s: float
    received_time_s: float
    values: dict
    quality: dict
    source: str = "simulated_io"
    clock_domain: str = "simulation"

    def __post_init__(self):
        if type(self.sequence) is not int or self.sequence < 0:
            raise ValueError("sequence must be a nonnegative integer")
        if not all(math.isfinite(t) and t >= 0 for t in
                   (self.source_time_s, self.received_time_s)):
            raise ValueError("timestamps must be finite and nonnegative")
        if self.received_time_s < self.source_time_s:
            raise ValueError("reception precedes source time in the shared simulation clock")
        if self.clock_domain != "simulation" or self.source != "simulated_io":
            raise ValueError("only the shared simulation clock/source is implemented")
        if not self.values or self.values.keys() != self.quality.keys():
            raise ValueError("each signal needs an explicit quality")
        for name, value in self.values.items():
            quality = self.quality[name]
            if value is not None and type(value) is not bool:
                raise ValueError(f"{name}: expected bool or None")
            if quality not in {"good", "stale", "unavailable"}:
                raise ValueError(f"{name}: unsupported quality {quality}")
            if (value is None) != (quality == "unavailable"):
                raise ValueError(f"{name}: unavailable must be None; good/stale must be bool")

    def as_dict(self):
        return asdict(self)

    def aged(self, now_s, max_age_s):
        if not math.isfinite(now_s) or now_s < self.received_time_s:
            raise ValueError("evaluation must be at/after reception in the same clock")
        if not math.isfinite(max_age_s) or max_age_s < 0:
            raise ValueError("max_age_s must be finite and nonnegative")
        if now_s - self.source_time_s <= max_age_s:
            return self
        return replace(self, quality={name: "stale" if q == "good" else q
                                     for name, q in self.quality.items()})
