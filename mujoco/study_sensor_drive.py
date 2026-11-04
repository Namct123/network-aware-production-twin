"""Controlled virtual sensor/drive ambiguity study; plant truth remains evaluator-only."""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
from config import exact_keys,load_config,validate_config
from model_profile import write_model
from runtime import RuntimeCore
from sensor_model import SensorModel

HERE=Path(__file__).resolve().parent
CASES=('nominal','feed_sensor_missing','feed_drive_stall','pickup_sensor_missing','long_drive_stall','pickup_sensor_high','upstream_sensor_missing')


def write(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def load_plan(path):
    p=json.loads(Path(path).read_text(encoding='utf-8'))
    exact_keys(p,('kind','repetitions','cases','scope'),'sensor-drive plan')
    if p['kind']!='sensor_drive_plan_v1' or p['cases']!=list(CASES):raise ValueError('fixed seven-case matrix required')
    if type(p['repetitions']) is not int or not 1<=p['repetitions']<=5:raise ValueError('1..5 repeats required')
    return p


def should_start(case,phase,previous,current,anchors):
    if case.startswith('feed_'):return phase=='FEED'
    if case=='upstream_sensor_missing':return phase=='TRACK'
    if case in ('pickup_sensor_missing','long_drive_stall','pickup_sensor_high'):
        return phase=='TRACK' and anchors>=1 and previous is True and current is False
    return False


def inject_signal(frame,case):
    signal,level={'feed_sensor_missing':('transfer_present',False),
        'pickup_sensor_missing':('ps2',False),'pickup_sensor_high':('ps2',True),
        'upstream_sensor_missing':('ps1',False)}.get(case,(None,None))
    return replace(frame,values={**frame.values,signal:level}) if signal else frame


def applied_command(command,case,active):
    result=deepcopy(command)
    if active and case=='feed_drive_stall':result['front']=0.
    if active and case=='long_drive_stall':result['long']=0.
    return result


def trial(folder,config,case):
    from run_cell import Cell
    folder.mkdir(parents=True,exist_ok=False)
    model=write_model(config,folder/'effective_model.xml');write(folder/'effective_config.json',config)
    cell=Cell(config,model);sensor=SensorModel(config=config)
    core=RuntimeCore(config)  # Opaque UUID session: no fixture label in core metadata.
    period=config['timing']['physics_step_s']*config['timing']['sample_steps']
    onset=None;previous=None;first_finding=None;first_hold=None;count=0
    try:
        with (folder/'observations.jsonl').open('w',encoding='utf-8') as observations,(folder/'decisions.jsonl').open('w',encoding='utf-8') as decisions,(folder/'truth_evaluator_only.jsonl').open('w',encoding='utf-8') as truth:
            for index in range(math.ceil(config['timing']['run_budget_s']/period)+1):
                state=cell.observe();now=state['time_s'];frame,_=sensor.sample(state)
                if onset is None and should_start(case,core.controller.phase,previous,frame.values['ps1'],core.controller.estimator.estimate.anchors):onset=now
                original_ps1=frame.values['ps1']
                if onset is not None:frame=inject_signal(frame,case)
                # Only the sensor frame enters the DT. Fault label, actual applied drive
                # command and product pose stay in the independent experiment/evaluator.
                step=core.step(core.wrap(frame),now)
                command=step['command'];actual=applied_command(command,case,onset is not None)
                observations.write(json.dumps(frame.as_dict(),allow_nan=False)+'\n')
                record={'time_s':now,'phase':core.controller.phase,'reason':core.controller.reason,
                    'estimate':core.controller.estimator.estimate.as_dict(),'command':command,
                    'prediction':step['prediction'],'health':step['health'],'policy':step['policy']}
                decisions.write(json.dumps(record,allow_nan=False)+'\n')
                truth.write(json.dumps({'time_s':now,'product_xyz_m':state['product_xyz_m'],
                    'physical_ps1':state['ps1'],'physical_ps2':state['ps2'],
                    'physical_transfer_present':state['transfer_present'],'applied_command':actual},allow_nan=False)+'\n')
                findings=(step['health'] or {}).get('findings',[])
                if onset is not None and findings and first_finding is None:first_finding={'time_s':now,'codes':[f['code'] for f in findings]}
                if core.controller.phase=='HOLD' and first_hold is None:first_hold={'time_s':now,'reason':core.controller.reason}
                cell.apply(actual);previous=original_ps1;count+=1
                if first_hold and now-first_hold['time_s']>=config['timing']['hold_settle_s']:break
                cell.step()
    finally:core.close()
    result={'case':case,'session_context':core.context,'onset_s':onset,'ticks':count,'first_finding':first_finding,'first_hold':first_hold,
        'finding_delay_ms':1000*(first_finding['time_s']-onset) if first_finding and onset is not None else None,
        'hold_delay_ms':1000*(first_hold['time_s']-onset) if first_hold and onset is not None else None,
        'controller_state':core.controller.phase,'hold_reason':core.controller.reason,
        'health':core.health.summary(),'physical_output':False,'physical_validation':False,
        'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
        'truth_scope':'evaluator only; not provided to RuntimeCore or estimator'}
    write(folder/'summary.json',result)
    return result


def rows(path):return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]


def pair(folder,left,right):
    a,b=folder/left,folder/right
    sa,sb=json.loads((a/'summary.json').read_text()),json.loads((b/'summary.json').read_text())
    times=[s['first_hold']['time_s'] for s in (sa,sb) if s['first_hold']]
    until=min(times) if len(times)==2 else None
    obs_a,obs_b=rows(a/'observations.jsonl'),rows(b/'observations.jsonl')
    dec_a,dec_b=rows(a/'decisions.jsonl'),rows(b/'decisions.jsonl')
    def prefix(values):return [r for r in values if until is not None and r.get('time_s',r.get('received_time_s'))<=until]
    def logical(r):
        result={**r}
        if result.get('prediction') is not None:result['prediction']={k:v for k,v in result['prediction'].items() if k!='compute_ms'}
        return result
    oa,ob=prefix(obs_a),prefix(obs_b);da,db=prefix(dec_a),prefix(dec_b)
    pose_a=next((r['product_xyz_m'] for r in rows(a/'truth_evaluator_only.jsonl') if r['time_s']==until),None)
    pose_b=next((r['product_xyz_m'] for r in rows(b/'truth_evaluator_only.jsonl') if r['time_s']==until),None)
    equal_prefix=0
    for x,y in zip(obs_a,obs_b):
        if x!=y:break
        equal_prefix+=1
    return {'left':left,'right':right,'through_first_hold_s':until,
        'observations_equal_through_hold':bool(oa) and oa==ob,
        'decisions_equal_through_hold':bool(da) and [logical(x) for x in da]==[logical(x) for x in db],
        'equal_observation_prefix_ticks':equal_prefix,
        'evaluator_pose_separation_m':math.dist(pose_a,pose_b) if pose_a is not None and pose_b is not None else None,
        'pose_scope':'hidden simulation truth used for this audit only, not diagnostic input'}


def study(output,config_path=HERE/'configs/reconfigurable_cell_20261030.json',plan_path=HERE/'experiments/sensor_drive_20261104.json'):
    config=load_config(config_path);validate_config(config);plan=load_plan(plan_path)
    period=config['timing']['physics_step_s']*config['timing']['sample_steps']
    if 'mechanics' not in config or config['timing']['run_budget_s']/period>10000:raise ValueError('mechanical profile and <=10000 ticks required')
    if config['prediction'].get('background',{}).get('enabled') or config['prediction'].get('backend','numeric_1d')!='numeric_1d':raise ValueError('numeric predictor without background required')
    if any(config['network'][n] for n in ('delay_s','jitter_s','drop_probability')):raise ValueError('study directly delivers frames; network impairment must be zero')
    output=Path(output);output.mkdir(parents=True,exist_ok=False);write(output/'plan.json',plan)
    write(output/'manifest.json',{'kind':'sensor_drive_source_v1','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')},
        'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
        'boundary':'Core receives only SensorModel frames with optional injected digital bit; drive override and poses are evaluator-side'})
    results=[];comparisons=[]
    for repeat in range(1,plan['repetitions']+1):
        for case in CASES:
            name=f'{repeat:02}_{case}';print('Sensor/drive:',name,flush=True)
            results.append({'name':name,**trial(output/name,config,case)})
            write(output/'partial_results.json',results)
        for left,right in [('feed_sensor_missing','feed_drive_stall'),('pickup_sensor_missing','long_drive_stall')]:
            comparisons.append(pair(output,f'{repeat:02}_{left}',f'{repeat:02}_{right}'))
    valid=all(r['controller_state'] in ('HOLD','DONE') and (r['case']=='nominal' or r['onset_s'] is not None) for r in results)
    report={'kind':'sensor_drive_study_v1','passed':valid,'trial_count':len(results),'trials':results,'pairs':comparisons,
        'physical_validation':False,'physical_output':False,'parameter_tuning':False,
        'scope':'fixed counterexample-oriented fault fixtures; not representative classification accuracy; strict single-product loop stops before unconfirmed XY/vacuum actuation'}
    write(output/'sensor_drive_study.json',report)
    lines=['# Cảm biến không báo hay băng tải không chạy?','',
        '| Ca thử | Từ lúc chèn tới nghi ngờ đầu (ms) | Từ lúc chèn tới dừng (ms) | Mã lý do dừng |',
        '|---|---:|---:|---|']
    for r in results:
        f=lambda key:'không có' if r[key] is None else f"{r[key]:.1f}"
        lines.append(f"| {r['name']} | {f('finding_delay_ms')} | {f('hold_delay_ms')} | {r['hold_reason']} |")
    lines+=['',f"{len(comparisons)} cặp kiểm tra; {sum(p['observations_equal_through_hold'] and p['decisions_equal_through_hold'] for p in comparisons)} cặp cùng quan sát/quyết định tới lần dừng đầu.",'',
        'Vị trí thật chỉ chấm ở tệp truth_evaluator_only.jsonl; không vào bộ ước lượng. Có cùng quan sát nhưng vị trí khác là giới hạn tách nguyên nhân trong các ca đã chọn. Không diễn giải thành độ chính xác cảm biến hoặc hiệu quả mọi tình huống lỗi.']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    p.add_argument('--plan',type=Path,default=HERE/'experiments/sensor_drive_20261104.json')
    a=p.parse_args();raise SystemExit(int(not study(a.output,a.config,a.plan)['passed']))
