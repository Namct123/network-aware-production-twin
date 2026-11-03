"""Generate manuscript tables from the versioned evidence; audit citations and blanks."""
import csv
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def prepare():
    evidence=ROOT/'docker/evidence/candidate-20261102-qualification.json'
    data=json.loads(evidence.read_text(encoding='utf-8'))
    result=data['qualification']; groups=result['benchmark_groups']
    assert result['completed_runs']==result['planned_runs']==24
    assert not result['physical_validation'] and result['parameter_tuning'] is False
    done=sum(g['done'] for g in result['groups']); hold=sum(g['hold'] for g in result['groups'])
    assert done+hold==24 and result['verification_failures']==0
    numeric=next(g for g in groups if g['backend']=='numeric_1d' and g['budget_kind']=='configured')
    physics=next(g for g in groups if g['backend']=='mujoco_belt' and g['budget_kind']=='functional')
    assert all(g['samples']==15 for g in groups)
    output=HERE/'generated'; output.mkdir(exist_ok=True)
    (HERE/'evidence').mkdir(exist_ok=True)
    (HERE/'evidence/qualification_20261102.json').write_bytes(evidence.read_bytes())
    log=ROOT/'output/docker/qualification_20261102_review/tests.log'
    saved_log=HERE/'evidence/logic_checks.txt'
    if log.exists():saved_log.write_text(log.read_text(encoding='utf-8'),encoding='utf-8')
    count=int(re.search(r'Ran (\d+) tests',saved_log.read_text(encoding='utf-8'))[1])
    values={'StudyRuns':24,'DoneCount':done,'HoldCount':hold,'LogicTests':count,
            'NumericPninetyfive':f"{numeric['p95_ms']:.2f}",'PhysicsPninetyfive':f"{physics['p95_ms']:.2f}"}
    (output/'values.tex').write_text(''.join('\\newcommand{\\'+key+'}{'+str(value)+'}\n' for key,value in values.items()),encoding='utf-8')
    lines=[r'\begin{table}[t]',r'\caption{Observed Docker forecast timing; 15 measured calls per row after warm-up}',
           r'\label{tab:timing}',r'\centering\small',r'\begin{tabular}{llrrrr}',r'\toprule',
           r'Model & Allowance & Median & p95 & Complete & Overruns\\',r' & (ms) & (ms) & (ms) & /15 & /15\\',r'\midrule']
    for g in groups:
        label='Reduced 1D' if g['backend']=='numeric_1d' else 'MuJoCo contact'
        budget=20 if g['budget_kind']=='configured' else 1000
        lines.append(f"{label} & {budget} & {g['median_ms']:.2f} & {g['p95_ms']:.2f} & {g['complete']} & {g['deadline_misses']}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (output/'timing_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines=[r'\begin{table}[t]',r'\caption{Matched reconfiguration-module study: completion (D) and supported hold (H)}',
           r'\label{tab:study}',r'\centering\small',r'\begin{tabular}{lrrrr}',r'\toprule',
           r'Condition & Off: D & Off: H & On: D & On: H\\',r'\midrule']
    titles={'nominal':'Nominal','pickup_missing':'Pickup sensor stuck low','delay20':'Delay: 20 ms',
            'loss5':r'Loss: 5\%','plant_slow':'Plant speed: 0.85 command','plant_fast':'Plant speed: 1.15 command'}
    for key,title in titles.items():
        a=next(g for g in result['groups'] if g['scenario']==key and g['policy']=='disabled')
        b=next(g for g in result['groups'] if g['scenario']==key and g['policy']=='enabled')
        lines.append(f"{title} & {a['done']} & {a['hold']} & {b['done']} & {b['hold']}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (output/'study_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    native_path=ROOT/'docker/evidence/candidate-20261103-native-physics.json'
    native_evidence=json.loads(native_path.read_text(encoding='utf-8'))
    native=native_evidence['optimization']
    assert native['equivalence_failures']==0 and native['equivalence_cases']==12
    assert native['physical_validation'] is False
    (HERE/'evidence/native_20261103.json').write_bytes(native_path.read_bytes())
    native_groups=native['benchmark_groups']
    lines=[r'\begin{table}[t]',r'\caption{Native rollout observations on 3 November: full-call median and p95 use the 1 s allowance; each count is out of 15 measured calls}',
           r'\label{tab:native}',r'\centering\small',r'\begin{tabular}{lrrrr}',r'\toprule',
           r'Implementation & Median & p95 & Complete & Complete\\',r' & (ms) & (ms) & at 20 ms & at 1 s\\',r'\midrule']
    for backend,label in [('physics_reference','Reference loop'),('physics_native_t1','Native: 1 worker'),('physics_native_t4','Native: 4 workers'),('physics_native_t8','Native: 8 workers')]:
        full=next(g for g in native_groups if g['backend']==backend and g['budget_kind']=='functional')
        deadline=next(g for g in native_groups if g['backend']==backend and g['budget_kind']=='configured')
        lines.append(f"{label} & {full['median_ms']:.2f} & {full['p95_ms']:.2f} & {deadline['complete']} & {full['complete']}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (output/'native_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    background_path=ROOT/'docker/evidence/candidate-20261103-background-observer.json'
    background_evidence=json.loads(background_path.read_text(encoding='utf-8'))
    background=background_evidence['background_observer']
    assert background['passed'] and not background['physical_validation'] and not background['control_applied']
    assert all(background['checks'].values())
    (HERE/'evidence/background_20261103.json').write_bytes(background_path.read_bytes())
    lines=[r'\begin{table}[t]',r'\caption{Paced observation-only Docker cycles on 3 November; foreground runtime-call timing, not end-to-end latency}',
           r'\label{tab:background}',r'\centering\small',r'\begin{tabular}{lrrrrr}',r'\toprule',
           r'Condition & Steps & Median & p95 & Maximum & Over 20 ms\\',r' & & (ms) & (ms) & (ms) & (steps)\\',r'\midrule']
    for key,label in [('baseline','Disabled'),('observer','Observation only'),('incomplete_worker','Incomplete worker')]:
        g=background['latency'][key]
        lines.append(f"{label} & {g['samples']} & {g['median_ms']:.2f} & {g['p95_ms']:.2f} & {g['max_ms']:.2f} & {g['observed_over_20ms']}"+r'\\')
    observer=background['summaries']['observer']['background_forecast']
    missing=background['summaries']['incomplete_worker']['background_forecast']['discard_reasons']['prediction_incomplete']
    lines += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip\footnotesize '+f"Observation-only cycle: {observer['submitted']} requests, {observer['accepted_observations']} admitted observations, {observer['discarded']} discarded. Incomplete-worker cycle: {missing} incomplete forecasts rejected.",r'\end{table}']
    (output/'background_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    boundary_path=ROOT/'docker/evidence/candidate-20261103-boundary-study.json'
    boundary_evidence=json.loads(boundary_path.read_text(encoding='utf-8'))
    boundary=boundary_evidence['boundary']
    assert boundary['planned']==boundary['recorded']==boundary['complete']==144
    assert boundary['invariant_failures']==0 and not boundary['parameter_tuning'] and not boundary['physical_validation']
    lines=[r'\begin{table}[t]',r'\caption{Fixed exploratory boundary grid: disagreement of reduced and forward-contact actions; complete inputs per row, not production trials}',
           r'\label{tab:boundary}',r'\centering\small',r'\begin{tabular}{rrrrr}',r'\toprule',
           r'Friction scale & Age (ms) & Complete & Reduced C / contact H & Reduced H / contact C\\',r'\midrule']
    for g in boundary['groups']:
        o=g['forward_decision_pairs']
        lines.append(f"{g['sliding_friction_scale']} & {g['age_s']*1000:.0f} & {g['complete']}/{g['planned']} & {o.get('reduced_continue_contact_hold',0)} & {o.get('reduced_hold_contact_continue',0)}"+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\par\smallskip\footnotesize C: continue; H: hold. Full-contact and forward-only actions coincide on this grid.',r'\end{table}']
    (output/'boundary_table.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    abstract=(HERE/'title_abstract.tex').read_text(encoding='utf-8')
    words=re.search(r'\\begin\{abstract\}(.*?)\\keywords',abstract,re.S)[1].split()
    assert 150<=len(words)<=250, len(words)
    body=(HERE/'body.tex').read_text(encoding='utf-8')
    physical=body.split(r'\section{Physical Validation}')[1].split(r'\section{Discussion')[0]
    assert not re.search(r'\d|\\input',physical.replace(r'\vspace{12mm}',''))
    text=abstract+body
    keys={key for group in re.findall(r'\\cite\{([^}]+)\}',text) for key in group.split(',')}
    refs=set(re.findall(r'\\bibitem\{([^}]+)\}',(HERE/'references_list.tex').read_text(encoding='utf-8')))
    assert keys==refs,(keys,refs)
    assert not {'SoftwareArtifact','MuJoCoRollout'}.intersection(refs)
    literature_path=HERE/'evidence/literature_sources_20261103.json'
    literature=json.loads(literature_path.read_text(encoding='utf-8'))
    metadata_path=HERE/'evidence/literature_metadata_20261103.json'
    metadata=json.loads(metadata_path.read_text(encoding='utf-8'))
    dois={record['DOI'].lower() for record in metadata['records']}
    assert all(source['key'] in refs and source['doi'].lower() in dois for source in literature['sources'].values())
    assert r'\author{\mbox{}}' in abstract and r'\institute{\mbox{}}' in abstract
    sources={'E001':[evidence],'E002':[ROOT/'mujoco'/name for name in ['runtime.py','estimator.py','predictor.py','physics_predictor.py','sequence.py','reconfiguration.py','check_robustness.py','qualify.py']],
             'E003':[ROOT/'mujoco/configs/reconfigurable_cell_20261030.json',ROOT/'mujoco/experiments/qualification_20261102.json'],
             'E004':[native_path,ROOT/'mujoco/check_physics_optimization.py'],
             'E005':[background_path,ROOT/'mujoco/background_forecast.py',ROOT/'mujoco/check_background.py',ROOT/'mujoco/configs/background_observer_20261103.json'],
             'E006':[ROOT/'docker/evidence/candidate-20261103-model-audit.json',ROOT/'mujoco/audit_background.py',ROOT/'mujoco/test_background_audit.py'],
             'E007':[boundary_path,ROOT/'mujoco/study_model_boundary.py',ROOT/'mujoco/experiments/model_boundary_20261103.json']}
    manifest={'prepared_on':'2026-11-03','status':'working_draft_human_verification_pending','physical_evidence':None,
        'baseline_artifact_commit':'93d60ca','native_candidate_image':native_evidence['image_id'],
        'background_candidate_image':background_evidence['image_id'],'author_approval':False,
        'literature_sources':literature['sources'],
        'literature_records':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [literature_path,metadata_path]],
        'sources':{key:[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths] for key,paths in sources.items()}}
    (HERE/'evidence/source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    claims=[]
    for name in ['title_abstract.tex','body.tex']:
        content=(HERE/name).read_text(encoding='utf-8')
        markers=list(re.finditer(r'% \[claim:(C\d+)\] \[evidence:([^\]]+)\]',content))
        for index,marker in enumerate(markers):
            block=content[marker.end():markers[index+1].start() if index+1<len(markers) else len(content)]
            normalized=' '.join(block.split())
            claims.append({'claim_id':marker[1],'file':name,'evidence_ids':marker[2],
                           'block_sha256':hashlib.sha256(normalized.encode()).hexdigest(),'human_verification':'pending'})
    with (HERE/'evidence/claims.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(claims[0]));w.writeheader();w.writerows(claims)
    audit={'abstract_words':len(words),'citations':sorted(keys),'reference_count':len(refs),'new_published_papers':6,'removed_nonpaper_references':['SoftwareArtifact','MuJoCoRollout'],'physical_result_values':0,'authors_unfilled':True,
           'study_runs':24,'done':done,'hold':hold,'logic_checks':count,'human_verification':'pending','submission_ready':False}
    (HERE/'evidence/audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit),flush=True)
    return audit

if __name__=='__main__':prepare()
