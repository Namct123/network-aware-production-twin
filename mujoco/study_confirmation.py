"""Read-only qualification and ambiguity audit on new closed-loop recordings."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from config import load_config
from pulse_observer import PulseObserver
from signals import SignalFrame
from model_confirmation import qualify
from calibrate_residual import save,digest
from study_pulse import rows

HERE=Path(__file__).resolve().parent

def audit(source,output):
    if output.exists():raise FileExistsError("Do not overwrite audit")
    data=json.loads((source/"results.json").read_text());plan=json.loads((source/"plan.json").read_text());base=load_config(HERE/"configs/reconfigurable_cell_20261030.json");base["estimator"]["drift_m_s"]=plan["drift_m_s"]
    runs=[];hashes={}
    for trial in data["runs"]:
        decisions=rows(source/trial["id"]/"decisions.jsonl")
        observer=PulseObserver(base,{"gain_bounds":[.8,1.2],"drift_m_s":plan["drift_m_s"],"confirm_samples":2},plan["length_guard_m"])
        last=None;seen_stop=None
        for row in decisions:
            frame=SignalFrame(**row["received"]) if row["received"] is not None else None
            record=observer.observe(frame,row["time_s"])
            if record!=row["observer"]:raise ValueError("Observer replay mismatch")
            if seen_stop is None and row["stop_reason"] is not None:seen_stop=row["time_s"]
            last=qualify(record,observer,row["time_s"],seen_stop,plan["settle_s"],trial["zone_m"],base)
            observer.issued(row["time_s"],row["command"]["long"])
        # Pose is used only after all eligibility decisions, for scoring false conditional claims.
        y=trial["evaluator_final_y_m"];inside=trial["zone_m"][0]<=y<=trial["zone_m"][1]
        runs.append({"id":trial["id"],"policy":trial["policy"],"fault":trial["fixture"]["fault"],"zone":trial["zone"],"qualification":last,"truth_inside":inside,"false_conditional_claim":last["conditional_position_ok"] and not inside})
        for name in ("decisions.jsonl","evaluator_only.jsonl"):hashes[trial["id"]+"/"+name]=digest(source/trial["id"]/name)
    pairs=[]
    for left in data["runs"]:
        if left["fixture"]["fault"]!="pickup_missing":continue
        other=next(x for x in data["runs"] if x["zone"]==left["zone"] and x["policy"]==left["policy"] and x["fixture"]=={**left["fixture"],"fault":"drive_stall"})
        a=rows(source/left["id"]/"decisions.jsonl");b=rows(source/other["id"]/"decisions.jsonl")
        obs_equal=[x["received"] for x in a]==[x["received"] for x in b]
        # Ignore compute timing only; retain forecast status and deadline-dependent action.
        def logical(records):
            result=deepcopy(records)
            for row in result:
                for forecast in row["forecasts"]:forecast["forecast"].pop("compute_ms",None)
            return result
        pairs.append({"left":left["id"],"right":other["id"],"observations_equal":obs_equal,"logical_decisions_equal":logical(a)==logical(b),"final_y_difference_m":abs(left["evaluator_final_y_m"]-other["evaluator_final_y_m"])})
    report={"runs":runs,"pairs":pairs,"conditional_claims":sum(r["qualification"]["conditional_position_ok"] for r in runs),"release_eligible_claims":sum(r["qualification"]["release_eligible"] for r in runs),"false_conditional_claims":sum(r["false_conditional_claim"] for r in runs),"input_sha256":hashes,"audit_source_sha256":digest(Path(__file__)),"physical_validation":False,"scope":"Read-only qualification, not operational bypass. Actuation evidence remains unavailable; no claim of impossibility with independent feedback."}
    save(output,report);print(json.dumps({k:report[k] for k in ("conditional_claims","release_eligible_claims","false_conditional_claims")}|{"pairs":len(pairs),"identical_pairs":sum(p["observations_equal"] and p["logical_decisions_equal"] for p in pairs)}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();audit(a.source,a.output)
