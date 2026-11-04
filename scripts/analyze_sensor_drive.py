"""Independent interpretation of sensor/drive study logs; never feeds the DT."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'mujoco'))
from evaluation import Evaluator
from study_sensor_drive import pair


def analyze(folder,output):
    folder=Path(folder).resolve();output=Path(output)
    if output.exists():raise FileExistsError('choose a new interpretation file')
    report=json.loads((folder/'sensor_drive_study.json').read_text(encoding='utf-8'))
    mapping={'feed_sensor_missing':('transfer_present','physical_transfer_present'),
        'pickup_sensor_missing':('ps2','physical_ps2'),'pickup_sensor_high':('ps2','physical_ps2'),
        'upstream_sensor_missing':('ps1','physical_ps1')}
    results=[];hashes={}
    for trial in report['trials']:
        base=(folder/trial['name']).resolve()
        if not base.is_relative_to(folder):raise ValueError('unsafe trial path')
        def read(name):
            p=base/name;data=p.read_bytes();hashes[trial['name']+'/'+name]=hashlib.sha256(data).hexdigest();return data.decode('utf-8')
        obs=[json.loads(s) for s in read('observations.jsonl').splitlines()]
        truth=[json.loads(s) for s in read('truth_evaluator_only.jsonl').splitlines()]
        config=json.loads(read('effective_config.json'))
        if len(obs)!=len(truth) or len(obs)!=trial['ticks']:raise ValueError('unaligned row counts')
        first=None
        keys=mapping.get(trial['case'])
        for observed,physical in zip(obs,truth):
            if observed['received_time_s']!=physical['time_s']:raise ValueError('unaligned evaluator timestamps')
            if keys and first is None and trial['onset_s'] is not None and physical['time_s']>=trial['onset_s'] and observed['values'][keys[0]]!=physical[keys[1]]:
                first=physical['time_s']
        hold=trial['first_hold']['time_s'] if trial['first_hold'] else None
        assessment=Evaluator(config['geometry']).finish(truth[-1],trial['controller_state'],1)
        results.append({'name':trial['name'],'case':trial['case'],'onset_s':trial['onset_s'],
            'first_hidden_sensor_disagreement_s':first,
            'hold_after_hidden_disagreement_ms':1000*(hold-first) if hold is not None and first is not None else None,
            'hold_after_fixture_onset_ms':trial['hold_delay_ms'],**assessment})
    comparisons=[]
    for previous in report['pairs']:
        current=pair(folder,previous['left'],previous['right'])
        if current!=previous:raise ValueError('pair report differs from recomputed trace')
        comparisons.append(current)
    result={'kind':'sensor_drive_interpretation_v1','passed':True,'trial_count':len(results),'trials':results,'pairs':comparisons,
        'input_sha256':hashes,'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'evaluation_source_sha256':hashlib.sha256((ROOT/'mujoco/evaluation.py').read_bytes()).hexdigest(),
        'scope':'hidden disagreement time is evaluator-only, not a timestamp the core can observe; position support is not a physical safety certificate',
        'physical_validation':False,'physical_output':False}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=analyze(a.input,a.output)
    print(json.dumps({'passed':r['passed'],'trials':r['trial_count'],'pair_reports_recomputed':len(r['pairs'])}))
