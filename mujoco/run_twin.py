"""CLI entry point; experiment.run remains import-compatible."""

import argparse
import json
from pathlib import Path
from config import load_config
from experiment import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/dt_sequence"))
    parser.add_argument("--bin", type=int, choices=range(1, 7), default=1)
    parser.add_argument("--speed", type=float, default=None)
    parser.add_argument("--assume-open-loop", action="store_true",
                        help="SIMULATION ONLY: allow timed unconfirmed XY/A2 and suction")
    parser.add_argument("--fault", choices=("none", "ps1_stuck_low", "ps2_stuck_low",
                                           "ps1_stuck_high", "ps2_stuck_high", "a1_extended_stuck_low", "transfer_present_stuck_low", "transfer_present_stuck_high"), default="none")
    parser.add_argument('--fault-start-s',type=float,default=0.0,help='Simulation fixture onset in shared simulation seconds')
    parser.add_argument("--view", action="store_true")
    parser.add_argument("--config", type=Path, help="SI machine profile JSON")
    args = parser.parse_args()
    result = run(args.output, args.bin, args.speed, args.assume_open_loop, args.fault, args.view, config=load_config(args.config),fault_start_s=args.fault_start_s)
    print(json.dumps(result, indent=2))
    if result["placement_pass_evaluator_only"] is False:
        raise SystemExit(1)
