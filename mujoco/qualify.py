"""Reproducible timing and matched fault study; never changes the default policy."""
import argparse
from copy import deepcopy
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import time
from config import exact_keys,load_config,number
from estimator import Estimate
from predictor import Predictor
from check_robustness import prepare,check as study
from experiment import write_json

HERE=Path(__file__).resolve().parent

def validate(base,plan):
    exact_keys(plan,('schema_version','name','benchmark','study'),'qualification')
    if type(plan['schema_version']) is not int or plan['schema_version']!=1: raise ValueError('unsupported qualification schema')
    if not isinstance(plan['name'],str) or not plan['name']: raise ValueError('name required')
    b=plan['benchmark']; exact_keys(b,('repeats','warmup','functional_budget_s','cases'),'benchmark')
    for key,lo,hi in [('repeats',2,30),('warmup',0,5)]:
        if type(b[key]) is not int or not lo<=b[key]<=hi: raise ValueError('invalid '+key)
    number(b['functional_budget_s'],'functional budget',0,True)
    if b['functional_budget_s']<base['prediction']['wall_budget_s']: raise ValueError('functional budget must not shorten the configured deadline')
    if not isinstance(b['cases'],list) or not 1<=len(b['cases'])<=10: raise ValueError('1..10 benchmark cases required')
    names=set()
    for c in b['cases']:
        exact_keys(c,('name','position_fraction','speed_m_s','uncertainty_m','age_s'),'benchmark case')
        if not isinstance(c['name'],str) or not c['name'] or c['name'] in names: raise ValueError('distinct case names required')
        names.add(c['name'])
        for key in ('position_fraction','speed_m_s','uncertainty_m','age_s'): number(c[key],key,0)
        if c['position_fraction']>1: raise ValueError('position fraction outside belt')
    jobs=prepare(base,plan['study'])
    return jobs

def statistics(rows):
    groups=[]
    for backend,budget in dict.fromkeys((r['backend'],r['budget_kind']) for r in rows):
        selected=[r for r in rows if r['backend']==backend and r['budget_kind']==budget and r['phase']=='measured']
        elapsed=sorted(r['external_ms'] for r in selected)
        groups.append({'backend':backend,'budget_kind':budget,'samples':len(selected),
            'median_ms':(elapsed[(len(elapsed)-1)//2]+elapsed[len(elapsed)//2])/2,
            'p95_ms':elapsed[math.ceil(.95*len(elapsed))-1],'max_ms':elapsed[-1],
            'complete':sum(r['status']=='complete' for r in selected),
            'incomplete':sum(r['status']!='complete' for r in selected),
            'deadline_misses':sum(r['external_ms']>r['budget_ms'] for r in selected),
            'continue':sum(r['action']=='CONTINUE' for r in selected)})
    return groups

def benchmark(base,settings,output,factories=None):
    if factories is None:
        from physics_predictor import MuJoCoBeltPredictor
        factories={'numeric_1d':Predictor,'mujoco_belt':MuJoCoBeltPredictor}
    rows=[]; initialization=[]
    for backend,factory in factories.items():
        for kind,budget in [('configured',base['prediction']['wall_budget_s']),('functional',settings['functional_budget_s'])]:
            c=deepcopy(base); c['prediction']['wall_budget_s']=budget
            started=time.perf_counter(); predictor=factory(c)
            initialization.append({'backend':backend,'budget_kind':kind,'initialization_ms':1000*(time.perf_counter()-started)})
            for case in settings['cases']:
                a,b=base['geometry']['long_belt_y_m']
                estimate=Estimate(a+(b-a)*case['position_fraction'],case['speed_m_s'],case['uncertainty_m'],2,'tracking')
                for repeat in range(settings['warmup']+settings['repeats']):
                    started=time.perf_counter(); result=predictor.rollout(deepcopy(estimate),0,case['age_s'])
                    elapsed=1000*(time.perf_counter()-started)
                    rows.append({'backend':backend,'budget_kind':kind,'budget_ms':1000*budget,'case':case['name'],
                        'phase':'warmup' if repeat<settings['warmup'] else 'measured','repeat':repeat,
                        'external_ms':elapsed,'internal_ms':result['compute_ms'],'status':result['status'],'action':result['action'],
                        'completed_scenarios':result['completed_scenarios'],'expected_scenarios':result['expected_scenarios'],
                        'rollout_steps':result['rollout_steps'],'margins_m':result['margins_m']})
                    # Flush observations incrementally; interrupted runs retain their measurements.
                    with (output/'timing.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(rows[-1],allow_nan=False)+'\n')
    result={'groups':statistics(rows),'initialization':initialization,'rows':rows,
        'scope':'synthetic estimated states; measured-call times include wrapper overhead; initialization and warmup separate; not plant accuracy or worst-case timing proof'}
    write_json(output/'benchmark.json',result)
    with (output/'timing.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=[k for k in rows[0] if k!='margins_m']; writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader(); writer.writerows(rows)
    return result

def qualify(output,base,plan):
    jobs=validate(base,plan)  # All jobs checked before any output or experiment.
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    write_json(output/'plan.json',plan); write_json(output/'base_config.json',base)
    import mujoco,numpy
    write_json(output/'manifest.json',{'python':platform.python_version(),'platform':platform.platform(),
        'mujoco':mujoco.__version__,'numpy':numpy.__version__,'planned_study_runs':len(jobs),
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))},
        'plan_sha256':hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),
        'base_sha256':hashlib.sha256(json.dumps(base,sort_keys=True).encode()).hexdigest()})
    timing=benchmark(base,plan['benchmark'],output)
    print('Timing measurements saved; starting matched simulation study.',flush=True)
    compared=study(output/'study',base,plan['study'])
    report={'kind':'qualification_v1','phase':'completed','benchmark_groups':timing['groups'],
        'planned_runs':compared['planned_runs'],'completed_runs':compared['completed_runs'],
        'verification_failures':compared['verification_failures'],'groups':compared['groups'],
        'realtime_certified':False,'physical_validation':False,'parameter_tuning':False,'user_acceptance':'pending',
        'scope':'paired reconfiguration OFF versus fixed cap ON, not sequential PLC versus DT; benchmarks compare different model fidelity, not accuracy'}
    write_json(output/'qualification.json',report)
    lines=['# Đánh giá thời gian dự báo và phản ứng khi có lỗi','',
        'Đo cùng trạng thái ước lượng giả lập trên hai nhánh. Không lấy vị trí thật để chọn lệnh.',
        'Khởi tạo và các lượt làm nóng được ghi riêng; bảng này chỉ gồm lượt đo sau đó.',
        'Hạn “đang cấu hình” giữ nguyên hồ sơ; hạn “chức năng” chỉ giúp xem đủ kịch bản, không chứng minh tính kịp.',
        'p95 là mốc chứa 95% mẫu đã đo theo cách chọn thứ hạng; không phải thời gian lớn nhất bảo đảm.','',
        '| Nhánh | Hạn | Mẫu | Trung vị (ms) | p95 (ms) | Lớn nhất (ms) | Tính đủ | Quá hạn |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for g in timing['groups']:
        label='Tính 1 chiều' if g['backend']=='numeric_1d' else 'MuJoCo băng/phôi'
        kind='Đang cấu hình' if g['budget_kind']=='configured' else 'Chức năng'
        lines.append(f"| {label} | {kind} | {g['samples']} | {g['median_ms']:.3f} | {g['p95_ms']:.3f} | {g['max_ms']:.3f} | {g['complete']} | {g['deadline_misses']} |")
    lines+=['',f"Đối chứng mô phỏng: {compared['completed_runs']}/{compared['planned_runs']} lượt; vi phạm tiêu chí: {compared['verification_failures']}.",
        'So sánh bật/tắt giới hạn tốc độ tái cấu hình cố định, cùng hồ sơ và seed (mã tạo nhiễu). Không gọi đây là PLC tuần tự so với DT.',
        'Các lượt không đạt được giữ nguyên. HOLD là dừng chờ, không phải chu trình đã hoàn tất; không gọi mọi lượt dừng không có lỗi cảm biến là báo nhầm.',
        'Hai mô hình dự báo có mức chi tiết khác nhau; tốc độ tính không chứng minh độ chính xác vật lý. Chưa hiệu chuẩn hoặc chứng nhận thời gian thực.',
        'Không điều chỉnh ngưỡng, không chọn lại tham số theo kết quả trong lượt này. Xem study/report.md và từng hồ sơ để điều tra.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    p.add_argument('--plan',type=Path,default=HERE/'experiments/qualification_20261102.json')
    a=p.parse_args(); r=qualify(a.output,load_config(a.config),json.loads(a.plan.read_text(encoding='utf-8-sig')))
    print('Completed; findings retained:',r['verification_failures'],flush=True)
    raise SystemExit(int(r['verification_failures']>0))
