"""Paired baseline/predictive experiments using the same physical cell and fixtures."""

import argparse
import json
from pathlib import Path
from config import load_config, resolved_config
from experiment import run


def check(output, config=None):
    base=resolved_config(config)
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    cases=[
        ("baseline_nominal",False,"none",0.0,True,False,"DONE",""),
        ("predictive_nominal",True,"none",0.0,True,False,"DONE",""),
        ("baseline_missing_ps2",False,"ps2_stuck_low",0.0,True,False,"HOLD","timeout:TRACK:ps2"),
        ("predictive_missing_ps2",True,"ps2_stuck_low",0.0,True,False,"HOLD","predictive_stop_margin"),
        ("predictive_delay_20ms",True,"none",.020,True,False,"DONE",""),
        ("predictive_loss_all",True,"none",0.0,True,False,"HOLD","telemetry_timeout"),
        ("predictive_strict",True,"none",0.0,False,False,"HOLD","unconfirmed_xy_a2_midstroke_and_vacuum"),
        ("predictive_deadline",True,"none",0.0,True,True,"HOLD","prediction_deadline_exceeded"),
        ("predictive_speed_low",True,"none",0.0,True,False,"DONE",""),
        ("predictive_speed_high",True,"none",0.0,True,False,"DONE",""),
    ]
    results=[]
    for name,enabled,fault,delay,assume,tiny_budget,expected,reason in cases:
        c=resolved_config(base)
        c["prediction"]["enabled"]=enabled
        if name in {"predictive_speed_low","predictive_speed_high"}:
            c["motion"]["long_speed_m_s"]=c["motion"]["test_speed_range_m_s"][0 if name.endswith("low") else 1]
        c["network"].update(delay_s=delay,jitter_s=0.0,drop_probability=1.0 if name=="predictive_loss_all" else 0.0)
        if tiny_budget: c["prediction"]["wall_budget_s"]=1e-9
        r=run(output/name,assume_open_loop=assume,fault=fault,config=c)
        passed=(r["controller_state"]==expected and r["hold_reason"]==reason and
                (r["placement_pass_evaluator_only"] is True if expected=="DONE"
                 else r["hold_product_supported_evaluator_only"] is True))
        results.append({"case":name,"pass":passed,**r})
        (output/"results.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
        print(f"{name}: {'PASS' if passed else 'FAIL'}; {r['controller_state']}; "
              f"reason={r['hold_reason']}; hold={r['hold_time_s']}; prediction={r['prediction']}",flush=True)
    by={r["case"]:r for r in results}
    improvement=by["baseline_missing_ps2"]["hold_time_s"]-by["predictive_missing_ps2"]["hold_time_s"]
    comparison={"missing_ps2_earlier_hold_s":improvement,
                "scope":"one deterministic matched fault fixture; not general fault-detection accuracy or safety proof",
                "all_cases_pass":all(r["pass"] for r in results)}
    (output/"comparison.json").write_text(json.dumps(comparison,indent=2)+"\n",encoding="utf-8")
    if not comparison["all_cases_pass"] or improvement<0:
        raise AssertionError("Predictive acceptance failed; inspect logs without changing outcome criteria")
    print(f"PASS: {len(results)}/{len(cases)}; PS2 HOLD earlier by {improvement:.3f} simulation seconds",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("output/predictive_acceptance"))
    parser.add_argument("--config",type=Path)
    args=parser.parse_args(); check(args.output,load_config(args.config))
