"""Acceptance of the parameterized plant; all values are profiles, not physical claims."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from config import load_config
from experiment import run

DEFAULT=Path(__file__).parent/'configs/measured_cell_20261030.json'

def check(output,config=None):
    base=load_config(DEFAULT) if config is None else config
    if 'mechanics' not in base: raise ValueError('This suite requires a parameterized mechanics profile')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    cases=[(f'bin_{b}',b,'none',True,'DONE',{}) for b in range(1,7)]
    cases += [('strict',1,'none',False,'HOLD',{}),
              ('pusher_sensor_missing',1,'transfer_present_stuck_low',True,'HOLD',{}),
              ('pusher_sensor_stuck_high',1,'transfer_present_stuck_high',True,'HOLD',{}),
              ('upstream_missing',1,'ps1_stuck_low',True,'HOLD',{}),
              ('pickup_missing',1,'ps2_stuck_low',True,'HOLD',{}),
              ('loss_all',1,'none',True,'HOLD',{'loss':1.0}),
              ('speed_low',1,'none',True,'DONE',{'speed':base['motion']['test_speed_range_m_s'][0]}),
              ('speed_high',1,'none',True,'DONE',{'speed':base['motion']['test_speed_range_m_s'][1]}),
              ('mass_variant',1,'none',True,'DONE',{'mass':base['plant']['product_mass_kg']*1.5}),
              ('height_variant',1,'none',True,'DONE',{'height_delta':.01}),
              ('baseline_nominal',1,'none',True,'DONE',{'prediction':False}),
              ('baseline_pickup_missing',1,'ps2_stuck_low',True,'HOLD',{'prediction':False})]
    results=[]
    for name,b,fault,assume,expected,patch in cases:
        c=deepcopy(base)
        c['prediction']['enabled']=patch.get('prediction',True)
        if 'loss' in patch: c['network']['drop_probability']=patch['loss']
        if 'speed' in patch: c['motion']['long_speed_m_s']=patch['speed']
        if 'mass' in patch: c['plant']['product_mass_kg']=patch['mass']
        if 'height_delta' in patch:
            dz=patch['height_delta']
            c['mechanics']['belt_surface_z_m']+=dz
            c['mechanics']['cup_retracted_z_m']+=dz
            c['mechanics']['pusher_rest_xyz_m'][2]+=dz
            c['geometry']['product_initial_xyz_m'][2]+=dz
            c['geometry']['optical_xz_m'][1]+=dz
            c['geometry']['hold_z_m']=[v+dz for v in c['geometry']['hold_z_m']]
        result=run(output/name,b,assume_open_loop=assume,fault=fault,config=c)
        passed=result['controller_state']==expected and (result['placement_pass_evaluator_only'] is True
            if expected=='DONE' else result['hold_product_supported_evaluator_only'] is True)
        results.append({'case':name,'pass':passed,**result})
        (output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(f"{name}: {'PASS' if passed else 'FAIL'}; {result['controller_state']}; {result['hold_reason']}",flush=True)
    by={r['case']:r for r in results}
    comparison={'nominal_cycle_difference_s':by['baseline_nominal']['simulation_time_s']-by['bin_1']['simulation_time_s'],
                'pickup_fault_earlier_hold_s':by['baseline_pickup_missing']['hold_time_s']-by['pickup_missing']['hold_time_s'],
                'baseline_fault_reason':by['baseline_pickup_missing']['hold_reason'],
                'predictive_fault_reason':by['pickup_missing']['hold_reason'],
                'scope':'matched fixtures in parameterized simulation; no physical validation or general accuracy claim'}
    (output/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    if not all(r['pass'] for r in results): raise AssertionError('Inspect failed measured-profile cases; do not infer pass from DONE alone')
    print(f'PASS: {len(results)}/{len(cases)} parameterized simulation cases',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True); p.add_argument('--config',type=Path)
    a=p.parse_args(); check(a.output,load_config(a.config or DEFAULT))
