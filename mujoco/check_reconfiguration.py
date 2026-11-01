"""Paired one-product simulation fixtures for automatic speed degradation and HOLD."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from config import load_config
from experiment import run

DEFAULT=Path(__file__).parent/'configs/reconfigurable_cell_20261030.json'

def check(output,config=None):
    base=load_config(DEFAULT) if config is None else config
    if not base.get('reconfiguration',{}).get('enabled'): raise ValueError('Enabled reconfiguration profile required')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    cases=[('nominal',{},'none','DONE','COMPLETE'),
           ('delay_20ms',{'delay':.02},'none','DONE','COMPLETE'),
           ('delay_20ms_baseline',{'delay':.02,'enabled':False},'none','HOLD','NORMAL'),
           ('delay_20ms_fixed_slow',{'delay':.02,'enabled':False,'speed':.12},'none','DONE','NORMAL'),
           ('delay_40ms',{'delay':.04},'none',None,None),
           ('delayed_acceleration',{'delay':.02,'schedule':[(.6,.22)]},'none','DONE','COMPLETE'),
           ('delayed_stop_resume',{'delay':.02,'schedule':[(.6,0),(.8,.22)]},'none','DONE','COMPLETE'),
           ('pickup_missing',{},'ps2_stuck_low','HOLD','HOLD'),
           ('pickup_missing_baseline',{'enabled':False},'ps2_stuck_low','HOLD','NORMAL'),
           ('upstream_missing',{},'ps1_stuck_low','HOLD','HOLD'),
           ('pusher_missing',{},'transfer_present_stuck_low','HOLD','HOLD'),
           ('initial_pickup_high',{},'ps2_stuck_high','HOLD','HOLD'),
           ('loss_all',{'loss':1},'none','HOLD','HOLD'),
           ('seeded_loss',{'loss':.15},'none',None,None),
           ('runtime_20ms',{'runtime_budget':.02},'none',None,None)]
    results=[]
    for name,patch,fault,expected,mode in cases:
        c=deepcopy(base)
        c['prediction']['wall_budget_s']=patch.get('runtime_budget',1.0)
        c['reconfiguration']['enabled']=patch.get('enabled',True)
        c['network']['delay_s']=patch.get('delay',0)
        c['network']['drop_probability']=patch.get('loss',0)
        c['motion']['long_speed_m_s']=patch.get('speed',base['motion']['long_speed_m_s'])
        c['motion']['long_speed_schedule']=[{'track_time_s':t,'speed_m_s':v} for t,v in patch.get('schedule',[])]
        result=run(output/name,config=c,assume_open_loop=True,fault=fault)
        records=[json.loads(s) for s in (output/name/'reconfiguration.jsonl').read_text().splitlines()]
        degraded=any(e['mode']=='DEGRADED' for e in result['reconfiguration']['events'])
        supported=(result['placement_pass_evaluator_only'] is True if result['controller_state']=='DONE'
                   else result['controller_state']=='HOLD' and result['hold_product_supported_evaluator_only'] is True)
        passed=supported and (expected is None or result['controller_state']==expected) and (mode is None or result['reconfiguration']['mode']==mode)
        if name in {'delay_20ms','delayed_acceleration','delayed_stop_resume'}:
            passed=passed and degraded and all(r['selected_long_speed_m_s']<=c['reconfiguration']['degraded_long_speed_m_s']
                for r in records if r['mode']=='DEGRADED' and r['phase']=='TRACK')
        if name=='nominal': passed=passed and not degraded
        if name=='pickup_missing': passed=passed and result['hold_reason']=='reconfiguration:expected_edge_missing'
        if name=='delay_20ms_baseline': passed=passed and result['hold_reason']=='pick_uncertainty_exceeded'
        results.append({'case':name,'pass':passed,**result})
        (output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(f"{name}: {'PASS' if passed else 'FAIL'}; {result['controller_state']}; {result['hold_reason']}; degraded={degraded}",flush=True)
    by={r['case']:r for r in results}
    comparison={'delay_20ms_enabled_state':by['delay_20ms']['controller_state'],
                'delay_20ms_disabled_state':by['delay_20ms_baseline']['controller_state'],
                'delay_20ms_disabled_reason':by['delay_20ms_baseline']['hold_reason'],
                'delay_20ms_vs_fixed_slow_cycle_difference_s':by['delay_20ms']['simulation_time_s']-by['delay_20ms_fixed_slow']['simulation_time_s'],
                'pickup_missing_earlier_hold_s':by['pickup_missing_baseline']['hold_time_s']-by['pickup_missing']['hold_time_s'],
                'scope':'paired functional fixtures, budget 1s; slower operation is intentional; no physical or statistical reliability claim'}
    (output/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    if not all(r['pass'] for r in results): raise AssertionError('Inspect reconfiguration failures')
    print(f'PASS: {len(results)}/{len(cases)} reconfiguration simulation cases',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True); p.add_argument('--config',type=Path)
    a=p.parse_args(); check(a.output,load_config(a.config or DEFAULT))
