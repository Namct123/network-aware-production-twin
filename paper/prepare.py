"""Build only focused monitoring tables and bind current manuscript claims to evidence."""
import csv
import hashlib
import json
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def prepare():
    output=HERE/'generated';output.mkdir(exist_ok=True)
    (HERE/'evidence').mkdir(exist_ok=True)
    ml_path=ROOT/'docker/evidence/candidate-20261106-eta-ml-v2.json'
    ml_evidence=json.loads(ml_path.read_text(encoding='utf-8'))
    ml=ml_evidence['study']
    assert ml['ml_trained'] and not ml['physical_validation']
    assert [ml['splits'][n]['n'] for n in ['train','validation','calibration','test','shift']]==[32,8,8,9,4]
    recordings=ml['input_sha256']; distinct={}; seen=set()
    for split in ['train','validation','calibration','test','shift']:
        pairs={(h,recordings[name.replace('observations.jsonl','issued_commands.jsonl')]) for name,h in recordings.items() if name.startswith(split+'_') and name.endswith('observations.jsonl')}
        assert not seen.intersection(pairs), 'recording overlap across ML splits'
        seen.update(pairs); distinct[split]=len(pairs)
    assert list(distinct.values())==[16,4,4,9,4]
    recording_audit=HERE/'evidence/eta_ml_recording_audit_20261106.json'
    recording_audit.write_text(json.dumps({'unique_recording_pairs':distinct,'cross_split_recording_overlap':False,'basis':'SHA256 pairs of admitted observations and issued commands from training receipt; duplicates are not independent repetitions'},indent=2)+'\n',encoding='utf-8')
    lines=[r'\begin{table}[t]',r'\caption{Sampled optical-edge arrival-time prediction: held-out normal test ($n=9$) and shifted conditions ($n=4$). MAE in ms; not physical timing accuracy.}',r'\label{tab:eta-ml}',r'\centering\small',r'\begin{tabular}{lrr}',r'\toprule',r'Method & Test MAE & Shift MAE\\',r'\midrule']
    for key,label in [('nominal','Nominal command kinematics'),('pulse','Upstream pulse kinematics'),('constant_bias','Pulse plus train-mean bias'),('ml','Pulse plus Ridge residual')]:
        lines.append(f"{label} & {ml['splits']['test']['mae_ms'][key]:.1f} & {ml['splits']['shift']['mae_ms'][key]:.1f}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip\footnotesize Constant-bias reference added after the initial pilot; its value uses training rows only.',r'\end{table}']
    (output/'eta_ml_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (HERE/'evidence/eta_ml_20261106.json').write_bytes(ml_path.read_bytes())
    monitor_path=ROOT/'docker/evidence/candidate-20261106-eta-monitor-v2.json'
    monitor_evidence=json.loads(monitor_path.read_text(encoding='utf-8'))
    mon=monitor_evidence['study']; assert mon['replays']==465 and mon['recordings']==31
    assert not mon['physical_validation'] and not mon['parameter_tuning'] and mon['identical_missing_stall_pairs']==9
    assert monitor_evidence['paired_immediate_comparison']['ml_earlier']==0
    bs=chr(92)
    lines=[bs+'begin{table}[t]',bs+'caption{Advisory ETA findings in fixed replay conditions; fault denominator combines nine missing-target and nine stalled-drive segments, which form nine identical input pairs.}',bs+'label{tab:eta-monitor}',bs+'centering'+bs+'small',bs+'begin{tabular}{lrrrr}',bs+'toprule','Method & Radius & Normal alerts & Fault alerts & Fault alerts'+bs*2,' & (ms) & no delay (/9) & no delay (/18) & 40 ms (/18)'+bs*2,bs+'midrule']
    for key,label in [('pulse','Pulse'),('constant','Constant bias'),('ml','Ridge')]:
        immediate=mon['groups']['immediate'][key]; delayed=mon['groups']['delay40ms'][key]
        fa=sum(immediate[n]['alerts'] for n in ['test_target_missing','test_drive_stall'])
        da=sum(delayed[n]['alerts'] for n in ['test_target_missing','test_drive_stall'])
        lines.append(f"{label} & {monitor_evidence['monitor_settings']['radii_s'][key]*1000:.1f} & {immediate['test_none']['alerts']} & {fa} & {da}"+bs*2)
    lines += [bs+'bottomrule',bs+'end{tabular}',bs+'par'+bs+'smallskip'+bs+'footnotesize Two delayed pulse replays end before a late-edge confirmation window. Data rejection and engineering fallback are not credited as learned-model detections.',bs+'end{table}']
    (output/'eta_monitor_table.tex').write_text(chr(10).join(lines)+chr(10),encoding='utf-8')
    (HERE/'evidence/eta_monitor_20261106.json').write_bytes(monitor_path.read_bytes())

    bs=chr(92)
    clock_path=ROOT/'docker/evidence/candidate-20261106-network-clock.json'
    clock_evidence=json.loads(clock_path.read_text(encoding='utf-8'));clock=clock_evidence['study']
    assert clock['recordings']==36 and clock['replays']==720 and not clock['parameter_tuning']
    initial_audit=HERE/'evidence/network_clock_initial_audit_20261106.json'
    assert json.loads(initial_audit.read_text())['initially_active_count']==6
    lines=[bs+'begin{table}[t]',bs+'caption{Fresh-condition clock ablation: normal finding counts and eligibility among 12 planned normal recordings. All rows use the same frozen constant correction.}',bs+'label{tab:clock}',bs+'centering'+bs+'small',bs+'begin{tabular}{rlrrr}',bs+'toprule','Delay & Age gate & Source findings & Receiver findings & Eligible'+bs*2,'(ms) & & (/12) & (/12) & (/12)'+bs*2,bs+'midrule']
    for case,gate,delay in [('immediate',True,0),('delay40ms',True,40),('delay80ms',True,80),('delay120ms',True,120),('delay120ms',False,120)]:
        suffix='age' if gate else 'no_age';left=clock['groups'][case]['source_'+suffix]['none'];right=clock['groups'][case]['receiver_'+suffix]['none']
        assert left['eligible_prediction_runs']==right['eligible_prediction_runs']
        lines.append(f"{delay} & {'On' if gate else 'Off'} & {left['findings']} & {right['findings']} & {left['eligible_prediction_runs']}"+bs*2)
    lines += [bs+'bottomrule',bs+'end{tabular}',bs+'par'+bs+'smallskip'+bs+'footnotesize Six recordings lack complete upstream pulses. The zero-finding target already fails without delay; zero eligible records under stale rejection is not healthy-process evidence.',bs+'end{table}']
    (output/'network_clock_table.tex').write_text(chr(10).join(lines)+chr(10),encoding='utf-8')
    pulse_audit_path=ROOT/'docker/evidence/candidate-20261106-pulse-model-audit.json'
    pulse_audit=json.loads(pulse_audit_path.read_text(encoding='utf-8'))
    assert pulse_audit['checks']['old61_model_results_unchanged'] and pulse_audit['audit']['resolved_pulses']==6
    abstract=(HERE/'title_abstract.tex').read_text(encoding='utf-8');body=(HERE/'body.tex').read_text(encoding='utf-8')
    words=re.search(re.escape(bs+'begin{abstract}')+'(.*?)'+re.escape(bs+'keywords'),abstract,re.S)[1].split()
    assert 150<=len(words)<=250,len(words)
    physical=body.split(bs+'section{Physical Validation}')[1].split(bs+'section{Conclusion}')[0]
    assert not re.search('[0-9]|'+re.escape(bs+'input'),physical.replace(bs+'vspace{8mm}',''))
    assert bs+'author{'+bs+'mbox{}}' in abstract and bs+'institute{'+bs+'mbox{}}' in abstract
    keys={key for group in re.findall(re.escape(bs+'cite{')+'([^}]+)'+re.escape('}'),abstract+body) for key in group.split(',')}
    refs=set(re.findall(re.escape(bs+'bibitem{')+'([^}]+)'+re.escape('}'),(HERE/'references_list.tex').read_text(encoding='utf-8')))
    assert keys==refs and len(refs)==14,(keys,refs)
    assert not {'SoftwareArtifact','MuJoCoRollout'}.intersection(refs)
    literature_files=[HERE/'evidence'/n for n in ['literature_sources_20261103.json','literature_metadata_20261103.json','literature_scope_20261106.json']]
    literature=json.loads(literature_files[0].read_text(encoding='utf-8'))['sources']
    literature.update(json.loads(literature_files[2].read_text(encoding='utf-8'))['sources'])
    assert all(source['key'] in refs for source in literature.values())
    focus_path=ROOT/'docker/evidence/candidate-20261106-monitoring-focus.json'
    focus=json.loads(focus_path.read_text(encoding='utf-8'))
    assert focus['checks']['465_full_decision_logs_identical'] and focus['source_allowlist_count']==32
    sources={'E003':[ROOT/'mujoco/configs/reconfigurable_cell_20261030.json'],
             'E009':[ml_path,ROOT/'docker/evidence/candidate-20261106-eta-ml.json',recording_audit,ROOT/'mujoco/eta_ml.py',ROOT/'mujoco/models/eta_residual_v1.json'],
             'E012':[monitor_path,ROOT/'mujoco/models/eta_monitor_v1.json',ROOT/'mujoco/experiments/eta_monitor_20261106.json'],
             'E013':[focus_path,ROOT/'mujoco/event_window.py',ROOT/'mujoco/eta_monitor.py',ROOT/'mujoco/test_eta_event_window.py'],
             'E014':[clock_path,initial_audit,ROOT/'mujoco/study_network_clock.py',ROOT/'mujoco/experiments/network_clock_ablation_20261106.json'],
             'E015':[pulse_audit_path,ROOT/'mujoco/audit_pulse_model.py',ROOT/'mujoco/test_eta_pulse_model.py',ROOT/'mujoco/eta_ml.py',ROOT/'research_scope.json']}
    manifest={'prepared_on':'2026-11-06','scope':'event_monitoring_focus_v1','status':'working_draft_human_verification_pending','physical_evidence':None,'author_approval':False,'historical_draft_commit':'7bbde4a',
              'literature_sources':literature,'literature_records':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in literature_files],
              'sources':{key:[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths] for key,paths in sources.items()}}
    (HERE/'evidence/source_manifest.json').write_text(json.dumps(manifest,indent=2)+chr(10),encoding='utf-8')
    claims=[]
    pattern=re.escape('% [claim:')+'(C[0-9]+)'+re.escape('] [evidence:')+'([^]]+)'+re.escape(']')
    for name in ['title_abstract.tex','body.tex']:
        content=(HERE/name).read_text(encoding='utf-8');markers=list(re.finditer(pattern,content))
        for index,marker in enumerate(markers):
            block=content[marker.end():markers[index+1].start() if index+1<len(markers) else len(content)]
            claims.append({'claim_id':marker[1],'file':name,'evidence_ids':marker[2],'block_sha256':hashlib.sha256(' '.join(block.split()).encode()).hexdigest(),'human_verification':'pending'})
    assert len(claims)==18
    with (HERE/'evidence/claims.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(claims[0]));w.writeheader();w.writerows(claims)
    audit={'scope':'event_monitoring_focus_v1','abstract_words':len(words),'reference_count':len(refs),'citations':sorted(keys),'claims':len(claims),'physical_result_values':0,'authors_unfilled':True,
           'ml_segments':61,'monitoring_recordings':31,'monitoring_replays':465,'distinct_physical_case_studies':0,'distinct_virtual_case_studies':1,'cross_machine_validation':False,
           'kernel_contract_tests_are_not_device_experiments':True,'runtime_source_allowlist_files':len(json.loads((ROOT/'research_scope.json').read_text())['runtime_files']),'network_ablation_recordings':36,'network_ablation_replays':720,'fresh_normal_finding_budget_met':False,'posthoc_sampling_audit':True,'sampling_bound_physical_guarantee':False,'human_verification':'pending','submission_ready':False}
    (HERE/'evidence/audit.json').write_text(json.dumps(audit,indent=2)+chr(10),encoding='utf-8')
    print(json.dumps(audit),flush=True);return audit

if __name__=='__main__':prepare()
