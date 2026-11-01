"""Apply a resolved profile to a private MJCF copy, leaving CAD/URDF sources intact."""

from pathlib import Path
import xml.etree.ElementTree as ET
from config import validate_config


def vec(values):
    return " ".join(format(float(x), ".12g") for x in values)


def model_xml(config, template=None):
    validate_config(config)
    template = Path(template or Path(__file__).resolve().parent/"production_cell.xml")
    tree = ET.parse(template)
    root = tree.getroot()
    g, p = config["geometry"], config["plant"]
    root.find("option").set("timestep", str(config["timing"]["physics_step_s"]))
    for joint, limits in g["joint_limits_m"].items():
        root.find(f".//joint[@name='{joint}']").set("range", vec(limits))
        root.find(f".//joint[@name='{joint}']").set("damping", str(p["joint_damping"]))
        actuator = root.find(f"actuator/position[@joint='{joint}']")
        actuator.set("ctrlrange", vec(limits))
        actuator.set("kp", str(p["position_kp"][joint]))
        actuator.set("dampratio", str(p["dampratio"]))
    xbody = root.find(".//body[@name='x_beam_link']")
    xpos = list(map(float, xbody.get("pos").split()))
    xpos[0] = g["robot_origin_xy_m"][0]
    xbody.set("pos", vec(xpos))
    ybody = root.find(".//body[@name='y_carriage_link']")
    ypos = list(map(float, ybody.get("pos").split()))
    ypos[1] = g["robot_origin_xy_m"][1]-xpos[1]
    ybody.set("pos", vec(ypos))
    for body, values in p["link_inertials"].items():
        inertial = root.find(f".//body[@name='{body}']/inertial")
        inertial.set("mass", str(values["mass_kg"]))
        inertial.set("pos", vec(values["com_m"]))
        inertial.set("diaginertia", vec(values["diagonal_kg_m2"]))
    root.find(".//body[@name='product']").set("pos", vec(g["product_initial_xyz_m"]))
    product = root.find(".//geom[@name='product_box']")
    product.set("size", vec(v/2 for v in g["product_size_m"]))
    product.set("mass", str(p["product_mass_kg"]))
    product.set("friction", vec(p["product_friction"]))
    for key in ("front_green_belt", "long_green_belt"):
        root.find(f".//geom[@name='{key}']").set("friction", vec(p["belt_friction"]))
    root.find(".//geom[@name='vacuum_cup']").set("friction", vec(p["cup_friction"]))
    belt = root.find(".//geom[@name='long_green_belt']")
    pos, size = (list(map(float, belt.get(k).split())) for k in ("pos", "size"))
    pos[0], pos[1] = g["lane_x_m"], sum(g["long_belt_y_m"])/2
    size[1] = (g["long_belt_y_m"][1]-g["long_belt_y_m"][0])/2
    belt.set("pos", vec(pos)); belt.set("size", vec(size))
    front = root.find(".//geom[@name='front_green_belt']")
    pos, size = (list(map(float, front.get(k).split())) for k in ("pos", "size"))
    for axis, bounds in enumerate(g["front_belt_xy_m"]):
        pos[axis], size[axis] = sum(bounds)/2, (bounds[1]-bounds[0])/2
    front.set("pos", vec(pos)); front.set("size", vec(size))
    for key, y in g["ps_y_m"].items():
        site = root.find(f".//site[@name='{key}_beam']")
        old = list(map(float, site.get("pos").split()))
        new = [g["optical_xz_m"][0], y, g["optical_xz_m"][1]]
        site.set("pos", vec(new))
        for geom in root.findall("worldbody/geom"):
            if geom.get("name", "").startswith(key+"_"):
                oldpos = list(map(float, geom.get("pos").split()))
                geom.set("pos", vec(a+b-c for a,b,c in zip(oldpos,new,old)))
    for i, center in enumerate(g["bin_centers_xy_m"]):
        prefix = f"bin_r{i//2+1}c{i%2+1}_"
        floor = root.find(f".//geom[@name='{prefix}floor']")
        original = list(map(float, floor.get("pos").split()))
        inner_x, inner_y = g["bin_inner_size_xy_m"]
        for geom in root.findall("worldbody/geom"):
            if not geom.get("name", "").startswith(prefix):
                continue
            name = geom.get("name")
            pos, size = (list(map(float, geom.get(k).split())) for k in ("pos", "size"))
            offset_x, offset_y = pos[0]-original[0], pos[1]-original[1]
            pos[0], pos[1] = center
            if "side_wall" in name:
                pos[0] += (1 if offset_x > 0 else -1)*(inner_x/2+size[0])
                size[1] = inner_y/2+2*size[0]
            elif "end_wall" in name:
                pos[1] += (1 if offset_y > 0 else -1)*(inner_y/2+size[1])
                size[0] = inner_x/2
            else:
                size[0], size[1] = inner_x/2+.004, inner_y/2+.004
            geom.set("pos", vec(pos)); geom.set("size", vec(size))
    # ponytail: the adapter moves operational points, not a complete parametric CAD
    # redesign. Rebuild the source CAD/URDF for changed frame topology or rail layout.
    ET.indent(root, space="  ")
    return '<?xml version="1.0"?>\n'+ET.tostring(root, encoding="unicode")+"\n"


def write_model(config, destination, template=None):
    Path(destination).write_text(model_xml(config, template), encoding="utf-8")
    return Path(destination)
