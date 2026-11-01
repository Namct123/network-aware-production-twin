"""Reproducible acceptance cases; run in the existing MuJoCo WSL environment."""

import argparse
import json
from pathlib import Path
from run_twin import run
from config import load_config, resolved_config
from calibrate import set_value


def check(output, config=None, extended=False):
    config = resolved_config(config)
    nominal = config["motion"]["long_speed_m_s"]
    low, high = config["motion"]["test_speed_range_m_s"]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    cases = [(f"bin_{b}", b, nominal, True, "none", "DONE", "") for b in range(1, 7)]
    cases += [("speed_low", 1, low, True, "none", "DONE", ""),
              ("speed_high", 1, high, True, "none", "DONE", ""),
              ("strict", 1, nominal, False, "none", "HOLD", "unconfirmed_xy_a2_midstroke_and_vacuum"),
              ("missing_ps1", 1, nominal, True, "ps1_stuck_low", "HOLD", "ps2_without_ps1"),
              ("missing_ps2", 1, nominal, True, "ps2_stuck_low", "HOLD", "timeout:TRACK:ps2"),
              ("missing_a1_end", 1, nominal, True, "a1_extended_stuck_low", "HOLD", "timeout:PUSH:a1_extended")]
    cases = [(*case,config) for case in cases]
    if extended:
        variations = [
            ("profile_geometry_slow_a2", {"geometry.ps_y_m.ps2":config["geometry"]["ps_y_m"]["ps2"]-.005,
                                  "geometry.bin_centers_xy_m.0.0":config["geometry"]["bin_centers_xy_m"][0][0]+.005,
                                  "motion.rates_m_s.a2_joint":.060}, "DONE", ""),
            ("profile_dynamics_slow_a2", {"plant.product_mass_kg":config["plant"]["product_mass_kg"]*1.1,
                                  "motion.rates_m_s.x_joint":config["motion"]["rates_m_s"]["x_joint"]*.85,
                                  "motion.rates_m_s.a2_joint":.060}, "DONE", ""),
            ("network_delay_20ms", {"network.delay_s":.020}, "DONE", ""),
            ("network_stale", {"network.delay_s":.080,"timing.max_age_s":.050}, "HOLD", "invalid_or_stale:ps1"),
            ("network_loss_all", {"network.drop_probability":1.0}, "HOLD", "telemetry_timeout"),
            ("network_pick_age", {"network.delay_s":.040}, "HOLD", "pick_uncertainty_exceeded")]
        for name,patch,expected,reason in variations:
            variant=resolved_config(config)
            for path,value in patch.items():
                set_value(variant,path,value)
            variant["profile"].update(name=name+"_synthetic_test",status="unmeasured",measurements=[],
                                      notes="Synthetic modular regression variation, not physical measurement.")
            cases.append((name,1,nominal,True,"none",expected,reason,variant))
    results = []
    for name, bin_number, speed, assume, fault, expected, reason, profile in cases:
        result = run(output/name, bin_number, speed, assume, fault, config=profile)
        passed = (result["controller_state"] == expected and result["hold_reason"] == reason
                  and (expected != "DONE" or result["placement_pass_evaluator_only"] is True)
                  and (expected != "HOLD" or result["hold_product_supported_evaluator_only"] is True))
        results.append({"case": name, "pass": passed, **result})
        print(f"{name}: {'PASS' if passed else 'FAIL'}; state={result['controller_state']}; "
              f"reason={result['hold_reason']}; t={result['simulation_time_s']:.2f}s", flush=True)
        (output/"results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    if not all(r["pass"] for r in results):
        raise AssertionError("Acceptance case failed; inspect per-case signals, decisions and truth")
    print(f"PASS: {len(results)}/{len(cases)} acceptance cases", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/dt_acceptance"))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--extended", action="store_true", help="Also test profile changes and network disturbances")
    args=parser.parse_args()
    check(args.output,load_config(args.config),args.extended)
