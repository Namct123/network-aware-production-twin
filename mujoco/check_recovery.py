"""MuJoCo post-HOLD review fixtures: restoration must never restart the cell."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from config import load_config
from experiment import run,write_json

DEFAULT=Path(__file__).parent/'configs/hold_review_cell_20261031.json'

def check(output,config=None):
    base=load_config(DEFAULT) if config is None else config
    if not base.get('recovery',{}).get('enabled'): raise ValueError('Enabled recovery assessment profile required')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    cases=[('nominal',{},'none',True,'DONE','NOT_HOLD'),
           ('transient_feed',{'outage':[[.1,.30]]},'none',True,'HOLD','OPERATOR_REVIEW'),
           ('transient_track',{'outage':[[5.4,5.56]]},'none',True,'HOLD','OPERATOR_REVIEW'),
           ('persistent_track',{'outage':[[5.4,10]]},'none',True,'HOLD','WAIT_OBSERVATIONS'),
           ('pickup_missing',{},'ps2_stuck_low',True,'HOLD','MANUAL_INTERVENTION'),
           ('upstream_missing',{},'ps1_stuck_low',True,'HOLD','MANUAL_INTERVENTION'),
           ('pusher_missing',{},'transfer_present_stuck_low',True,'HOLD','MANUAL_INTERVENTION'),
           ('initial_high',{},'ps2_stuck_high',True,'HOLD','MANUAL_INTERVENTION'),
           ('strict',{},'none',False,'HOLD','MANUAL_INTERVENTION'),
           ('review_expired',{'outage':[[.1,.3]],'max_hold':.2},'none',True,'HOLD','MANUAL_INTERVENTION')]
    results=[]
    for name,patch,fault,assume,expected,stage in cases:
        c=deepcopy(base); c['prediction']['wall_budget_s']=1.0
        c['network']['outage_windows_s']=patch.get('outage',[])
        c['recovery']['max_hold_age_s']=patch.get('max_hold',base['recovery']['max_hold_age_s'])
        summary=run(output/name,config=c,fault=fault,assume_open_loop=assume)
        reviews=[json.loads(s) for s in (output/name/'recovery.jsonl').read_text().splitlines()]
        commands=[json.loads(s) for s in (output/name/'controller.jsonl').read_text().splitlines()]
        held=[r for r in commands if r['phase']=='HOLD']
        no_restart=all(r['command']['hold'] and r['command']['front']==r['command']['long']==0 for r in held)
        no_restart=no_restart and all(not r['automatic_resume_allowed'] and not r['restart_command_issued'] for r in reviews)
        no_restart=no_restart and not any(t['from']=='HOLD' for t in summary['transitions'])
        terminal=(summary['placement_pass_evaluator_only'] is True if expected=='DONE'
                  else summary['hold_product_supported_evaluator_only'] is True)
        passed=(summary['controller_state']==expected and summary['recovery_assessment']['stage']==stage
                and no_restart and terminal)
        if expected=='HOLD': passed=passed and summary['hold_context'] is not None
        results.append({'case':name,'pass':passed,'no_restart_invariant':no_restart,**summary})
        write_json(output/'results.json',results)
        print(f"{name}: {'PASS' if passed else 'FAIL'}; {summary['controller_state']}; {summary['hold_reason']}; {summary['recovery_assessment']['stage']}",flush=True)
    if not all(r['pass'] for r in results): raise AssertionError('Inspect recovery review fixture failures')
    print(f'PASS: {len(results)}/{len(cases)} recovery review cases; no restart commands',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True); p.add_argument('--config',type=Path)
    a=p.parse_args(); check(a.output,load_config(a.config or DEFAULT))
