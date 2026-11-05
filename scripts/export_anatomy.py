"""Export a faithful, read-only teaching view of seven existing MuJoCo trials."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "nominal": "Bình thường — thiếu xác nhận để gắp",
    "feed_sensor_missing": "PS1 không báo có phôi",
    "feed_drive_stall": "Băng cấp phôi đứng",
    "pickup_sensor_missing": "PS3 không báo có phôi",
    "long_drive_stall": "Băng dọc đứng",
    "pickup_sensor_high": "PS3 luôn báo có phôi",
    "upstream_sensor_missing": "PS2 không báo có phôi",
}

def export(source):
    files = {}
    def read(p):
        files[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        return p.read_text(encoding="utf-8")
    trials = []
    for case, label in CASES.items():
        folder = source / ("01_" + case)
        summary = json.loads(read(folder / "summary.json"))
        rows = [list(map(json.loads, read(folder / name).splitlines())) for name in
                ("observations.jsonl", "decisions.jsonl", "truth_evaluator_only.jsonl")]
        obs, decisions, truth = rows
        if not len(obs) == len(decisions) == len(truth):
            raise ValueError("Unaligned source records")
        frames = []
        for o, d, t in zip(obs, decisions, truth):
            if abs(o["received_time_s"]-d["time_s"]) > 1e-8 or abs(d["time_s"]-t["time_s"]) > 1e-8:
                raise ValueError("Mismatching source clocks")
            frames.append({"t": d["time_s"], "p": t["product_xyz_m"], "o": o["values"],
                           "quality": o["quality"], "phase": d["phase"], "reason": d["reason"],
                           "estimate": d["estimate"], "command": d["command"],
                           "applied": t["applied_command"], "health": d["health"],
                           "prediction": d["prediction"], "policy": d["policy"]})
        trials.append({"id": case, "label": label, "summary": summary, "frames": frames})
    model = ET.fromstring(read(source / "01_nominal/effective_model.xml"))
    config = json.loads(read(source / "01_nominal/effective_config.json"))
    geometry = []
    def visit(node, origin=(0,0,0)):
        pos = tuple(map(float, node.get("pos", "0 0 0").split())) if node.tag == "body" else (0,0,0)
        origin = tuple(a+b for a,b in zip(origin,pos))
        for child in node:
            if child.tag == "geom" and child.get("type") == "box":
                xyz = [a+b for a,b in zip(origin,map(float,child.get("pos","0 0 0").split()))]
                geometry.append({"name": child.get("name"), "p":xyz,
                                 "s":list(map(float,child.get("size").split()))})
            elif child.tag == "site":
                xyz = [a+b for a,b in zip(origin,map(float,child.get("pos","0 0 0").split()))]
                geometry.append({"name": child.get("name"), "p":xyz, "s":[.006,.006,.006], "site":True})
            elif child.tag == "body": visit(child, origin)
    visit(model.find("worldbody"))
    return {"schema":1, "scope":"recorded_simulation_not_live_hardware",
            "source_study":"sensor_drive_20261104_v2", "units":"m, s",
            "geometry_scope":"MuJoCo functional baseline; not synchronized CAD V5",
            "geometry":geometry,"product_size_m":config["geometry"]["product_size_m"],
            "trials":trials, "source_hashes":files}

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--source",type=Path,default=ROOT/"output/docker/sensor_drive_20261104_v2")
    p.add_argument("--output",type=Path,default=ROOT/"web/anatomy_data.json")
    args=p.parse_args(); data=export(args.source.resolve())
    args.output.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"trials":len(data["trials"]),"frames":sum(len(t["frames"]) for t in data["trials"]),"output":str(args.output)}))
