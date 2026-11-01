"""Bounded assembly checks; no parameter search and no physical output."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from config import load_config
from experiment import run,write_json
from replay_input import replay
from physics_predictor import MuJoCoBeltPredictor

HERE=Path(__file__).resolve().parent

def check(output):
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    config=load_config(HERE/'configs/reconfigurable_cell_20261030.json')
    checks={}
    for name,open_loop in [('strict',False),('open_loop',True)]:
        result=run(output/name,config=config,assume_open_loop=open_loop)
        checks[name]={'passed':result['controller_state']==('DONE' if open_loop else 'HOLD'),
                      'state':result['controller_state'],'reason':result.get('hold_reason')}
        if open_loop: checks[name]['passed'] &= bool(result.get('placement_pass_evaluator_only'))
    rows=[{'session_id':'synthetic','generation':0,'sequence':i,'source_time':i*.02,
           'received_time_s':i*.02,'values':{'PS2_upstream':False},'quality':{'PS2_upstream':'good'}} for i in range(3)]
    source=output/'synthetic.jsonl'
    source.write_text('\n'.join(json.dumps(r) for r in rows)+'\n',encoding='utf-8')
    result=replay(source,HERE/'configs/recording_map_example.json',config,output/'replay')
    checks['replay']={'passed':result['rows']==3 and not result['physical_output_supported'] and result['controller_state']=='HOLD'}
    physics=deepcopy(config)
    # Functional check only: explicitly separate from the configured real-time budget.
    physics['prediction']['wall_budget_s']=2.0
    state=SimpleNamespace(y_m=sum(config['geometry']['long_belt_y_m'])/2,velocity_m_s=.05,uncertainty_m=.001)
    before=vars(state).copy()
    forecast=MuJoCoBeltPredictor(physics).rollout(state,0,0)
    checks['physics_forecast']={'passed':vars(state)==before and
        ((forecast['status']=='complete' and forecast['completed_scenarios']==forecast['expected_scenarios']) or
         (forecast['status']=='deadline_exceeded' and forecast['action']=='HOLD')),'result':forecast,
         'scope':'functional check with 2 s budget; not a real-time benchmark or calibration'}
    deadline_predictor=MuJoCoBeltPredictor(config)
    ticks=iter([0.0,config['prediction']['wall_budget_s']+1,config['prediction']['wall_budget_s']+1])
    deadline_predictor.clock=lambda:next(ticks)
    expired=deadline_predictor.rollout(state,0,0)
    checks['deadline_guard']={'passed':expired['status']=='deadline_exceeded' and expired['action']=='HOLD',
                              'scope':'deterministic injected elapsed time, not a speed measurement'}
    report={'passed':all(c['passed'] for c in checks.values()),'checks':checks,
            'physical_output':False,'parameter_tuning':False,'user_acceptance':'pending'}
    write_json(output/'summary.json',report)
    (output/'report.md').write_text('# Kiểm tra bản ghép\n\n'+
        '\n'.join(f"- {name}: {'đạt' if c['passed'] else 'cần xem lại'}." for name,c in checks.items())+
        '\n\nChỉ kiểm tra phần mềm. Không xác nhận độ chính xác máy thật, không điều chỉnh tham số.\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True)
    raise SystemExit(0 if check(p.parse_args().output)['passed'] else 1)
