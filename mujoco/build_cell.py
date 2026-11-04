"""Build a MuJoCo cell from the Fusion/CAD part ledger and canonical URDF joints."""

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = HERE.parent / "cad_reference/production_twin_v0_parts.csv"
URDF = HERE / "production_cell.urdf"
OUT = HERE / "production_cell.xml"
MM = 0.001


def vec(values):
    return " ".join(f"{v:.6g}" for v in values)


def name(text):
    return re.sub(r"[^a-zA-Z0-9_]+", "_", text).strip("_").lower()


def main():
    robot = ET.parse(URDF).getroot()
    joints = {j.get("name"): j for j in robot.findall("joint")}
    root = ET.Element("mujoco", model="production_cell")
    ET.SubElement(root, "compiler", angle="radian", autolimits="true")
    ET.SubElement(root, "option", timestep="0.002", gravity="0 0 -9.81", integrator="implicitfast")
    ET.SubElement(root, "size", memory="16M")
    ET.SubElement(ET.SubElement(root, "visual"), "global", offwidth="1200", offheight="900")
    world = ET.SubElement(root, "worldbody")
    ET.SubElement(world, "light", pos="0 -0.5 1.5", dir="0 0 -1", diffuse="0.9 0.9 0.9")
    ET.SubElement(world, "camera", name="overview", pos="1.15 -1.35 1.15", xyaxes="0.76 0.65 0 -0.34 0.4 0.85")

    # Each body origin and axis comes from the validated URDF, not from the CSV.
    bodies = {"Static": world}
    body_spec = [
        ("X", "x_joint", world, "x_beam_link"),
        ("Y", "y_joint", "X", "y_carriage_link"),
        ("Z", "a2_joint", "Y", "cup_link"),
        ("Pusher", "a1_joint", world, "pusher_link"),
    ]
    world_pose = {"Static": (0.0, 0.0, 0.0)}
    for group, joint_name, parent, link_name in body_spec:
        joint = joints[joint_name]
        p = bodies[parent] if isinstance(parent, str) else parent
        origin = [float(x) for x in joint.find("origin").get("xyz").split()]
        parent_pose = world_pose[parent] if isinstance(parent, str) else (0.0, 0.0, 0.0)
        world_pose[group] = tuple(a + b for a, b in zip(parent_pose, origin))
        body = ET.SubElement(p, "body", name=link_name, pos=vec(origin))
        bodies[group] = body
        lim = joint.find("limit")
        ET.SubElement(body, "joint", name=joint_name, type="slide",
                      axis=joint.find("axis").get("xyz"),
                      range=f"{lim.get('lower')} {lim.get('upper')}", damping="0.3")
        inertial = robot.find(f"link[@name='{link_name}']/inertial")
        tensor = inertial.find("inertia")
        ET.SubElement(body, "inertial", pos=inertial.find("origin").get("xyz"),
                      mass=inertial.find("mass").get("value"),
                      diaginertia=" ".join(tensor.get(k) for k in ("ixx", "iyy", "izz")))

    contact_names = {
        "base board", "front green belt", "long green belt", "L transfer guide",
        "A1 pusher plate", "vacuum cup",
    }
    colors = {"belt": "0.06 0.45 0.19 1", "bin": "0.82 0.79 0.91 1",
              "PS": "0.95 0.68 0.08 1", "base": "0.22 0.25 0.28 1"}
    used_names = set()
    with PARTS.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            label, group = row["name"], row["group"]
            x, y, z = (float(row[k]) * MM for k in ("x_mm", "y_mm", "z_mm"))
            sx, sy, sz = (float(row[k]) * MM for k in ("sx_mm", "sy_mm", "sz_mm"))
            if row["shape"] == "box":
                pos, size, shape, quat = (x, y, z + sz / 2), (sx / 2, sy / 2, sz / 2), "box", None
            else:
                if row["along_x"] == "1":
                    pos, quat = (x + sz / 2, y, z), "0.70710678 0 0.70710678 0"
                elif row["along_y"] == "1":
                    pos, quat = (x, y + sz / 2, z), "0.70710678 -0.70710678 0 0"
                else:
                    pos, quat = (x, y, z + sz / 2), None
                size, shape = (sx / 2, sz / 2), "cylinder"
            local = tuple(a - b for a, b in zip(pos, world_pose[group]))
            geom_name = name(label)
            if geom_name in used_names:
                geom_name += f"_{len(used_names)}"
            used_names.add(geom_name)
            attrs = {"name": geom_name, "type": shape, "pos": vec(local), "size": vec(size)}
            if quat:
                attrs["quat"] = quat
            if label not in contact_names and not label.startswith("bin ") and not label.startswith(("long conveyor side rail", "front conveyor side rail")):
                attrs.update(contype="0", conaffinity="0")
            if label in ("front green belt", "long green belt"):
                attrs.update(friction="1.4 0.005 0.0001", surfacevel="0 0 0 0 0 0")
            if label == "vacuum cup":
                attrs.update(friction="1.2 0.01 0.0001", adhesion="0", gap="0.003")
            attrs["rgba"] = next((color for key, color in colors.items() if key in label), "0.66 0.7 0.73 1")
            ET.SubElement(bodies[group], "geom", **attrs)

    # A legacy 22 mm test product. It is free: belts, A1 and cup must move it by contact.
    product = ET.SubElement(world, "body", name="product", pos="0.20 -0.325 0.060")
    ET.SubElement(product, "freejoint", name="product_free")
    ET.SubElement(product, "geom", name="product_box", type="box", size="0.011 0.011 0.011",
                  mass="0.02", friction="1.2 0.005 0.0001", rgba="0.72 0.42 0.20 1")

    actuators = ET.SubElement(root, "actuator")
    for joint_name in ("x_joint", "y_joint", "a2_joint", "a1_joint"):
        lim = joints[joint_name].find("limit")
        kp = {"x_joint": "250", "y_joint": "250", "a2_joint": "5000", "a1_joint": "600"}[joint_name]
        ET.SubElement(actuators, "position", name=joint_name + "_target", joint=joint_name,
                      kp=kp, dampratio="1",
                      ctrlrange=f"{lim.get('lower')} {lim.get('upper')}")
    sensors = ET.SubElement(root, "sensor")
    for joint_name in ("x_joint", "y_joint", "a2_joint", "a1_joint"):
        ET.SubElement(sensors, "jointpos", name=joint_name + "_pos", joint=joint_name)
    for sensor_name, y in (("ps1", -0.065), ("ps2", 0.170)):
        site = ET.SubElement(world, "site", name=sensor_name + "_beam",
                             pos=vec((-0.236, y, 0.065)),
                             quat="0.70710678 0 0.70710678 0", size="0.003", rgba="1 0.2 0.1 0.8")
        ET.SubElement(sensors, "rangefinder", name=sensor_name + "_range", site=site.get("name"))
    ET.SubElement(sensors, "framepos", name="product_position", objtype="body", objname="product")
    ET.indent(root, space="  ")
    OUT.write_text('<?xml version="1.0"?>\n' + ET.tostring(root, encoding="unicode") + "\n", encoding="utf-8")
    print(f"Built {OUT} from {URDF.name} and {PARTS.name}")


if __name__ == "__main__":
    main()
