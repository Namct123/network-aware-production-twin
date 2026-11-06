"""Post-hoc model audit; plant positions are evaluator-only, never predictor inputs."""
import argparse
import json
import math
from pathlib import Path
from calibrate_residual import digest,save
from config import load_config
from study_pulse import rows
HERE=Path(__file__).resolve().parent


def sampling_window(rise,fall,length,distance,period):
    values=[rise,fall,length,distance,period]
    if not all(type(v) in (int,float) and math.isfinite(v) for v in values) or min(length,distance,period)<=0 or rise<0 or fall-rise<=period:raise ValueError("resolved pulse and finite positive geometry/sample period required")
    point=fall+distance*(fall-rise)/length
    radius=(1+distance/length)*period
    return {"point_s":point,"radius_s":radius,"interval_s":[max(fall,point-radius),point+radius],
            "assumptions":"constant physical speed; known aligned length; ideal point beams; each sampled edge no more than one period late"}


def audit(source,out):
    config_path=HERE/'configs/reconfigurable_cell_20261030.json';model_path=HERE/'models/eta_residual_v1.json';settings_path=HERE/'models/eta_monitor_v1.json'
    c=load_config(config_path);model=json.loads(model_path.read_text());settings=json.loads(settings_path.read_text());g=c['geometry']
    length=g['product_size_m'][1];distance=g['ps_y_m']['ps2']-g['ps_y_m']['ps1']-length;period=c['timing']['physics_step_s']*c['timing']['sample_steps']
    out.mkdir(parents=True,exist_ok=False);manifest={'source_sha256':digest(Path(__file__)),'config_sha256':digest(config_path),'model_sha256':digest(model_path),'settings_sha256':digest(settings_path),'inputs':{}}
    results=[]
    for i in range(12):
        folder=source/f'condition_{i:02}_none'
        obs,commands,truth=(rows(folder/n) for n in ['observations.jsonl','issued_commands.jsonl','evaluator_only.jsonl'])
        if not len(obs)==len(commands)==len(truth):raise ValueError('aligned evaluator records required')
        for o,cmd,t in zip(obs,commands,truth):
            if not o['source_time_s']==cmd['time_s']==t['time_s']:raise ValueError('aligned source clocks required')
        for name in ['observations.jsonl','issued_commands.jsonl','evaluator_only.jsonl']:manifest['inputs'][folder.name+'/'+name]=digest(folder/name)
        record={'id':folder.name,'initial_upstream_active':obs[0]['values']['ps1'],'status':'initial_pulse_unresolved'}
        if not record['initial_upstream_active']:
            rise=next(k for k in range(1,len(obs)) if obs[k-1]['values']['ps1'] is False and obs[k]['values']['ps1'] is True)
            fall=next(k for k in range(rise+1,len(obs)) if obs[k-1]['values']['ps1'] is True and obs[k]['values']['ps1'] is False)
            target=next(k for k in range(fall,len(obs)) if obs[k]['values']['ps2'] is True)
            t=lambda k:obs[k]['source_time_s'];y=lambda k:truth[k]['product_xyz_m'][1]
            window=sampling_window(t(rise),t(fall),length,distance,period)
            corrected=max(t(fall),window['point_s']+model['constant_bias_s'])
            pulse_speed=(y(fall)-y(rise))/(t(fall)-t(rise));remaining_speed=(y(target)-y(fall))/(t(target)-t(fall))
            record.update(status='resolved_pulse_audited',sampling_window=window,pulse_duration_s=t(fall)-t(rise),target_source_s=t(target),raw_residual_s=t(target)-window['point_s'],constant_residual_s=t(target)-corrected,
                          sampling_only_covered=window['interval_s'][0]-1e-9<=t(target)<=window['interval_s'][1]+1e-9,
                          frozen_constant_envelope_covered=abs(t(target)-corrected)<=settings['radii_s']['constant']+1e-9,
                          evaluator_pulse_mean_speed_m_s=pulse_speed,evaluator_remaining_mean_speed_m_s=remaining_speed,
                          evaluator_relative_speed_increase=remaining_speed/pulse_speed-1,
                          evaluator_pulse_displacement_m=y(fall)-y(rise),evaluator_remaining_displacement_m=y(target)-y(fall))
        results.append(record)
    eligible=[v for v in results if v['status']=='resolved_pulse_audited'];increases=[v['evaluator_relative_speed_increase'] for v in eligible]
    report={'analysis_kind':'posthoc_diagnostic_on_observed_data','normal_records':12,'resolved_pulses':len(eligible),'initially_occupied':sum(v['initial_upstream_active'] for v in results),
            'sampling_only_covered':sum(v['sampling_only_covered'] for v in eligible),'frozen_constant_envelope_covered':sum(v['frozen_constant_envelope_covered'] for v in eligible),
            'remaining_mean_speed_higher':sum(v['evaluator_remaining_mean_speed_m_s']>v['evaluator_pulse_mean_speed_m_s'] for v in eligible),
            'relative_mean_speed_increase_range': [min(increases),max(increases)],'sampling_radius_s':(1+distance/length)*period,'records':results,
            'scope':'Analytical bound requires constant speed and ideal known geometry; violations diagnose assumption failure, not a calibrated new predictor. Evaluator pose used only to inspect motion averages. No tuning, no new independent validation or physical evidence.'}
    save(out/'manifest.json',manifest);save(out/'results.json',report);print(json.dumps({k:v for k,v in report.items() if k!='records'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.source,a.output)
