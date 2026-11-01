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
from supervisor import Supervisor
from calibrate import parameter_report
from command_history import CommandHistory
from health import SignalHealth
from reconfiguration import Reconfiguration
from recovery import RecoveryAssessment
from runtime import RuntimeCore


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def run(output, bin_number=1, speed=None, assume_open_loop=False, fault="none", view=False, config=None, fault_start_s=0.0,prepared_cell=None,session_context=None):
    if fault not in {"none", "ps1_stuck_low", "ps2_stuck_low", "ps1_stuck_high", "ps2_stuck_high", "a1_extended_stuck_low", "transfer_present_stuck_low", "transfer_present_stuck_high"}:
        raise ValueError("unsupported fault fixture")
    c = resolved_config(config, speed)
    if prepared_cell is not None:
        from run_cell import Cell
        if not isinstance(prepared_cell,Cell) or prepared_cell.config!=c or prepared_cell.data.time!=0 or prepared_cell.last_command is not None:
            raise ValueError('prepared cell must be a fresh, uncommanded simulation scene with identical configuration')
    from config import number
    number(fault_start_s,'fault_start_s',0)
    if fault.startswith('transfer_present_') and 'mechanics' not in c:
        raise ValueError('transfer_present fault requires a profile with the third sensor')
    runtime=RuntimeCore(c,bin_number,assume_open_loop,session_context=session_context)
    controller=runtime.controller
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    model_path = write_model(c, output/"effective_model.xml")
    write_json(output/"effective_config.json", c)
    write_json(output/'parameters.json',parameter_report(c))
    here = Path(__file__).resolve().parent
    paths = [here/name for name in ("config.py", "model_profile.py", "signals.py", "sensor_model.py",
                                   "estimator.py", "sequence.py", "network.py", "predictor.py", "supervisor.py",
                                   "evaluation.py", "experiment.py", "run_cell.py", "calibrate.py", "health.py", "command_history.py", "reconfiguration.py", "speed_policy.py", "recovery.py", "runtime.py", "session.py", "physics_predictor.py")]
    if 'mechanics' in c:
        paths.append(here/'parametric_cell.py')
    manifest = {"config_sha256": hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
                "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                "template_sha256": hashlib.sha256((here/"production_cell.xml").read_bytes()).hexdigest() if 'mechanics' not in c else None,
                "model_origin": 'parameterized_functional_plant' if 'mechanics' in c else 'legacy_template',
                "initialization":'prepared_simulation_scene' if prepared_cell is not None else 'new_simulation_scene',
                "session":runtime.context,
                "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
    write_json(output/"manifest.json", manifest)
    from run_cell import Cell
    import mujoco
    manifest["mujoco_version"] = mujoco.__version__
    write_json(output/"manifest.json", manifest)
    cell = prepared_cell if prepared_cell is not None else Cell(c, model_path)
    sensor, network, evaluator = SensorModel(config=c), Network(c["network"]), Evaluator(c["geometry"])
    supervisor=runtime.supervisor
    history,health=runtime.history,runtime.health
    reconfiguration,recovery=runtime.reconfiguration,runtime.recovery
    schedule_events=runtime.schedule_events
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
         (output/"ground_truth.jsonl").open("w",encoding="utf-8") as truth, \
         (output/"prediction.jsonl").open("w",encoding="utf-8") as predictions, \
         (output/'health.jsonl').open('w',encoding='utf-8') as health_log, \
         (output/'reconfiguration.jsonl').open('w',encoding='utf-8') as policy_log, \
         (output/'recovery.jsonl').open('w',encoding='utf-8') as recovery_log, \
         (output/'messages.jsonl').open('w',encoding='utf-8') as message_log:
        state = cell.observe()
        while True:
            source_frame, _ = sensor.sample(state)
            source_truth[source_frame.sequence] = state
            if fault != "none" and state['time_s']>=fault_start_s:
                name,level = fault.rsplit('_stuck_',1)
                source_frame = replace(source_frame, values={**source_frame.values, name:level=='high'})
            emitted.write(json.dumps(source_frame.as_dict(),allow_nan=False)+"\n")
            now = state["time_s"]
            network.send(runtime.wrap(source_frame),now)
            incoming=network.receive(now)
            step=runtime.step(incoming,now)
            frame=step['frame']; before=step['before_phase']; command=step['command']; error=None
            if frame is not None:
                signals.write(json.dumps(frame.as_dict(),allow_nan=False)+"\n")
                if controller.estimate_sequence==frame.sequence:
                    error=evaluator.observe(controller.estimator.estimate,source_truth[frame.sequence],before)
            for key,target in (('prediction',predictions),('health',health_log),('policy',policy_log),('recovery',recovery_log)):
                if step[key] is not None: target.write(json.dumps(step[key],allow_nan=False)+"\n")
            message_log.write(json.dumps({k:step[k] for k in ('received_message','input_guard','command_message','output_guard','command_error')},allow_nan=False)+"\n")
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
        "fault_start_s":fault_start_s,"speed_schedule_events":schedule_events,"signal_health":health.summary(),
        "reconfiguration":reconfiguration.summary(),
        "hold_context":controller.hold_context,"recovery_assessment":recovery.summary(),
        "assume_open_loop":assume_open_loop,"hold_time_s":hold_started,
        "observed_anchor_count":estimate.anchors,"estimated_transit_speed_m_s":estimate.velocity_m_s,
        "estimated_command_gain":estimate.command_gain,
        "profile_name":c["profile"]["name"],"profile_status":c["profile"]["status"],
        "physical_sensor_roles":c.get('mechanics',{}).get('sensor_roles',{'ps1':'baseline_ps1','ps2':'baseline_ps2'}),
        "config_sha256":manifest["config_sha256"],"network":network.stats,
        "session":runtime.context,"message_guard":{"accepted":runtime.guard.accepted,"rejected":runtime.guard.rejected},
        "prediction":supervisor.summary(),
        "error_scope":"source-time-aligned estimates after PS1 in TRACK/ALIGN, one product, not all-axis accuracy",
        "assumptions":["single product; admission from pusher sensor with provisional centering offset" if 'mechanics' in c
                       else "single product and known simulation reset; timed front admission",
            "piecewise issued command integral; bounded provisional command-to-motion gain; not encoder feedback" if controller.estimator.history_mode else "constant long belt command between matched optical edges; known product length and lane",
            "XY/intermediate A2 timed and suction unconfirmed if opt-in enabled",
            "shared simulation clock; no physical PLC clock synchronization"],
        "transitions":controller.transitions,**evaluator.finish(state,controller.phase,bin_number)}
    write_json(output/"summary.json",summary)
    write_json(output/'issued_commands.json',history.records)
    if viewer is not None:
        print("Cycle finished. Close the MuJoCo window to return.",flush=True)
        while viewer.is_running():
            viewer.sync()
            time.sleep(1/60)
        viewer.close()
    return summary
