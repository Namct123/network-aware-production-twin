"""Compose independent configuration, plant, sensing, transport, control and evaluation."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time

from config import resolved_config
from evaluation import Evaluator
from model_profile import write_model
from network import Network
from sensor_model import SensorModel
from sequence import Sequence


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def run(output, bin_number=1, speed=None, assume_open_loop=False, fault="none", view=False, config=None):
    if fault not in {"none", "ps1_stuck_low", "ps2_stuck_low", "a1_extended_stuck_low"}:
        raise ValueError("unsupported fault fixture")
    c = resolved_config(config, speed)
    controller = Sequence(bin_number, assume_open_loop=assume_open_loop, config=c)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    model_path = write_model(c, output/"effective_model.xml")
    write_json(output/"effective_config.json", c)
    here = Path(__file__).resolve().parent
    paths = [here/name for name in ("config.py", "model_profile.py", "signals.py", "sensor_model.py",
                                   "estimator.py", "sequence.py", "network.py", "evaluation.py", "experiment.py", "run_cell.py")]
    manifest = {"config_sha256": hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
                "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                "template_sha256": hashlib.sha256((here/"production_cell.xml").read_bytes()).hexdigest(),
                "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
    write_json(output/"manifest.json", manifest)
    from run_cell import Cell
    import mujoco
    manifest["mujoco_version"] = mujoco.__version__
    write_json(output/"manifest.json", manifest)
    cell = Cell(c, model_path)
    sensor, network, evaluator = SensorModel(config=c), Network(c["network"]), Evaluator(c["geometry"])
    dt = c["timing"]["physics_step_s"]*c["timing"]["sample_steps"]
    viewer = None
    if view:
        import mujoco.viewer
        viewer = mujoco.viewer.launch_passive(cell.model, cell.data)
        viewer.cam.lookat[:] = (0, 0, .12)
        viewer.cam.distance = 1.4
        viewer.cam.azimuth, viewer.cam.elevation = 135, -35
    hold_started = None
    # ponytail: bounded single-product experiments keep source truth for timestamp-
    # aligned evaluation. Use a time-bounded ring buffer for continuous production.
    source_truth = {}
    with (output/"source_signals.jsonl").open("w",encoding="utf-8") as emitted, \
         (output/"signals.jsonl").open("w",encoding="utf-8") as signals, \
         (output/"controller.jsonl").open("w",encoding="utf-8") as decisions, \
         (output/"ground_truth.jsonl").open("w",encoding="utf-8") as truth:
        state = cell.observe()
        while True:
            source_frame, _ = sensor.sample(state)
            source_truth[source_frame.sequence] = state
            if fault != "none":
                name = fault.removesuffix("_stuck_low")
                source_frame = replace(source_frame, values={**source_frame.values, name:False})
            emitted.write(json.dumps(source_frame.as_dict(),allow_nan=False)+"\n")
            now = state["time_s"]
            network.send(source_frame,now)
            frame = network.receive(now)
            before = controller.phase
            error = None
            if frame is not None:
                command = controller.tick(frame,now)
                signals.write(json.dumps(frame.as_dict(),allow_nan=False)+"\n")
                # Pair an estimate with the truth at its source sequence, not with
                # a later plant pose merely because the delayed sample arrived now.
                if controller.estimate_sequence == frame.sequence:
                    error = evaluator.observe(controller.estimator.estimate,source_truth[frame.sequence],before)
            else:
                controller.watchdog(now)
                command = controller.command
            if now >= c["timing"]["run_budget_s"] and controller.phase not in {"HOLD","DONE"}:
                controller.hold("run_budget_exceeded",now)
            cell.apply(command)
            estimate = controller.estimator.estimate
            decisions.write(json.dumps({"sequence":source_frame.sequence,"time_s":now,
                "estimate_source_sequence":controller.estimate_sequence,
                "last_received_sequence":controller.last_sequence,"phase":controller.phase,
                "reason":controller.reason,"estimate":estimate.as_dict(),"command":command},allow_nan=False)+"\n")
            truth.write(json.dumps({"sequence":source_frame.sequence,**state,
                "estimate_source_sequence":frame.sequence if error is not None else None,
                "y_estimation_error_m":error},allow_nan=False)+"\n")
            if viewer is not None:
                viewer.sync()
                time.sleep(dt)
            if controller.phase == "DONE":
                break
            if controller.phase == "HOLD":
                if hold_started is None:
                    hold_started = now
                if now-hold_started >= c["timing"]["hold_settle_s"]:
                    break
            state = cell.step()
    estimate = controller.estimator.estimate
    summary = {"controller_state":controller.phase,"hold_reason":controller.reason,
        "simulation_time_s":state["time_s"],"samples":sensor.sequence,"bin":bin_number,
        "commanded_long_belt_speed_m_s":c["motion"]["long_speed_m_s"],"fault_fixture":fault,
        "assume_open_loop":assume_open_loop,"hold_time_s":hold_started,
        "observed_anchor_count":estimate.anchors,"estimated_transit_speed_m_s":estimate.velocity_m_s,
        "profile_name":c["profile"]["name"],"profile_status":c["profile"]["status"],
        "config_sha256":manifest["config_sha256"],"network":network.stats,
        "error_scope":"source-time-aligned estimates after PS1 in TRACK/ALIGN, one product, not all-axis accuracy",
        "assumptions":["single product and known simulation reset; timed front admission",
            "constant long belt command between matched optical edges; known product length and lane",
            "XY/intermediate A2 timed and suction unconfirmed if opt-in enabled",
            "shared simulation clock; no physical PLC clock synchronization"],
        "transitions":controller.transitions,**evaluator.finish(state,controller.phase,bin_number)}
    write_json(output/"summary.json",summary)
    if viewer is not None:
        print("Cycle finished. Close the MuJoCo window to return.",flush=True)
        while viewer.is_running():
            viewer.sync()
            time.sleep(1/60)
        viewer.close()
    return summary
