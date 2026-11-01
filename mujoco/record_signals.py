"""Record ideal I/O separately from evaluator truth, or replay I/O without MuJoCo."""

import argparse
import json
from pathlib import Path
from signals import SignalFrame
from sensor_model import SensorModel


def replay(path):
    count, gaps, transitions = 0, 0, 0
    previous = None
    last = None
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            frame = SignalFrame(**json.loads(line))
            if previous is not None:
                if frame.sequence <= previous.sequence or frame.source_time_s <= previous.source_time_s:
                    raise ValueError("reordered/duplicate samples require a network receiver, not this replay")
                if frame.values.keys() != previous.values.keys():
                    raise ValueError("signal schema changed during the recording")
                gaps += frame.sequence - previous.sequence - 1
                transitions += sum(frame.values[k] != previous.values[k] for k in frame.values)
            previous = last = frame
            count += 1
    if last is None:
        raise ValueError("empty recording")
    return {"samples": count, "sequence_gaps": gaps, "observed_transitions": transitions,
            "last_source_time_s": last.source_time_s, "clock_domain": last.clock_domain}


def record(output, bin_number=1, view=False):
    # Import only for a physical simulation run; replay needs the standard library only.
    from run_cell import commissioning
    sensor = SensorModel()
    limits = sensor.limits
    output = Path(output)
    # Refuse overwriting a recording, including partial evidence after a failed run.
    output.mkdir(parents=True, exist_ok=False)
    with (output / "signals.jsonl").open("w", encoding="utf-8") as signals, \
            (output / "edges.jsonl").open("w", encoding="utf-8") as events, \
            (output / "ground_truth.jsonl").open("w", encoding="utf-8") as truth:
        def capture(phase, state):
            frame, edges = sensor.sample(state)
            signals.write(json.dumps(frame.as_dict(), allow_nan=False) + "\n")
            for edge in edges:
                events.write(json.dumps(edge, allow_nan=False) + "\n")
            truth.write(json.dumps({"sequence": frame.sequence, "phase": phase, **state},
                                   allow_nan=False) + "\n")

        commissioning(output / "commissioning.csv", bin_number, view, on_sample=capture)
    summary = {**replay(output / "signals.jsonl"), "bin": bin_number,
               "a1_limits_m": limits["a1"], "a2_limits_m": limits["a2"],
               "end_switch_tolerance_m": sensor.tolerance_m,
               "controller": "existing commissioning uses ground truth; NOT sensor-only control",
               "sensors": "ideal simulated digital I/O; no noise/network or hardware calibration"}
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/dt_signals"))
    parser.add_argument("--bin", type=int, choices=range(1, 7), default=1)
    parser.add_argument("--view", action="store_true")
    parser.add_argument("--replay", type=Path, help="Read an existing signals.jsonl; no simulator needed")
    args = parser.parse_args()
    print(json.dumps(replay(args.replay) if args.replay else record(args.output, args.bin, args.view),
                     indent=2))
