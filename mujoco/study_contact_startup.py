"""Evaluator-only paired contact/startup audit on already observed conditions."""
import argparse
from copy import deepcopy
import itertools
import hashlib
import json
import math
from pathlib import Path
from calibrate_residual import digest, save
from config import load_config
from audit_pulse_model import sampling_window
from study_pulse import rows
HERE=Path(__file__).resolve().parent


def protocol_digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def pulse_summary(obs,truth,length,distance,period,bias,radius):
    if not obs or len(obs)!=len(truth) or any(o['source_time_s']!=t['time_s'] for o,t in zip(obs,truth)):
        raise ValueError('nonempty aligned records required')
    result={'initial_upstream_active':obs[0]['values']['ps1'],'status':'initial_pulse_unresolved'}
    if result['initial_upstream_active']:return result
    rise=next((k for k in range(1,len(obs)) if obs[k-1]['values']['ps1'] is False and obs[k]['values']['ps1'] is True),None)
    fall=next((k for k in range((rise or 0)+1,len(obs)) if rise is not None and obs[k-1]['values']['ps1'] is True and obs[k]['values']['ps1'] is False),None)
    if fall is None:return {**result,'status':'no_complete_pulse'}
    target=next((k for k in range(fall,len(obs)) if obs[k]['values']['ps2'] is True),None)
    if target is None:return {**result,'status':'target_not_observed'}
    t=lambda k:obs[k]['source_time_s'];y=lambda k:truth[k]['product_xyz_m'][1]
    window=sampling_window(t(rise),t(fall),length,distance,period)
    pulse=(y(fall)-y(rise))/(t(fall)-t(rise));remaining=(y(target)-y(fall))/(t(target)-t(fall))
    corrected=max(t(fall),window['point_s']+bias)
    return {**result,'status':'resolved','rise_s':t(rise),'fall_s':t(fall),'target_s':t(target),
            'pulse_speed_m_s':pulse,'remaining_speed_m_s':remaining,'relative_speed_increase':remaining/pulse-1,
            'pulse_residual_s':t(target)-window['point_s'],'constant_residual_s':t(target)-corrected,
            'sampling_only_covered':window['interval_s'][0]-1e-9<=t(target)<=window['interval_s'][1]+1e-9,
            'frozen_constant_covered':abs(t(target)-corrected)<=radius+1e-9}


def record(folder,base,condition,start,settle_s,moving_bridge,segment):
    import mujoco
    import numpy as np
    from run_cell import Cell
    from sensor_model import SensorModel
    cfg=deepcopy(base);v,g=condition
    cfg['geometry']['product_initial_xyz_m']=[cfg['geometry']['lane_x_m'],start,cfg['mechanics']['belt_surface_z_m']+.031]
    cfg['motion']['long_speed_m_s']=v;cfg['plant']['belt_speed_scale']['long']=g
    cfg['plant']['product_friction'][0]=1.
    cfg['reconfiguration']['degraded_long_speed_m_s']=min(cfg['reconfiguration']['degraded_long_speed_m_s'],v)
    cell=Cell(cfg);bridge=cell.model.geom('transfer_bridge').id;product=cell.model.geom('product_box').id
    if settle_s:
        cell.step(round(settle_s/cfg['timing']['physics_step_s']))
        # Diagnostic clock origin only. Preserve settled pose/velocity; no hidden pose reset.
        cell.data.time=0.;mujoco.mj_forward(cell.model,cell.data)
    if moving_bridge:
        cell.model.geom_surfacevel[bridge,:3]=(0,v*g,0);cell._refresh_constants()
    folder.mkdir();save(folder/'effective_plant_config.json',cfg)
    mujoco.mj_saveLastXML(str(folder/'effective_model.xml'),cell.model)
    sensors=SensorModel(config=cfg);period=cfg['timing']['physics_step_s']*cfg['timing']['sample_steps']
    command={'front':0.,'long':v,'targets':{},'vacuum':False,'hold':False}
    names=['observations.jsonl','issued_commands.jsonl','evaluator_only.jsonl','contact_evaluator_only.jsonl']
    handles=[(folder/n).open('w',encoding='utf-8',newline='\n') for n in names]
    try:
        for _ in range(math.floor(segment['command_distance_m']/v/period)+1):
            state=cell.observe();now=state['time_s'];frame,_=sensors.sample(state)
            pairs=[];normal=0.
            for contact_id in range(cell.data.ncon):
                contact=cell.data.contact[contact_id]
                if product not in contact.geom:continue
                other=int(contact.geom[1] if contact.geom[0]==product else contact.geom[0])
                pairs.append(cell.model.geom(other).name)
                if other==bridge and contact.efc_address>=0:
                    force=np.zeros(6);mujoco.mj_contactForce(cell.model,cell.data,contact_id,force);normal+=abs(float(force[0]))
            records=[frame.as_dict(),{'time_s':now,'command':command},
                     {'time_s':now,'product_xyz_m':state['product_xyz_m'],'applied_command':command},
                     {'time_s':now,'product_contacts':sorted(set(pairs)),'bridge_normal_force_abs_sum_n':normal,
                      'product_quaternion_wxyz':cell.data.xquat[cell.product].tolist()}]
            for stream,row in zip(handles,records):stream.write(json.dumps(row)+'\n')
            cell.apply(command);cell.step()
    finally:
        for stream in handles:stream.close()
    return names


def study(plan_path,source,out):
    p=json.loads(plan_path.read_text());clock=HERE/'experiments/network_clock_ablation_20261106.json'
    if p['kind']!='contact_startup_audit_v1' or p.get('reference_hash_encoding')!='utf8_lf' or p['reference_plan_sha256']!=protocol_digest(clock):raise ValueError('frozen reference plan required')
    expected={'baseline':(0.,False),'settled':(.4,False),'moving_bridge':(0.,True),'settled_moving_bridge':(.4,True)}
    if p['arms']!={n:{'settle_s':s,'moving_bridge':b} for n,(s,b) in expected.items()}:raise ValueError('fixed paired interventions required')
    prior=json.loads(clock.read_text());cfg_path=HERE/'configs/reconfigurable_cell_20261030.json';base=load_config(cfg_path)
    segment=json.loads((HERE/'experiments/interval_calibration_20261105.json').read_text())
    model=json.loads((HERE/'models/eta_residual_v1.json').read_text());settings=json.loads((HERE/'models/eta_monitor_v1.json').read_text())
    g=base['geometry'];length=g['product_size_m'][1];distance=g['ps_y_m']['ps2']-g['ps_y_m']['ps1']-length
    period=base['timing']['physics_step_s']*base['timing']['sample_steps']
    out.mkdir(parents=True,exist_ok=False);save(out/'protocol.json',p)
    manifest={'plan_sha256':digest(plan_path),'reference_plan_sha256':digest(clock),'config_sha256':digest(cfg_path),
              'sources':{x.name:digest(x) for x in HERE.glob('*.py')},'inputs':{},'outputs':{}}
    results=[];baseline_exact=0
    for i,(v,g,y) in enumerate(itertools.product(prior['speeds_m_s'],prior['gains'],prior['start_y_m'])):
        ref=source/f'condition_{i:02}_none'
        for arm,(settle,moving) in expected.items():
            name=f'condition_{i:02}_{arm}';folder=out/name;print(name,flush=True)
            names=record(folder,base,(v,g),y,settle,moving,segment)
            for n in names:manifest['outputs'][name+'/'+n]=digest(folder/n)
            if arm=='baseline':
                for n in names[:3]:
                    manifest['inputs'][ref.name+'/'+n]=digest(ref/n)
                    if digest(ref/n)!=digest(folder/n):raise ValueError('baseline no longer reproduces prior recording: '+name+'/'+n)
                baseline_exact+=1
            obs,truth,contacts=(rows(folder/n) for n in [names[0],names[2],names[3]])
            summary=pulse_summary(obs,truth,length,distance,period,model['constant_bias_s'],settings['radii_s']['constant'])
            bridge_times=[r['time_s'] for r in contacts if r['bridge_normal_force_abs_sum_n']>1e-9]
            results.append({'id':i,'arm':arm,**summary,'bridge_force_samples':len(bridge_times),
                            'last_bridge_force_s':max(bridge_times) if bridge_times else None,
                            'bridge_force_during_pulse':sum(summary.get('rise_s',math.inf)<=t<=summary.get('fall_s',-math.inf) for t in bridge_times)})
    groups={}
    for arm in expected:
        rs=[r for r in results if r['arm']==arm];resolved=[r for r in rs if r['status']=='resolved']
        groups[arm]={'planned':len(rs),'resolved':len(resolved),'initially_high':sum(r['initial_upstream_active'] for r in rs),
                     'pulse_mae_ms':sum(abs(r['pulse_residual_s']) for r in resolved)*1000/len(resolved) if resolved else None,
                     'constant_mae_ms':sum(abs(r['constant_residual_s']) for r in resolved)*1000/len(resolved) if resolved else None,
                     'sampling_only_covered':sum(r['sampling_only_covered'] for r in resolved),
                     'frozen_constant_covered':sum(r['frozen_constant_covered'] for r in resolved),
                     'bridge_force_during_pulse_runs':sum(r['bridge_force_during_pulse']>0 for r in resolved),
                     'relative_speed_increase_range': [min(r['relative_speed_increase'] for r in resolved),max(r['relative_speed_increase'] for r in resolved)] if resolved else None}
    report={'kind':p['kind'],'analysis_kind':'posthoc_simulator_intervention','recordings':len(results),'baseline_exact':baseline_exact,
            'groups':groups,'records':results,'physical_validation':False,'predictor_changed':False,
            'scope':p['scope']}
    save(out/'manifest.json',manifest);save(out/'results.json',report);print(json.dumps(groups),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,default=HERE/'experiments/contact_startup_audit_20261106.json');p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();study(a.plan,a.source,a.output)
