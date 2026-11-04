"""Export the legacy Fusion CAD part ledger in millimetres, Z up."""

import csv
import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "cad_reference" / "production_twin_v0_parts.csv"
FUSION = ROOT / "fusion" / "ProductionTwin_V0" / "ProductionTwin_V0.py"
PARTS = []


def group(name):
    if name.startswith(("A2 rod ", "A2 rod end plate", "vacuum cup")):
        return "Z"
    if name.startswith(("pick carriage", "A2 carriage mount", "A2 TN", "S3 ", "S4 ")):
        return "Y"
    if name.startswith(("moving Y rail", "motor Y carriage")):
        return "X"
    if name.startswith(("A1 pusher rod", "A1 pusher plate")):
        return "Pusher"
    return "Static"


def add(name, shape, x, y, z, sx, sy, sz, along_x=False, along_y=False):
    PARTS.append((name, group(name), shape, x, y, z, sx, sy, sz,
                  int(along_x), int(along_y)))


def record_box(_root, name, x, y, z, sx, sy, sz):
    add(name, "box", x, y, z, sx, sy, sz)


def record_cylinder(_root, name, x, y, z, diameter, length,
                    along_x=False, along_y=False):
    add(name, "cylinder", x, y, z, diameter, diameter, length,
        along_x, along_y)


def record_bin(_root, name, x, y):
    size, height, wall, base = 104, 78, 4, 12
    record_box(None, name + " floor", x, y, base, size, size, wall)
    for side in (-1, 1):
        record_box(None, name + " side wall " + str(side),
                   x + side * 50, y, base, wall, size, height)
        record_box(None, name + " end wall " + str(side),
                   x, y + side * 50, base, size - 2 * wall, wall, height)


def load_layout():
    # The geometry calls in Fusion are the sole source of part names and sizes.
    for name in ("adsk", "adsk.core", "adsk.fusion"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["adsk"].core = sys.modules["adsk.core"]
    sys.modules["adsk"].fusion = sys.modules["adsk.fusion"]
    spec = importlib.util.spec_from_file_location("production_twin_fusion", FUSION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._box = record_box
    module._cylinder = record_cylinder
    module._open_bin = record_bin
    module.build(None)


def validate_transfer():
    part = {row[0]: row for row in PARTS}
    front = part["front green belt"]
    long = part["long green belt"]
    body = part["A1 front pusher cylinder"]
    rod = part["A1 pusher rod"]
    plate = part["A1 pusher plate"]
    stroke = 110  # provisional, not a measured cylinder rating
    plate_left, plate_right = plate[3] - plate[6] / 2, plate[3] + plate[6] / 2
    assert plate[3] == long[3], "A1 must align with long-belt centerline"
    assert plate[5] == front[5] + front[8], "Plate must sit above belt surface"
    assert plate[4] + plate[7] / 2 < front[4] - front[7] / 2
    assert plate[4] + stroke + plate[7] / 2 >= long[4] - long[7] / 2
    assert rod[4] - rod[7] / 2 + stroke == body[4] + body[7] / 2
    for row in PARTS:
        if row[0].startswith("front conveyor side rail"):
            assert row[3] + row[6] / 2 <= plate_left or row[3] - row[6] / 2 >= plate_right, row[0]
    a2 = part["A2 TN10X75-S twin rod body"]
    mount = part["A2 carriage mount"]
    carriage = part["pick carriage"]
    assert a2[5] + a2[8] == mount[5]
    assert mount[5] + mount[8] == carriage[5]
    station = part["button station envelope"]
    motor = part["front conveyor DC motor"]
    assert station[4] - station[7] / 2 > motor[4] + motor[7] / 2
    assert [part["button " + label][4] for label in
            ("EStop", "Reset", "Stop", "Start")] == [-135, -178, -221, -264]
    ps1 = part["PS1 optical face"]
    ps2 = part["PS2 optical face"]
    belt_left = long[3] - long[6] / 2
    for ps in (ps1, ps2):
        assert ps[3] < belt_left and ps[9] == 1 and ps[10] == 0
        assert long[4] - long[7] / 2 < ps[4] < long[4] + long[7] / 2
        assert long[5] + long[8] < ps[5] < long[5] + long[8] + 22
    assert ps1[4] < ps2[4] and (ps1[4], ps2[4]) == (-65, 170)
    for tag in ("PS1", "PS2"):
        foot = part[tag + " bracket foot"]
        chassis = part["long conveyor chassis"]
        assert foot[3] + foot[6] / 2 >= chassis[3] - chassis[6] / 2
    assert part["motor Y carriage"][1] == "X"
    assert all(part[name][1] == "Static" for name in
               ("motor X rear", "motor X front"))
    for x, y in ((-180, 120), (80, 75), (195, 305)):
        assert -315 <= x - 12.5 and x + 12.5 <= 315
        assert -0.5 <= y - 34 and y + 34 <= 434.5


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    target=parser.parse_args().output
    load_layout(); validate_transfer()
    names=[part[0] for part in PARTS]
    assert len(names)==len(set(names)) and len(PARTS)>100
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(('name','group','shape','x_mm','y_mm','z_mm','sx_mm','sy_mm','sz_mm','along_x','along_y'))
        writer.writerows(PARTS)
    print('Exported',len(PARTS),'CAD parts to',target)


if __name__=='__main__':main()
