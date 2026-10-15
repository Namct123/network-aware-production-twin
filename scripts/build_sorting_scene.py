"""Build Smart_Sorting_Cell_Phase1 from Factory I/O standard components.

The installed scenes are used only as schema/component templates. The generated
scene is written to the workspace and every object/I/O key is regenerated.
"""

from __future__ import annotations

import copy
import json
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


INSTALL_SCENES = Path(r"C:\Program Files (x86)\Real Games\Factory IO\Scenes")
WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUT_DIR = WORKSPACE / "scenes"
OUTPUT_SCENE = OUTPUT_DIR / "Smart_Sorting_Cell_Phase1.factoryio"
OUTPUT_MANIFEST = OUTPUT_DIR / "Smart_Sorting_Cell_Phase1.mapping.json"
ZERO_GUID = "00000000-0000-0000-0000-000000000000"


def load(name: str) -> ET.ElementTree:
    return ET.parse(INSTALL_SCENES / name)


SOURCE_TREES = {
    "base": load("Separating Station.factoryio"),
    "sorting": load("Sorting Station.factoryio"),
    "basic": load("Sorting by Height (Basic).factoryio"),
}


def template(prefab: str, source: str = "base", occurrence: int = 0) -> ET.Element:
    found = [
        obj
        for obj in SOURCE_TREES[source].getroot().findall("Object")
        if obj.find("Proxy").get("PrefabName") == prefab
    ]
    if occurrence >= len(found):
        raise RuntimeError(f"Missing template {source}:{prefab}[{occurrence}]")
    return copy.deepcopy(found[occurrence])


def set_transform(
    obj: ET.Element,
    *,
    x: float,
    y: float,
    z: float,
    rotation: tuple[float, float, float, float] | None = None,
    forward: tuple[float, float, float] | None = None,
    right: tuple[float, float, float] | None = None,
) -> None:
    proxy = obj.find("Proxy")
    pos = proxy.find("Position")
    pos.attrib.update(X=str(x), Y=str(y), Z=str(z))
    if rotation is not None:
        rot = proxy.find("Rotation")
        rot.attrib.update(
            X=str(rotation[0]),
            Y=str(rotation[1]),
            Z=str(rotation[2]),
            W=str(rotation[3]),
        )
    if forward is not None:
        node = proxy.find("Forward")
        node.attrib.update(X=str(forward[0]), Y=str(forward[1]), Z=str(forward[2]))
    if right is not None:
        node = proxy.find("Right")
        node.attrib.update(X=str(right[0]), Y=str(right[1]), Z=str(right[2]))


def rename_io(
    obj: ET.Element,
    definitions: list[tuple[str, int, bool | None]],
) -> None:
    points = [
        node
        for node in obj.iter()
        if node.tag in {"BinaryInput", "BinaryOutput"}
    ]
    if len(points) != len(definitions):
        prefab = obj.find("Proxy").get("PrefabName")
        raise RuntimeError(f"I/O shape mismatch for {prefab}: {len(points)}")
    for point, (name, address, forced) in zip(points, definitions, strict=True):
        point.set("Name", name)
        point.set("Address", str(address))
        if forced is not None:
            point.set("UseForcedValue", "True")
            point.set("ForcedValue", "True" if forced else "False")


def regenerate_keys(obj: ET.Element) -> None:
    obj.set("GroupKey", ZERO_GUID)
    obj.find("Proxy").set("Key", str(uuid.uuid4()))
    for node in obj.iter():
        if node.tag in {"BinaryInput", "BinaryOutput", "NumericInput", "NumericOutput"}:
            node.set("Key", str(uuid.uuid4()))


def point_inventory(objects: list[ET.Element]) -> tuple[list[ET.Element], list[ET.Element]]:
    inputs: list[ET.Element] = []
    outputs: list[ET.Element] = []
    for obj in objects:
        inputs.extend(obj.iter("BinaryInput"))
        outputs.extend(obj.iter("BinaryOutput"))
    inputs.sort(key=lambda node: int(node.get("Address")))
    outputs.sort(key=lambda node: int(node.get("Address")))
    return inputs, outputs


def rebuild_driver_maps(root: ET.Element, objects: list[ET.Element]) -> None:
    inputs, outputs = point_inventory(objects)
    drivers = root.find("Drivers")
    if drivers is None:
        raise RuntimeError("Template has no Drivers section")

    mapping_prefixes = ("BitInput", "BitOutput", "Float", "Int", "Numeric")
    protected = {"PointIOCount", "PointIOOffset"}
    for driver in list(drivers):
        count = driver.find("PointIOCount")
        if count is None:
            continue
        count.attrib.update(
            BitInputCount=str(len(inputs)),
            BitOutputCount=str(len(outputs)),
            FloatInputCount="0",
            FloatOutputCount="0",
            IntInputCount="0",
            IntOutputCount="0",
            NumericInputCount="0",
            NumericOutputCount="0",
        )
        for child in list(driver):
            if child.tag not in protected and child.tag.startswith(mapping_prefixes):
                driver.remove(child)
        offset = driver.find("PointIOOffset")
        insert_at = list(driver).index(offset) + 1 if offset is not None else 1
        mappings: list[ET.Element] = []
        mappings.extend(
            ET.Element(f"BitInput{index}", PointIOKey=point.get("Key"))
            for index, point in enumerate(inputs)
        )
        mappings.extend(
            ET.Element(f"BitOutput{index}", PointIOKey=point.get("Key"))
            for index, point in enumerate(outputs)
        )
        for mapping in reversed(mappings):
            driver.insert(insert_at, mapping)


def main() -> None:
    tree = copy.deepcopy(SOURCE_TREES["base"])
    root = tree.getroot()
    # Factory I/O only lists user scenes whose root type is MySavedScene.
    root.set("Type", "MySavedScene")
    root.set("Version", "2.5.8")
    root.set("GUID", ZERO_GUID)
    now = datetime.now()
    for key, value in {
        "Year": now.year,
        "Month": now.month,
        "Day": now.day,
        "Hour": now.hour,
        "Minute": now.minute,
        "Second": now.second,
    }.items():
        root.set(key, str(value))
    description = root.find("Description")
    description.set(
        "Data",
        "Smart Sorting Cell Phase 1 - three-product baseline for virtual commissioning",
    )

    for obj in list(root.findall("Object")):
        root.remove(obj)

    objects: list[ET.Element] = []

    def add(obj: ET.Element) -> ET.Element:
        regenerate_keys(obj)
        objects.append(obj)
        return obj

    # Product source: three visually distinct raw materials, moderate spacing.
    emitter = add(template("Emitter"))
    # Keep the drop point just inside the 6 m belt footprint (z=106..166).
    # Placing it beyond z=166 makes emitted parts miss the conveyor.
    set_transform(emitter, x=264, y=9, z=163)
    rename_io(emitter, [("Q_Source_Emit", 0, True)])
    emitter_cfg = emitter.find("Emitter")
    emitter_cfg.set("MinTimeToEmit", "2.5")
    emitter_cfg.set("MaxTimeToEmit", "3.5")
    emitter_cfg.set("RandomPartPosition", "False")
    emitter_cfg.set("RandomPartOrientation", "False")
    parts = emitter_cfg.find("Parts")
    parts.attrib.clear()
    parts.attrib.update(
        RawMaterialBlue="True",
        RawMaterialGreen="True",
        ProductBaseBlue="True",
    )

    conveyor = add(template("BeltConveyor6M"))
    set_transform(conveyor, x=264, y=3, z=136)
    rename_io(conveyor, [("Q_Conveyor_Run", 1, None)])
    conveyor.find("Encoder").set("Enabled", "False")

    # Two monostable pneumatic pushers on the left, discharging to the right.
    pusher1 = add(template("Pusher", occurrence=0))
    set_transform(pusher1, x=257, y=6, z=148)
    rename_io(
        pusher1,
        [
            ("Q_Cyl1_Extend", 2, None),
            ("I_Cyl1_Extended", 6, None),
            ("I_Cyl1_Retracted", 7, None),
        ],
    )
    pusher2 = add(template("Pusher", occurrence=0))
    set_transform(pusher2, x=257, y=6, z=123)
    rename_io(
        pusher2,
        [
            ("Q_Cyl2_Extend", 3, None),
            ("I_Cyl2_Extended", 8, None),
            ("I_Cyl2_Retracted", 9, None),
        ],
    )

    # Passive side chutes and one downstream chute.
    for z in (148, 123):
        chute = add(template("ChuteConveyor", source="sorting"))
        set_transform(
            chute,
            x=276,
            y=4,
            z=z,
            rotation=(0, 0, 0, -1),
            forward=(0, 0, -1),
            right=(-1, 0, 0),
        )
    chute_c = add(template("ChuteConveyor"))
    set_transform(chute_c, x=264, y=4, z=104)

    remover_specs = [
        ("AUX_BinA_Remover", 4, 290, 148, "sorting"),
        ("AUX_BinB_Remover", 5, 290, 123, "sorting"),
        ("AUX_BinC_Remover", 6, 264, 90, "base"),
    ]
    for name, address, x, z, source in remover_specs:
        remover = add(template("Remover", source=source))
        set_transform(remover, x=x, y=1, z=z)
        rename_io(remover, [(name, address, True)])

    # Main-line photoelectric sensor/mirror pairs (beam across conveyor).
    sensor_template = template("RetroreflectivePhotoelectricSensor", source="basic")
    mirror_template = template("RetroreflectiveMirror", source="basic")
    for name, address, z in [
        ("I_S1_Entry", 0, 159),
        ("I_S2_SortA", 1, 151),
        ("I_S3_SortB", 2, 136),
        ("I_BinC_OK", 5, 96),
    ]:
        sensor = add(copy.deepcopy(sensor_template))
        set_transform(sensor, x=268, y=5, z=z)
        rename_io(sensor, [(name, address, None)])
        mirror = add(copy.deepcopy(mirror_template))
        set_transform(mirror, x=260, y=5, z=z)

    # Side-output verification beams across each chute.
    side_sensor_template = template(
        "RetroreflectivePhotoelectricSensor", source="sorting"
    )
    side_mirror_template = template("RetroreflectiveMirror", source="sorting")
    for name, address, x, z_sensor, z_mirror in [
        ("I_BinA_OK", 3, 282, 152, 144),
        ("I_BinB_OK", 4, 282, 127, 119),
    ]:
        sensor = add(copy.deepcopy(side_sensor_template))
        set_transform(sensor, x=x, y=8, z=z_sensor)
        rename_io(sensor, [(name, address, None)])
        mirror = add(copy.deepcopy(side_mirror_template))
        set_transform(mirror, x=x, y=8, z=z_mirror)

    # Standard aligners keep emitted products centered on the main belt.
    aligner2 = add(template("Aligner2", source="sorting"))
    set_transform(aligner2, x=262, y=8, z=157)
    aligner3 = add(template("Aligner3", source="sorting"))
    set_transform(aligner3, x=267, y=8, z=157)

    # Insert objects before Groups/Drivers so the layout matches native files.
    first_non_scene = next(
        (
            index
            for index, child in enumerate(list(root))
            if child.tag not in {"Description", "Camera", "Object"}
        ),
        len(root),
    )
    for obj in objects:
        root.insert(first_non_scene, obj)
        first_non_scene += 1

    rebuild_driver_maps(root, objects)
    ET.indent(tree, space="  ")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tree.write(OUTPUT_SCENE, encoding="utf-8", xml_declaration=False)

    inputs, outputs = point_inventory(objects)
    manifest = {
        "scene": OUTPUT_SCENE.name,
        "architecture": "Main conveyor -> Pusher A / Bin A -> Pusher B / Bin B -> Bin C",
        "products": ["RawMaterialBlue", "RawMaterialGreen", "ProductBaseBlue"],
        "digital_inputs": [
            {"address": int(point.get("Address")), "tag": point.get("Name")}
            for point in inputs
        ],
        "digital_outputs": [
            {
                "address": int(point.get("Address")),
                "tag": point.get("Name"),
                "forced": point.get("UseForcedValue") == "True",
            }
            for point in outputs
        ],
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(OUTPUT_SCENE)
    print(OUTPUT_MANIFEST)


if __name__ == "__main__":
    main()
