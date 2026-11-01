"""Bounded simulation qualification of command-history estimation and health hypotheses."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from config import load_config
from experiment import run

DEFAULT=Path(__file__).parent/'configs/observable_cell_20261030.json'

def check(output,config=None):
    base=load_config(DEFAULT) if config is None else config
    if not base['estimator'].get('command_history_enabled') or not base.get('health',{}).get('enabled'):
        raise ValueError('Observer qualification requires enabled history and health modules')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    # Expected outcomes are fixture-specific: no hardware accuracy/latency claims.
    cases=[('nominal',{},'none',0,'DONE',None),
           ('runtime_20ms_budget',{'runtime_budget':.02},'none',0,None,None),
           ('accelerate',{'schedule':[(.6,.22)]},'none',0,'DONE',None),
           ('decelerate',{'schedule':[(.6,.10)]},'none',0,'DONE',None),
           ('stop_resume',{'schedule':[(.6,0),(.8,.16)]},'none',0,'DONE',None),
           ('delayed_speed_change',{'schedule':[(.6,.22)],'delay':.04},'none',0,None,None),
           ('upstream_missing',{},'ps1_stuck_low',0,'HOLD','unmatched_pickup_observation'),
           ('pickup_missing',{},'ps2_stuck_low',0,'HOLD','expected_edge_missing'),
           ('upstream_high_after_start',{},'ps1_stuck_high',3,'HOLD',None),
           ('initial_pickup_high',{},'ps2_stuck_high',0,'HOLD','unmatched_pickup_observation'),
           ('loss_all',{'loss':1},'none',0,'HOLD','telemetry_silence'),
           ('old_telemetry',{'delay':.12},'none',0,'HOLD','stale_observation'),
           ('seeded_loss',{'loss':.15},'none',0,None,'observation_sequence_gap')]
    results=[]
    for name,patch,fault,onset,expected,event in cases:
        c=deepcopy(base)
        # Functional correctness checks allow host scheduling pauses; the separate
        # 20ms case retains the deployed deadline and must HOLD on an overrun.
        c['prediction']['wall_budget_s']=patch.get('runtime_budget',1.0)
        c['motion']['long_speed_schedule']=[{'track_time_s':t,'speed_m_s':v} for t,v in patch.get('schedule',[])]
        c['network']['delay_s']=patch.get('delay',0)
        c['network']['drop_probability']=patch.get('loss',0)
        result=run(output/name,assume_open_loop=True,config=c,fault=fault,fault_start_s=onset)
        codes={x['code'] for x in result['signal_health']['events']}
        supported=(result['placement_pass_evaluator_only'] is True if result['controller_state']=='DONE'
                   else result['hold_product_supported_evaluator_only'] is True)
        passed=(expected is None or result['controller_state']==expected) and supported and (event is None or event in codes)
        if name=='nominal': passed=passed and not codes
        results.append({'case':name,'pass':passed,'expected_state':expected or 'DONE or supported HOLD',
                        'expected_health_code':event,**result})
        (output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(f"{name}: {'PASS' if passed else 'FAIL'}; {result['controller_state']}; {result['hold_reason']}; {sorted(codes)}",flush=True)
    if not all(r['pass'] for r in results): raise AssertionError('Inspect observer qualification failures')
    print(f'PASS: {len(results)}/{len(cases)} observer simulation cases',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True); p.add_argument('--config',type=Path)
    a=p.parse_args(); check(a.output,load_config(a.config or DEFAULT))
