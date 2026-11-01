"""Configurable paired simulation study; failures are retained, never relabeled as success."""
import argparse
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import re
import traceback
from calibrate import set_value
from config import exact_keys,load_config,number,validate_config
from experiment import run,write_json

HERE=Path(__file__).parent
POLICIES=('disabled','enabled','adaptive')
# Plant variations deliberately do not change estimator parameters with them.
PATCHES={'network.delay_s','network.jitter_s','network.drop_probability',
         'plant.belt_speed_scale.long','plant.product_mass_kg','plant.vacuum_adhesion_n'}
FAULTS={'none','ps1_stuck_low','ps2_stuck_low','ps1_stuck_high','ps2_stuck_high',
        'transfer_present_stuck_low','transfer_present_stuck_high','a1_extended_stuck_low'}

def prepare(base,plan):
    exact_keys(plan,('schema_version','name','seeds','compute_budget_s','scenarios',*(['policies'] if 'policies' in plan else [])),'experiment plan')
    if type(plan['schema_version']) is not int or plan['schema_version']!=1: raise ValueError('unsupported plan schema')
    if not isinstance(plan['name'],str) or not plan['name']: raise ValueError('plan name required')
    number(plan['compute_budget_s'],'compute_budget_s',0,True)
    seeds=plan['seeds']
    policies=plan.get('policies',['disabled','enabled'])
    if (not isinstance(policies,list) or not 2<=len(policies)<=3 or any(p not in POLICIES for p in policies)
        or len(set(policies))!=len(policies) or policies[0]!='disabled'):
        raise ValueError('policies must start with disabled and contain 2..3 distinct supported policies')
    if (not isinstance(seeds,list) or not 1<=len(seeds)<=20 or
        any(type(s) is not int or s<0 for s in seeds) or len(set(seeds))!=len(seeds)):
        raise ValueError('1..20 distinct nonnegative seeds required')
    scenarios=plan['scenarios']
    if not isinstance(scenarios,list) or not scenarios or len(scenarios)*len(seeds)*len(policies)>200:
        raise ValueError('plan must contain 1..200 paired runs')
    jobs=[]; names=set()
    for item in scenarios:
        exact_keys(item,('name','patch','fault','fault_start_s'),'scenario')
        name=item['name']
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}',name) or name in names:
            raise ValueError('unique safe scenario name required')
        names.add(name)
        if not isinstance(item['patch'],dict) or not item['patch'].keys()<=PATCHES:
            raise ValueError('unsupported experimental parameter path')
        if item['fault'] not in FAULTS: raise ValueError('unsupported injected fault')
        number(item['fault_start_s'],'fault_start_s',0)
        for seed in seeds:
            for policy in policies:
                c=deepcopy(base)
                if not c.get('reconfiguration',{}).get('enabled'):
                    raise ValueError('study base must enable reconfiguration')
                c['reconfiguration']['enabled']=policy!='disabled'
                adaptive=c['reconfiguration'].get('adaptive')
                if policy=='adaptive' and not adaptive: raise ValueError('adaptive policy requires adaptive settings in base profile')
                if adaptive is not None: adaptive['enabled']=policy=='adaptive'
                c['prediction']['wall_budget_s']=plan['compute_budget_s']
                c['network']['seed']=seed
                for path,value in item['patch'].items(): set_value(c,path,value)
                validate_config(c)  # Validate every job before creating any experiment output.
                if item['fault_start_s']>=c['timing']['run_budget_s']: raise ValueError('fault onset outside run budget')
                jobs.append({'id':f'{name}_s{seed}_{policy}','scenario':name,'seed':seed,'policy':policy,
                             'fault':item['fault'],'fault_start_s':item['fault_start_s'],'config':c})
    return jobs

def assess(summary,policy_rows,enabled,cap,adaptive=False):
    state=summary['controller_state']
    supported=(state=='DONE' and summary['placement_pass_evaluator_only'] is True) or (
        state=='HOLD' and summary['hold_product_supported_evaluator_only'] is True)
    cap_ok=all(r['selected_long_speed_m_s']<=(r['latched_cap_m_s'] if adaptive else cap)+1e-12 for r in policy_rows
               if r['mode']=='DEGRADED' and r['phase']=='TRACK')
    if adaptive:
        caps=[r['latched_cap_m_s'] for r in policy_rows]
        cap_ok=cap_ok and all(b<=a+1e-12 for a,b in zip(caps,caps[1:]))
    # A disabled policy is expected to produce no policy rows.
    log_ok=bool(policy_rows) if enabled else not policy_rows
    return {'terminal_support_or_placement_pass':supported,'speed_cap_pass':cap_ok,
            'policy_logging_pass':log_ok,'verification_pass':supported and cap_ok and log_ok}

def error_coverage(truth_rows,decisions):
    if len(truth_rows)!=len(decisions): raise ValueError('unaligned evaluation logs')
    samples=covered=0; excess=0.0
    for truth,decision in zip(truth_rows,decisions):
        if truth['sequence']!=decision['sequence']: raise ValueError('unaligned evaluation sequence')
        error=truth['y_estimation_error_m']
        bound=decision['estimate']['uncertainty_m']
        if error is None or bound is None: continue
        samples+=1; covered+=int(abs(error)<=bound+1e-12)
        excess=max(excess,abs(error)-bound)
    return {'error_bound_samples':samples,'error_bound_samples_within':covered,
            'error_bound_max_excess_m':excess,'error_bound_observed_coverage':covered/samples if samples else None}

def aggregate(results):
    groups=[]
    for scenario in dict.fromkeys(r['scenario'] for r in results):
        for policy in [p for p in POLICIES if any(r['policy']==p for r in results)]:
            rows=[r for r in results if r['scenario']==scenario and r['policy']==policy]
            done=[r['simulation_time_s'] for r in rows if r.get('controller_state')=='DONE']
            groups.append({'scenario':scenario,'policy':policy,'runs':len(rows),
                'done':len(done),'hold':sum(r.get('controller_state')=='HOLD' for r in rows),
                'exceptions':sum('exception' in r for r in rows),
                'verification_failures':sum(not r['verification_pass'] for r in rows),
                'mean_completed_cycle_s':sum(done)/len(done) if done else None,
                'error_bound_samples':sum(r.get('error_bound_samples',0) for r in rows),
                'error_bound_samples_within':sum(r.get('error_bound_samples_within',0) for r in rows),
                'hold_without_injected_sensor_fault':sum(r.get('controller_state')=='HOLD' and r['fault']=='none' for r in rows)})
    return groups

def save_report(output,results,jobs,plan):
    groups=aggregate(results)
    pairs=[]
    by={(r['scenario'],r['seed'],r['policy']):r for r in results}
    for r in results:
        if r['policy']=='disabled': continue
        references=['disabled'] if r['policy']=='enabled' else ['disabled','enabled']
        for reference in references:
            b=by.get((r['scenario'],r['seed'],reference))
            if b is None: continue
            both_done=r.get('controller_state')==b.get('controller_state')=='DONE'
            both_hold=r.get('controller_state')==b.get('controller_state')=='HOLD'
            pairs.append({'scenario':r['scenario'],'seed':r['seed'],'policy':r['policy'],'reference_policy':reference,
                'reference_state':b.get('controller_state','EXCEPTION'),'policy_state':r.get('controller_state','EXCEPTION'),
                'both_verification_pass':r['verification_pass'] and b['verification_pass'],
                'cycle_difference_policy_minus_reference_s':r['simulation_time_s']-b['simulation_time_s'] if both_done else None,
                'earlier_hold_policy_s':b['hold_time_s']-r['hold_time_s'] if both_hold else None})
    report={'plan_name':plan['name'],'planned_runs':len(jobs),'completed_runs':len(results),
        'verification_failures':sum(not r['verification_pass'] for r in results),'groups':groups,'pairs':pairs,
        'scope':'descriptive finite-fixture simulation study; shared clock and open-loop XY/vacuum assumptions; not measured fault accuracy, independent trials, physical safety or realtime qualification'}
    write_json(output/'results.json',results); write_json(output/'report.json',report)
    with (output/'groups.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(groups[0]) if groups else ['scenario']); writer.writeheader(); writer.writerows(groups)
    lines=['# Ma trận kiểm chứng mô phỏng Digital Twin','',
        f"Kế hoạch: {plan['name']}. Đã chạy {len(results)}/{len(jobs)}; vi phạm tiêu chí: {report['verification_failures']}.",'',
        f"Budget tính predictor: {plan['compute_budget_s']} s. Đây là kiểm tra chức năng, không bảo đảm deadline 20 ms.",'',
        '| Kịch bản | Chính sách | Lượt | DONE | HOLD | Exception | Vi phạm | Chu kỳ trung bình chỉ DONE (s) |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for g in groups:
        mean='—' if g['mean_completed_cycle_s'] is None else f"{g['mean_completed_cycle_s']:.3f}"
        lines.append(f"| {g['scenario']} | {g['policy']} | {g['runs']} | {g['done']} | {g['hold']} | {g['exceptions']} | {g['verification_failures']} | {mean} |")
    lines+=['','HOLD không có lỗi cảm biến chủ động gây ra không đồng nghĩa HOLD nhầm: mạng và bất định vẫn có thể đòi hỏi dừng.',
        'Các seed dùng cùng kế hoạch mạng khi so cặp; chu trình khác nhau làm số mẫu và lịch nhận khác nhau. Trường hợp mạng tất định không trở thành các thử nghiệm độc lập chỉ vì đổi seed.',
        'Không tính chênh lệch chu kỳ giữa DONE và HOLD. Thời gian HOLD sớm hơn chỉ là thời điểm phản ứng, không phải dự đoán trước lỗi.',
        'Vi phạm tiêu chí hỗ trợ/đặt phôi là kết quả cần điều tra, không bị xóa hoặc đổi thành PASS. Đọc từng summary/ground_truth và effective_config.',
        'groups.csv ghi số mẫu sai số nằm trong biên bất định. Các mẫu tương quan và biên chưa hiệu chuẩn; coverage quan sát không phải xác suất bảo đảm hay tiêu chí PASS của lượt.',
        'Các tổng kết chỉ mô tả ma trận hữu hạn này, không suy ra độ chính xác phát hiện hoặc an toàn máy thật.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    return report

def check(output,base,plan):
    jobs=prepare(base,plan)
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    write_json(output/'plan.json',plan); write_json(output/'base_config.json',base)
    write_json(output/'study_manifest.json',{'plan_sha256':hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),
        'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'planned_runs':len(jobs)})
    results=[]
    for job in jobs:
        row={k:job[k] for k in ('id','scenario','seed','policy','fault','fault_start_s')}
        try:
            summary=run(output/job['id'],config=job['config'],assume_open_loop=True,
                        fault=job['fault'],fault_start_s=job['fault_start_s'])
            rows=[json.loads(s) for s in (output/job['id']/'reconfiguration.jsonl').read_text().splitlines()]
            row.update(summary)
            row.update(assess(summary,rows,job['policy']!='disabled',job['config']['reconfiguration']['degraded_long_speed_m_s'],adaptive=job['policy']=='adaptive'))
            truth=[json.loads(s) for s in (output/job['id']/'ground_truth.jsonl').read_text().splitlines()]
            decisions=[json.loads(s) for s in (output/job['id']/'controller.jsonl').read_text().splitlines()]
            row.update(error_coverage(truth,decisions))
        except Exception as error:
            row.update(exception=f'{type(error).__name__}: {error}',verification_pass=False)
            (output/(job['id']+'_error.txt')).write_text(traceback.format_exc(),encoding='utf-8')
        results.append(row)
        save_report(output,results,jobs,plan)
        print(f"{len(results)}/{len(jobs)} {job['id']}: {'PASS' if row['verification_pass'] else 'FAIL'}; {row.get('controller_state','EXCEPTION')}; {row.get('hold_reason',row.get('exception',''))}",flush=True)
    report=save_report(output,results,jobs,plan)
    print(f"STUDY: {report['completed_runs']}/{report['planned_runs']}; verification_failures={report['verification_failures']}",flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    p.add_argument('--plan',type=Path,default=HERE/'experiments/robustness_20261031.json')
    a=p.parse_args(); report=check(a.output,load_config(a.config),json.loads(a.plan.read_text(encoding='utf-8-sig')))
    raise SystemExit(int(report['verification_failures']>0))
