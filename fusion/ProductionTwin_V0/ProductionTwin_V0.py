"""Estimated CAD layout for the PLC sorting demonstrator.

Run from Fusion's Scripts and Add-Ins dialog. Dimensions below are preliminary
millimetres because the reference video contains no dimension callouts.
"""

import os
import math
import traceback

import adsk.core
import adsk.fusion


OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output", "cad"))

# All dimensions are provisional and can be calibrated from measurements.
BASE_X, BASE_Y, BASE_Z = 760, 1000, 12
FRAME_TOP_Z = 300
CONVEYOR_Z = 45
_APPEARANCES = {}

# Visual materials for the digital twin; actual grades are not identified.
_PALETTE = {
    "board": (49, 53, 57),
    "aluminum": (181, 188, 194),
    "steel": (125, 136, 146),
    "rubber_green": (24, 125, 65),
    "plastic_lilac": (222, 213, 232),
    "plastic_yellow": (239, 183, 43),
    "plastic_white": (227, 228, 223),
    "dark_housing": (55, 64, 74),
    "red": (204, 54, 52),
    "yellow": (232, 171, 31),
    "green": (39, 174, 81),
    "blue": (41, 111, 194),
    "black": (36, 39, 43),
}


def _material_key(name):
    tag = name.lower()
    if "green belt" in tag:
        return "rubber_green"
    if tag.startswith("bin "):
        return "plastic_lilac"
    if tag == "base board":
        return "board"
    if tag == "button start":
        return "green"
    if tag == "button reset":
        return "yellow"
    if tag in ("button estop", "button stop"):
        return "red"
    if tag.startswith("button station"):
        return "plastic_white"
    if tag.startswith("ps"):
        return "black" if "optical face" in tag else "plastic_yellow"
    if tag.startswith("plc") or tag.startswith("motor "):
        return "dark_housing"
    if "vacuum cup" in tag:
        return "black"
    if "coil" in tag or "spring cap" in tag:
        return "black"
    if "collet" in tag or "manual button" in tag:
        return "blue"
    if "rod" in tag or "roller" in tag:
        return "steel"
    return "aluminum"


def _make_appearances(app, design):
    # Autodesk's native generic opaque appearance is copied into this document.
    lib = app.materialLibraries.itemById("BA5EE55E-9982-449B-9D66-9F036540E140")
    if not lib:
        raise RuntimeError("Fusion native appearance library is unavailable")
    source = lib.appearances.itemById("Prism-129")
    if not source:
        raise RuntimeError("Fusion generic opaque appearance is unavailable")
    for key, rgb in _PALETTE.items():
        appearance = design.appearances.addByCopy(source, "Twin " + key)
        if not appearance:
            raise RuntimeError("Cannot create Fusion appearance: " + key)
        prop = adsk.core.ColorProperty.cast(
            appearance.appearanceProperties.itemById("opaque_albedo"))
        if not prop:
            raise RuntimeError("Appearance has no opaque_albedo: " + key)
        prop.value = adsk.core.Color.create(*rgb, 255)
        _APPEARANCES[key] = appearance


def _solid(comp, name, x, y, sx, sy, sz):
    """Extrude a local rectangle. Fusion uses centimetres internally."""
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.name = name + " footprint"
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create((x - sx / 2) / 10, (y - sy / 2) / 10, 0),
        adsk.core.Point3D.create((x + sx / 2) / 10, (y + sy / 2) / 10, 0),
    )
    feature = comp.features.extrudeFeatures.addSimple(
        sketch.profiles.item(0),
        adsk.core.ValueInput.createByReal(sz / 10),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    body = feature.bodies.item(0)
    body.name = name
    if _APPEARANCES:
        body.appearance = _APPEARANCES[_material_key(name)]
    sketch.isVisible = False


def _box(root, name, x, y, z, sx, sy, sz):
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(x / 10, y / 10, z / 10)
    comp = root.occurrences.addNewComponent(m).component
    comp.name = name
    _solid(comp, name, 0, 0, sx, sy, sz)
    return comp


def _cylinder(root, name, x, y, z, diameter, length,
              along_x=False, along_y=False):
    m = adsk.core.Matrix3D.create()
    if along_x:
        m.setToRotation(math.pi / 2, adsk.core.Vector3D.create(0, 1, 0),
                        adsk.core.Point3D.create(0, 0, 0))
    elif along_y:
        m.setToRotation(-math.pi / 2, adsk.core.Vector3D.create(1, 0, 0),
                        adsk.core.Point3D.create(0, 0, 0))
    m.translation = adsk.core.Vector3D.create(x / 10, y / 10, z / 10)
    comp = root.occurrences.addNewComponent(m).component
    comp.name = name
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(0, 0, 0), diameter / 20)
    feature = comp.features.extrudeFeatures.addSimple(
        sketch.profiles.item(0), adsk.core.ValueInput.createByReal(length / 10),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = feature.bodies.item(0)
    body.name = name
    if _APPEARANCES:
        body.appearance = _APPEARANCES[_material_key(name)]
    sketch.isVisible = False
    return comp


def _photo_sensor(root, tag, x, y):
    # Both E3F-DS30C4 sensors sit to the left of the long conveyor, facing +X.
    # The foot reaches the conveyor underside; dimensions remain photo estimates.
    _box(root, tag + " bracket foot", x + 56, y, 22, 35, 24, 4)
    _box(root, tag + " bracket upright", x + 60, y, 26, 5, 24, 56)
    _cylinder(root, tag + " YF-KJ E3F-DS30C4 M18 body",
              x, y, 65, 18, 58, along_x=True)
    _cylinder(root, tag + " locking ring", x + 58, y, 65, 24, 8,
              along_x=True)
    _cylinder(root, tag + " optical face", x + 66, y, 65, 18, 3,
              along_x=True)


def _valve(root, tag, y):
    # EAGLE-A 4V210-08 5/2 single-coil; block sizes follow the visible envelope.
    x = 0
    _box(root, tag + " 4V210-08 manifold", x, y, BASE_Z, 130, 33, 16)
    _box(root, tag + " 4V210-08 aluminum body", x - 22, y, 28, 67, 22, 24)
    _box(root, tag + " spring cap", x - 64, y, 28, 17, 22, 24)
    _box(root, tag + " pilot and manual override", x + 23, y, 28, 23, 22, 24)
    _box(root, tag + " DC24V 4.8W 200mA coil", x + 55, y, 28, 40, 24, 28)
    _box(root, tag + " DIN plug", x + 55, y, 56, 32, 24, 18)
    _cylinder(root, tag + " manual button", x + 23, y, 52, 7, 6)
    for label, offset in (("A", -43), ("B", -4)):
        _cylinder(root, tag + " port " + label + " fitting", x + offset,
                  y, 52, 13, 11)
        _cylinder(root, tag + " port " + label + " collet", x + offset,
                  y, 63, 8, 3)


def _open_bin(root, name, x, y):
    size, height, wall = 104, 78, 4
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(x / 10, y / 10, BASE_Z / 10)
    comp = root.occurrences.addNewComponent(m).component
    comp.name = name
    _solid(comp, name + " floor", 0, 0, size, size, wall)
    for side in (-1, 1):
        _solid(comp, name + " side wall " + str(side),
               side * (size - wall) / 2, 0, wall, size, height)
        _solid(comp, name + " end wall " + str(side),
               0, side * (size - wall) / 2, size - 2 * wall, wall, height)
    return comp


def build(root):
    _box(root, "base board", 0, 0, 0, BASE_X, BASE_Y, BASE_Z)

    # Front X conveyor feeds toward -X; A1 pushes +Y onto the long conveyor.
    _box(root, "long conveyor chassis", -180, -20, 26, 100, 510, 19)
    _box(root, "long green belt", -180, -20, CONVEYOR_Z, 78, 490, 4)
    _box(root, "front conveyor chassis", -40, -325, 26, 610, 95, 19)
    _box(root, "front green belt", -40, -325, CONVEYOR_Z, 590, 73, 4)
    for edge in (-1, 1):
        _box(root, "long conveyor side rail {}".format(edge),
             -180 + edge * 47, -20, 31, 6, 510, 20)
        # Leave the A1 transfer aperture open through both front-belt rails.
        _box(root, "front conveyor side rail {} left".format(edge),
             -287.5, -325 + edge * 44, 31, 115, 6, 20)
        _box(root, "front conveyor side rail {} right".format(edge),
             67.5, -325 + edge * 44, 31, 395, 6, 20)
    for x in (-330, 250):
        _cylinder(root, "front conveyor roller {}".format(x),
                  x, -362, 29, 24, 75, along_y=True)
    for y in (-265, 225):
        _cylinder(root, "long conveyor roller {}".format(y),
                  -219, y, 29, 24, 78, along_x=True)
    _box(root, "front conveyor DC motor", 285, -325, 24, 56, 36, 36)
    _box(root, "long conveyor DC motor", -180, 259, 24, 40, 56, 36)
    _box(root, "L transfer guide", -180, -282, 45, 88, 56, 4)

    # 20 mm profiles are a scale assumption, not a measured specification.
    for x_name, x in (("left", -305), ("right", 305)):
        for y_name, y in (("front", 10), ("rear", 425)):
            _box(root, "gantry post " + x_name + " " + y_name,
                 x, y, BASE_Z, 20, 20, FRAME_TOP_Z - BASE_Z)

    for y_name, y in (("front", 10), ("rear", 425)):
        _box(root, "gantry X rail " + y_name, 0, y, FRAME_TOP_Z,
             630, 20, 20)
    _box(root, "right Y guide", 305, 217, FRAME_TOP_Z + 20, 20, 435, 20)
    _box(root, "moving Y rail", -180, 217, FRAME_TOP_Z + 20, 25, 435, 25)
    _box(root, "pick carriage", -180, 120, FRAME_TOP_Z + 45, 62, 68, 30)
    _box(root, "moving Y rail lower guide", -180, 217,
         FRAME_TOP_Z + 5, 25, 435, 12)
    _box(root, "A2 carriage mount", -180, 120, 290, 45, 32, 55)
    _box(root, "A2 TN10X75-S twin rod body", -180, 120, 175, 45, 32, 115)
    for x in (-191, -169):
        _cylinder(root, "A2 rod at x {}".format(x), x, 120, 151, 8, 99)
    _box(root, "A2 rod end plate", -180, 120, 143, 44, 30, 8)
    _cylinder(root, "vacuum cup", -180, 120, 127, 22, 16)
    _cylinder(root, "vacuum cup stem", -180, 120, 151, 8, 16)
    _box(root, "S3 A2 upper proximity switch (code pending)",
         -207, 120, 255, 8, 22, 13)
    _box(root, "S4 A2 lower proximity switch (code pending)",
         -207, 120, 185, 8, 22, 13)
    for name, x, y in (("motor Y carriage", -180, 435),
                       ("motor X rear", 330, 425),
                       ("motor X front", 330, 10)):
        _box(root, name, x, y, FRAME_TOP_Z + 20, 45, 45, 46)

    for row, y in enumerate((75, 190, 305), start=1):
        for col, x in enumerate((80, 195), start=1):
            _open_bin(root, "bin R{}C{}".format(row, col), x, y)

    # +Y is the travel direction on the long conveyor. PS1 confirms transfer;
    # PS2 marks the pick position. The overview photo shows both on its left.
    _photo_sensor(root, "PS1", -302, -65)
    _photo_sensor(root, "PS2", -302, 170)
    # At home the plate is just outside the front belt. A 110 mm estimated
    # extension reaches the long-belt inlet while the rod remains in its body.
    _box(root, "A1 front pusher cylinder", -180, -435, 20, 36, 120, 42)
    _box(root, "A1 pusher rod", -180, -431, 55, 9, 108, 9)
    _box(root, "A1 pusher plate", -180, -377, 49, 70, 6, 30)
    _box(root, "S1 A1 retracted switch (code pending)",
         -206, -480, 37, 9, 16, 11)
    _box(root, "S2 A1 extended switch (code pending)",
         -206, -390, 37, 9, 16, 11)
    _valve(root, "Y1", -455)
    _valve(root, "Y2", -415)
    _box(root, "PLC 1214C envelope", 320, 190, BASE_Z, 90, 155, 85)
    _box(root, "button station envelope", 320, -200, BASE_Z, 75, 180, 35)
    for label, y, diameter in (("EStop", -135, 29),
                                ("Reset", -178, 20),
                                ("Stop", -221, 20),
                                ("Start", -264, 20)):
        _cylinder(root, "button " + label, 320, y, 48, diameter, 10)


def _check_xy_travel(app, root):
    """Pose the gantry in Fusion and record provisional rail clearances."""
    x_home, y_home = -180, 120
    rail_x_min, rail_x_max = -315, 315
    rail_y_min, rail_y_max = -0.5, 434.5
    beam_half_width, carriage_half_length = 12.5, 34
    targets = ((x_home, y_home), (80, 75), (195, 305))
    report = ["XY gantry travel check (mm; photo-estimated geometry)"]
    for x, y in targets:
        clear_x = min(x - beam_half_width - rail_x_min,
                      rail_x_max - x - beam_half_width)
        clear_y = min(y - carriage_half_length - rail_y_min,
                      rail_y_max - y - carriage_half_length)
        if min(clear_x, clear_y) < 0:
            raise ValueError("XY target leaves modeled rails: {}, {}".format(x, y))
        report.append("XY ({}, {}): X end clearance {:.1f}; Y end clearance {:.1f}".format(
            x, y, clear_x, clear_y))

    initial = []
    for occ in root.occurrences:
        name = occ.component.name
        x_group = name.startswith(("moving Y rail", "motor Y carriage"))
        y_group = name.startswith(("pick carriage", "A2 carriage mount", "A2 TN",
                                   "S3 ", "S4 ", "A2 rod ", "A2 rod end plate",
                                   "vacuum cup"))
        if x_group or y_group:
            initial.append((occ, occ.transform2.copy(), y_group))

    def pose(x, y):
        for occ, original, y_group in initial:
            matrix = original.copy()
            translation = matrix.translation
            matrix.translation = adsk.core.Vector3D.create(
                translation.x + (x - x_home) / 10,
                translation.y + ((y - y_home) / 10 if y_group else 0),
                translation.z)
            occ.transform2 = matrix
        adsk.doEvents()

    try:
        pose(195, 305)
        app.activeViewport.fit()
        adsk.doEvents()
        path = os.path.join(OUT, "production_twin_v4_xy_far.png")
        if not app.activeViewport.saveAsImageFile(path, 0, 0):
            raise RuntimeError("Fusion XY snapshot failed: " + path)
    finally:
        pose(x_home, y_home)
    with open(os.path.join(OUT, "xy_travel_v4.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")



def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        _APPEARANCES.clear()
        _make_appearances(app, design)
        build(root)

        os.makedirs(OUT, exist_ok=True)
        exporter = design.exportManager
        outputs = (
            ("production_twin_v4.f3d", exporter.createFusionArchiveExportOptions),
            ("production_twin_v4.step", exporter.createSTEPExportOptions),
        )
        for filename, factory in outputs:
            path = os.path.join(OUT, filename)
            if not exporter.execute(factory(path)):
                raise RuntimeError("Fusion export failed: " + path)
        mesh_dir = os.path.join(OUT, "obj_v4")
        os.makedirs(mesh_dir, exist_ok=True)
        mesh_options = exporter.createOBJExportOptions(
            root, os.path.join(mesh_dir, "part.obj"))
        mesh_options.isOneFilePerBody = True
        if not exporter.execute(mesh_options):
            raise RuntimeError("Fusion OBJ export failed")
        app.activeViewport.fit()
        adsk.doEvents()
        image_path = os.path.join(OUT, "production_twin_v4.png")
        if not app.activeViewport.saveAsImageFile(image_path, 0, 0):
            raise RuntimeError("Fusion snapshot failed: " + image_path)
        _check_xy_travel(app, root)
        ui.messageBox("Production twin V4 created. Exports: " + OUT)
    except Exception:
        detail = traceback.format_exc()
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "fusion_error.txt"), "w", encoding="utf-8") as f:
            f.write(detail)
        if ui:
            ui.messageBox(detail)
