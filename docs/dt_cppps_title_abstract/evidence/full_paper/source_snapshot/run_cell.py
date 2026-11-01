"""Headless physical cell and a one-product commissioning run in MuJoCo WSL."""

import argparse
import csv
import time
from pathlib import Path

import mujoco
import numpy as np
from config import resolved_config
from model_profile import model_xml

HERE = Path(__file__).resolve().parent
MODEL = HERE / "production_cell.xml"


class Cell:
    def __init__(self, config=None, model_path=None):
        self.config = resolved_config(config)
        self.model = (mujoco.MjModel.from_xml_path(str(model_path)) if model_path is not None
                      else mujoco.MjModel.from_xml_string(model_xml(self.config)))
        self.data = mujoco.MjData(self.model)
        self.belts = {key: self.model.geom(key).id for key in ("front_green_belt", "long_green_belt")}
        self.cup = self.model.geom("vacuum_cup").id
        self.product = self.model.body("product").id
        self.actuators = {key: self.model.actuator(key + "_target").id
                          for key in ("x_joint", "y_joint", "a2_joint", "a1_joint")}
        self.rates = self.config["motion"]["rates_m_s"].copy()
        self.last_command = None
        self.reset()

    def reset(self):
        mujoco.mj_resetData(self.model, self.data)
        self.model.geom_surfacevel[:] = 0
        self.model.geom_adhesion[self.cup] = 0
        self.data.ctrl[:] = 0
        self.goals = {key: 0.0 for key in self.actuators}
        mujoco.mj_setConst(self.model, self.data)
        for key, home in zip(("x_joint", "y_joint"), self.config["motion"]["home_xy_m"]):
            self.data.joint(key).qpos[0] = home
            self.data.ctrl[self.actuators[key]] = home
            self.goals[key] = home
        self.last_command = None
        mujoco.mj_forward(self.model, self.data)
        return self.observe()

    def _refresh_constants(self):
        # MuJoCo 3.16 needs mj_setConst after runtime surfacevel/adhesion edits;
        # that call resets mjData, so preserve the physical state and actuator controls.
        spec = mujoco.mjtState.mjSTATE_FULLPHYSICS
        state = np.empty(mujoco.mj_stateSize(self.model, spec))
        mujoco.mj_getState(self.model, self.data, state, spec)
        controls = self.data.ctrl.copy()
        mujoco.mj_setConst(self.model, self.data)
        mujoco.mj_setState(self.model, self.data, state, spec)
        self.data.ctrl[:] = controls
        mujoco.mj_forward(self.model, self.data)

    def belts_at(self, front=0.0, long=0.0):
        scale = self.config["plant"]["belt_speed_scale"]
        self.model.geom_surfacevel[self.belts["front_green_belt"], :3] = (-front*scale["front"], 0, 0)
        self.model.geom_surfacevel[self.belts["long_green_belt"], :3] = (0, long*scale["long"], 0)
        self._refresh_constants()

    def targets(self, **joints):
        for key, value in joints.items():
            actuator = self.actuators[key]
            lo, hi = self.model.actuator_ctrlrange[actuator]
            if not lo <= value <= hi:
                raise ValueError(f"{key} target {value} outside {lo}..{hi} m")
            self.goals[key] = value

    def hold(self):
        """Stop belts and freeze issued ramp setpoints; retain vacuum command."""
        self.belts_at()
        for key, actuator in self.actuators.items():
            self.goals[key] = float(self.data.ctrl[actuator])

    def grip(self, enabled):
        # Provisional contact adhesion, not a calibrated pneumatic pressure model.
        self.model.geom_adhesion[self.cup] = self.config["plant"]["vacuum_adhesion_n"] if enabled else 0.0
        self._refresh_constants()

    def apply(self, command):
        """Actuator boundary: never returns measured pose to the controller."""
        if self.last_command == command:
            return
        if command["hold"]:
            self.hold()
        else:
            self.belts_at(command["front"], command["long"])
            self.targets(**command["targets"])
            if self.last_command is None or self.last_command["vacuum"] != command["vacuum"]:
                self.grip(command["vacuum"])
        from copy import deepcopy
        self.last_command = deepcopy(command)

    def step(self, steps=None):
        steps = self.config["timing"]["sample_steps"] if steps is None else steps
        for _ in range(steps):
            for key, actuator in self.actuators.items():
                current = self.data.ctrl[actuator]
                delta = self.goals[key] - current
                step = self.rates[key] * self.model.opt.timestep
                self.data.ctrl[actuator] = current + max(-step, min(step, delta))
            mujoco.mj_step(self.model, self.data)
        return self.observe()

    def observe(self):
        def ray(key):
            distance = float(self.data.sensor(key + "_range").data[0])
            return 0 < distance < self.config["sensors"]["optical_detection_range_m"]

        xyz = self.data.xpos[self.product].tolist()
        return {
            "time_s": float(self.data.time),
            "product_xyz_m": xyz,
            "ps1": ray("ps1"), "ps2": ray("ps2"),
            "x_m": float(self.data.joint("x_joint").qpos[0]),
            "y_m": float(self.data.joint("y_joint").qpos[0]),
            "a2_m": float(self.data.joint("a2_joint").qpos[0]),
            "a1_m": float(self.data.joint("a1_joint").qpos[0]),
            "vacuum_command": bool(self.model.geom_adhesion[self.cup]),
        }


def commissioning(log_path, bin_number=1, view=False, on_sample=None):
    cell = Cell()
    viewer = None
    if view:
        import mujoco.viewer
        viewer = mujoco.viewer.launch_passive(cell.model, cell.data)
        viewer.cam.lookat[:] = (0, 0, 0.12)
        viewer.cam.distance = 1.4
        viewer.cam.azimuth = 135
        viewer.cam.elevation = -35
    log = []
    if on_sample is not None:
        on_sample("reset", cell.observe())
    row, column = divmod(bin_number - 1, 2)
    bin_x, bin_y = (0.080 if column == 0 else 0.195), 0.075 + row * 0.115

    def advance(phase, stop, seconds):
        end = cell.data.time + seconds
        while cell.data.time < end:
            state = cell.step()
            if on_sample is not None:
                on_sample(phase, state)
            if viewer is not None:
                viewer.sync()
                time.sleep(cell.model.opt.timestep * 10)
            if len(log) == 0 or state["time_s"] - log[-1]["time_s"] >= 0.098:
                log.append({"phase": phase, **state})
            if stop is not None and stop(state):
                print(f"{phase}: {state}")
                return state
        if stop is None:
            state = cell.observe()
            print(f"{phase}: {state}")
            return state
        raise RuntimeError(f"{phase} timed out at {cell.observe()}")

    cell.belts_at(front=0.16)
    advance("front_to_a1", lambda s: s["product_xyz_m"][0] <= -0.175, 6)
    cell.belts_at()
    cell.targets(a1_joint=0.110)
    advance("a1_push", lambda s: s["a1_m"] >= 0.105, 2)
    cell.targets(a1_joint=0)
    cell.belts_at(long=0.16)
    advance("long_to_ps2", lambda s: s["ps2"], 6)
    cell.belts_at()
    # Commissioning uses simulated product pose; real deployment needs a calibrated
    # sensor-stop offset or camera estimate before this target may drive hardware.
    pick = cell.observe()["product_xyz_m"]
    pick_x, pick_y = pick[0] + 0.180, pick[1] - 0.120
    cell.targets(x_joint=pick_x, y_joint=pick_y)
    advance("align_pick", lambda s: abs(s["x_m"] - pick_x) < 0.002 and abs(s["y_m"] - pick_y) < 0.002, 2)
    cell.targets(a2_joint=0.060)
    advance("a2_down", lambda s: s["a2_m"] >= 0.058, 2)
    cell.grip(True)
    advance("grip", None, 0.2)
    cell.targets(a2_joint=0)
    lifted = advance("lift", lambda s: s["a2_m"] <= 0.003, 2)
    if lifted["product_xyz_m"][2] < 0.09:
        raise AssertionError("Vacuum did not lift the product clear of the long belt")
    x_target, y_target = bin_x + 0.180, bin_y - 0.120
    cell.targets(x_joint=x_target, y_joint=y_target)
    advance("move_to_bin", lambda s: abs(s["x_m"] - x_target) < 0.004 and abs(s["y_m"] - y_target) < 0.004, 5)
    cell.targets(a2_joint=0.060)
    advance("lower_to_bin", lambda s: s["a2_m"] >= 0.058, 2)
    cell.grip(False)
    advance("release", None, 0.4)
    cell.targets(a2_joint=0)
    advance("raise", lambda s: s["a2_m"] <= 0.003, 2)
    cell.targets(x_joint=0, y_joint=0)
    advance("home", lambda s: abs(s["x_m"]) < 0.004 and abs(s["y_m"]) < 0.004, 5)
    with log_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=log[0])
        writer.writeheader()
        writer.writerows(log)
    final = cell.observe()
    x, y, z = final["product_xyz_m"]
    if not any(row["ps1"] for row in log):
        raise AssertionError("Product never crossed PS1")
    # Bin interior is 96 mm wide; a 22 mm cube center must remain within 37 mm.
    if not (abs(x - bin_x) < 0.037 and abs(y - bin_y) < 0.037 and 0.020 < z < 0.060):
        raise AssertionError(f"Product did not settle inside bin {bin_number}: {final}")
    print(f"PASS: contact-driven transfer, PS1/PS2, vacuum pickup and bin {bin_number} placement")
    print("Final", final, "log", log_path)
    if viewer is not None:
        print("Cycle complete. Close the MuJoCo window when finished inspecting.", flush=True)
        while viewer.is_running():
            viewer.sync()
            time.sleep(1 / 60)
        viewer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commission", action="store_true", help="Run one full contact-driven cycle")
    parser.add_argument("--bin", type=int, choices=range(1, 7), default=1)
    parser.add_argument("--log", type=Path, default=HERE / "commissioning.csv")
    parser.add_argument("--view", action="store_true", help="Show real-time MuJoCo viewer (requires WSLg)")
    args = parser.parse_args()
    if args.commission:
        commissioning(args.log, args.bin, args.view)
    else:
        cell = Cell()
        print("Loaded", cell.model.ngeom, "geoms,", cell.model.nq, "position coordinates")
        print(cell.step())
