"""Import measured SI scalar values, preserving provenance and unmeasured defaults."""

import argparse
import csv
from datetime import date
import hashlib
import json
from pathlib import Path
from config import JOINTS, load_config, number, resolved_config, validate_config

FIELDS = ("path", "value", "unit", "uncertainty", "measured_on", "method", "operator", "notes")
UNITS = {"plant.product_mass_kg":"kg", "plant.vacuum_adhesion_n":"N"}
for key in ("stop_coast_m", "anchor_tolerance_m", "pick_uncertainty_limit_m"):
    UNITS["estimator."+key] = "m"
UNITS["estimator.drift_m_s"] = "m/s"
for key in ("end_switch_tolerance_m", "optical_detection_range_m"):
    UNITS["sensors."+key] = "m"
for key in ("a2_pick_m", "feed_distance_m"):
    UNITS["motion."+key] = "m"
for key in ("feed_startup_s", "axis_settle_s", "a2_settle_s", "grip_wait_s", "release_wait_s"):
    UNITS["motion."+key] = "s"
for key in ("front_speed_m_s", "long_speed_m_s"):
    UNITS["motion."+key] = "m/s"
for key in ("max_age_s", "max_sample_gap_s", "silence_timeout_s", "cylinder_timeout_s",
            "track_timeout_max_s", "hold_settle_s"):
    UNITS["timing."+key] = "s"
for axis in JOINTS:
    UNITS["motion.rates_m_s."+axis] = "m/s"
    for i in range(2):
        UNITS[f"geometry.joint_limits_m.{axis}.{i}"] = "m"
for key, size in (("robot_origin_xy_m",2), ("product_size_m",3), ("optical_xz_m",2),
                  ("product_initial_xyz_m",3), ("bin_inner_size_xy_m",2)):
    for i in range(size):
        UNITS[f"geometry.{key}.{i}"] = "m"
for sensor in ("ps1", "ps2"):
    UNITS["geometry.ps_y_m."+sensor] = "m"
UNITS["geometry.lane_x_m"] = "m"
for i in range(6):
    for j in range(2):
        UNITS[f"geometry.bin_centers_xy_m.{i}.{j}"] = "m"
for body in ("x_beam_link", "y_carriage_link", "cup_link", "pusher_link"):
    UNITS[f"plant.link_inertials.{body}.mass_kg"] = "kg"
    for i in range(3):
        UNITS[f"plant.link_inertials.{body}.com_m.{i}"] = "m"
        UNITS[f"plant.link_inertials.{body}.diagonal_kg_m2.{i}"] = "kg*m^2"


def set_value(config, path, value):
    target = config
    keys = path.split(".")
    for key in keys[:-1]:
        target = target[int(key)] if isinstance(target,list) else target[key]
    if isinstance(target,list):
        target[int(keys[-1])] = value
    else:
        target[keys[-1]] = value


def value_at(config, path):
    value=config
    for key in path.split('.'):
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value


def parameter_units(config):
    """Enumerate supported numeric leaves; no hidden writable paths or guessed units."""
    result={}
    def walk(value,path):
        if isinstance(value,dict):
            for key,item in value.items(): walk(item,path+[key])
        elif isinstance(value,list):
            for i,item in enumerate(value): walk(item,path+[str(i)])
        elif type(value) in (int,float):
            name='.'.join(path)
            if name in UNITS:
                unit=UNITS[name]
            elif path[:2] == ['plant','position_kp']:
                unit='N/m'
            elif name == 'plant.joint_damping':
                unit='N*s/m'
            elif path[0]=='plant' and path[1].endswith('_friction'):
                unit='1' if path[-1]=='0' else 'm'
            elif name in {'schema_version','plant.dampratio','network.seed','network.drop_probability',
                          'timing.sample_steps','mechanics.cup_contact_dimension','reconfiguration.warning_ticks','recovery.fresh_samples',
                          'prediction.native_threads','prediction.background.max_lag_sequences'} or path[:2] in (
                          ['plant','belt_speed_scale'],['prediction','position_offsets']):
                unit='1'
            elif path[:2]==['estimator','command_gain_range']:
                unit='1'
            else:
                unit=None
                for key in reversed(path):
                    for suffix, candidate in (('_kg_m2','kg*m^2'),('_m_s2','m/s^2'),('_m_s','m/s'),
                                               ('_kg','kg'),('_n','N'),('_s','s'),('_m','m')):
                        if key.endswith(suffix): unit=candidate; break
                    if unit: break
                if not unit: raise ValueError('Parameter unit not declared: '+name)
            if name!='schema_version': result[name]=unit
    for key,value in config.items():
        if key not in {'profile','schema_version'}: walk(value,[key])
    return result


def parameter_report(config):
    records={r['path']:r for r in config['profile']['measurements']
             if isinstance(r,dict) and 'path' in r}
    rows=[]
    for path,unit in parameter_units(config).items():
        value=value_at(config,path); record=records.get(path)
        state=('recorded_partial_measurement' if value==record.get('value') else 'changed_since_measurement') if record else 'provisional_or_design'
        if state=='recorded_partial_measurement' and record.get('method','').startswith('derived'):
            state='derived_from_reported_dimensions'
        active=not ('mechanics' in config and path in {'motion.feed_distance_m','motion.feed_startup_s'})
        rows.append({'path':path,'value':value,'unit':unit,'status':state,'active_in_this_model':active,
                     'uncertainty':record.get('uncertainty') if record and state in {'recorded_partial_measurement','derived_from_reported_dimensions'} else None,
                     'measured_on':record.get('measured_on') if record else None,
                     'method':record.get('method') if record else None})
    return rows


def export_template(config, destination):
    rows=parameter_report(config)
    with Path(destination).open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS); writer.writeheader()
        for r in rows:
            writer.writerow({'path':r['path'],'value':'','unit':r['unit'],'uncertainty':'',
                             'measured_on':'','method':'','operator':'',
                             'notes':f"Current={r['value']}; status={r['status']}. Blank means no new measurement, not zero."})
    return rows


def import_measurements(base, csv_path, output, name=None):
    c = resolved_config(base)
    units=parameter_units(c)
    records = []
    seen = set()
    digest = hashlib.sha256(Path(csv_path).read_bytes()).hexdigest()
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or set(reader.fieldnames) != set(FIELDS) or len(reader.fieldnames) != len(FIELDS):
            raise ValueError("measurement CSV requires exactly: "+",".join(FIELDS))
        for line, row in enumerate(reader,2):
            if set(row) != set(FIELDS) or any(v is None for v in row.values()):
                raise ValueError(f"CSV line {line}: missing/extra columns")
            row = {k:v.strip() for k,v in row.items()}
            if not row["value"]:
                continue  # Unmeasured is not zero.
            path = row["path"]
            if path not in units or row["unit"] != units[path] or path in seen:
                raise ValueError(f"CSV line {line}: unknown/duplicate parameter or wrong SI unit: {path}")
            value = number(float(row["value"]),path)
            if type(value_at(c,path)) is int and value.is_integer():
                value=int(value)
            uncertainty = number(float(row["uncertainty"]),path+".uncertainty",0) if row["uncertainty"] else None
            date.fromisoformat(row["measured_on"])
            if not row["method"]:
                raise ValueError(f"CSV line {line}: measurement method is required")
            set_value(c,path,value)
            records.append({**row,"value":value,"uncertainty":uncertainty,
                            "source_csv_sha256":digest,"source_csv_line":line})
            seen.add(path)
    if not records:
        raise ValueError("No measured values entered; blank rows do not create a calibrated profile")
    c["profile"]["name"] = name or c["profile"]["name"]+"_partial"
    c["profile"]["status"] = "partial"
    c["profile"]["measurements"].extend(records)
    c["profile"]["notes"] += " Imported partial measurements; validation against the physical plant is still required."
    validate_config(c)
    # Validate the whole batch before creating output. Never overwrite its source.
    with Path(output).open("x",encoding="utf-8") as stream:
        json.dump(c,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
    return c


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base",type=Path)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--measurements",type=Path)
    action.add_argument("--export-template",type=Path,help='Export every configurable numeric field, leaving measurements blank')
    parser.add_argument("--output",type=Path)
    parser.add_argument("--name")
    args=parser.parse_args()
    if args.export_template:
        rows=export_template(load_config(args.base),args.export_template)
        print(f'Created {args.export_template}: {len(rows)} editable SI parameters')
    else:
        if args.output is None: parser.error('--output is required when importing measurements')
        c=import_measurements(load_config(args.base),args.measurements,args.output,args.name)
        print(f"Created {args.output}: status={c['profile']['status']}, measurements={len(c['profile']['measurements'])}")
