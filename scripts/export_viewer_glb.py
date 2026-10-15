"""Make the colored CAD Viewer mesh from the Unity/Fusion part list.

Run with the Python 3.14 installation that already has trimesh.
"""

import argparse
import csv
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "unity/Assets/ProductionTwin/parts.csv"
OUT = ROOT / "output/cad"


def color(name):
    tag = name.lower()
    if "green belt" in tag:
        return [24, 125, 65, 255]
    if tag.startswith("bin "):
        return [222, 213, 232, 255]
    if tag == "base board":
        return [49, 53, 57, 255]
    if tag.startswith("ps"):
        return [36, 39, 43, 255] if "optical face" in tag else [239, 183, 43, 255]
    if tag.startswith("button station"):
        return [227, 228, 223, 255]
    if "rail" in tag or "post" in tag:
        return [181, 188, 194, 255]
    if tag.startswith("plc") or tag.startswith("motor "):
        return [55, 64, 74, 255]
    if tag in ("button estop", "button stop"):
        return [204, 54, 52, 255]
    if tag == "button start":
        return [39, 174, 81, 255]
    if tag == "button reset":
        return [232, 171, 31, 255]
    if "vacuum cup" in tag or "coil" in tag or "spring cap" in tag:
        return [36, 39, 43, 255]
    if "collet" in tag or "manual button" in tag:
        return [41, 111, 194, 255]
    if "rod" in tag or "roller" in tag:
        return [125, 136, 146, 255]
    return [181, 188, 194, 255]


def metallic(name):
    tag = name.lower()
    return 0.65 if ("rail" in tag or "post" in tag or "rod" in tag or
                    "roller" in tag or "chassis" in tag or "aluminum" in tag or
                    "manifold" in tag) else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--a1-extended", action="store_true")
    args = parser.parse_args()
    scene = trimesh.Scene()
    rows = list(csv.DictReader(PARTS.open(encoding="utf-8")))
    for row in rows:
        name = row["name"]
        x, y, z = (float(row[k]) / 1000 for k in ("x_mm", "y_mm", "z_mm"))
        if args.a1_extended and row["group"] == "Pusher":
            y += 0.110
        sx, sy, sz = (float(row[k]) / 1000 for k in ("sx_mm", "sy_mm", "sz_mm"))
        if row["shape"] == "box":
            mesh = trimesh.creation.box(extents=(sx, sz, sy))
            center = (x, z + sz / 2, y)
        else:
            mesh = trimesh.creation.cylinder(radius=sx / 2, height=sz, sections=24)
            if row["along_x"] == "1":
                axis, center = (1, 0, 0), (x + sz / 2, z, y)
            elif row["along_y"] == "1":
                axis, center = (0, 0, 1), (x, z, y + sz / 2)
            else:
                axis, center = (0, 1, 0), (x, z + sz / 2, y)
            mesh.apply_transform(trimesh.geometry.align_vectors((0, 0, 1), axis))
        mesh.apply_translation(center)
        mesh.visual = trimesh.visual.TextureVisuals(material=
            trimesh.visual.material.PBRMaterial(
                baseColorFactor=color(name), metallicFactor=metallic(name),
                roughnessFactor=0.72 if metallic(name) else 0.9,
                doubleSided=True))
        scene.add_geometry(mesh, geom_name=name, node_name=name)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / ("production_twin_v4_a1_extended.glb" if args.a1_extended
                  else "production_twin_v4_viewer.glb")
    path.write_bytes(trimesh.exchange.gltf.export_glb(scene, include_normals=True))
    check = trimesh.load(path, force="scene")
    assert len(check.geometry) == len(rows) and len(rows) >= 100
    print(len(rows), "parts ->", path)


if __name__ == "__main__":
    main()
