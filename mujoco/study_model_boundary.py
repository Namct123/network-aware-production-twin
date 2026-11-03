"""Exploratory fixed-grid model disagreement study; never tunes the controller."""
import argparse
from collections import Counter
from copy import deepcopy
import csv
import hashlib
from itertools import product
import json
from pathlib import Path
import platform
from config import exact_keys,load_config,number,validate_config
from estimator import Estimate
from predictor import Predictor

HERE=Path(__file__).resolve().parent
AXES=('distance_to_limit_m','speed_m_s','age_s','sliding_friction_scale')


def jobs(base,plan):
    exact_keys(plan,('schema_version','name',*AXES,'uncertainty_m','functional_budget_s','native_threads'),'model boundary plan')
    if type(plan['schema_version']) is not int or plan['schema_version']!=1:raise ValueError('unsupported boundary schema')
    if not isinstance(plan['name'],str) or not plan['name']:raise ValueError('name required')
    count=1
    for key in AXES:
        values=plan[key]
        if not isinstance(values,list) or not 1<=len(values)<=30:raise ValueError('1..30 entries per axis required')
        for value in values:number(value,key,None if key=='distance_to_limit_m' else 0,key=='sliding_friction_scale')
        if len(set(values))!=len(values):raise ValueError('duplicate grid entries')
        count*=len(values)
    if count>500:raise ValueError('boundary grid exceeds 500 input states')
    number(plan['uncertainty_m'],'uncertainty_m',0)
    number(plan['functional_budget_s'],'functional_budget_s',0,True)
    if not base['prediction']['wall_budget_s']<=plan['functional_budget_s']<=30:raise ValueError('invalid functional allowance')
    if type(plan['native_threads']) is not int or not 1<=plan['native_threads']<=16:raise ValueError('invalid native_threads')
    return [dict(zip(AXES,values)) for values in product(*(plan[key] for key in AXES))]


def variant(base,plan,scale):
    c=deepcopy(base);c['prediction']['wall_budget_s']=plan['functional_budget_s']
    c['prediction']['native_threads']=plan['native_threads']
    if 'background' in c['prediction']:c['prediction']['background']['enabled']=False
    for key in ('belt_friction','product_friction'):c['plant'][key][0]*=scale
    validate_config(c)
    return c


def summarize(rows,planned):
    complete=[r for r in rows if r.get('complete')]
    return {'planned':planned,'recorded':len(rows),'complete':len(complete),'incomplete_or_error':len(rows)-len(complete),
        'forward_decision_pairs':dict(Counter(r['forward_pair'] for r in complete)),
        'full_decision_pairs':dict(Counter(r['full_pair'] for r in complete)),
        'extra_constraints_change_action':sum(r['contact_forward']['action']!=r['contact_full']['action'] for r in complete),
        'invariant_failures':sum(r.get('invariant_failure',False) for r in rows),
        'forward_margin_difference_m':{'min':min((r['forward_margin_delta_m'] for r in complete),default=None),
                                       'max':max((r['forward_margin_delta_m'] for r in complete),default=None)}}


def pair(left,right):
    return 'agree' if left['action']==right['action'] else 'reduced_continue_contact_hold' if left['action']=='CONTINUE' else 'reduced_hold_contact_continue'


def run(output,base,plan):
    grid=jobs(base,plan)
    from physics_predictor import MuJoCoBeltPredictor
    import mujoco,numpy

    class ForwardOnly(MuJoCoBeltPredictor):
        # Diagnostic constraint ablation only; dynamics, states and timesteps unchanged.
        def _margins(self,states):return self.limit-states[...,2]
        def rollout(self,*args):
            result=super().rollout(*args)
            result['model']='diagnostic MuJoCo contact dynamics with forward-only margin; not a control policy'
            return result

    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    def write(name,data):(output/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    write('base_config.json',base);write('plan.json',plan)
    write('manifest.json',{'study_design':'fixed full-factorial exploratory simulation; no physical validation or parameter fitting',
        'python':platform.python_version(),'mujoco':mujoco.__version__,'numpy':numpy.__version__,
        'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('study_model_boundary.py','physics_predictor.py','predictor.py','config.py')},
        'base_config_sha256':hashlib.sha256(json.dumps(base,sort_keys=True).encode()).hexdigest(),
        'plan_sha256':hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()})
    models={}
    for scale in plan['sliding_friction_scale']:
        c=variant(base,plan,scale);write('effective_scale_'+str(scale)+'.json',c)
        models[scale]=(Predictor(c),ForwardOnly(c),MuJoCoBeltPredictor(c))
    rows=[]
    try:
        with (output/'cases.jsonl').open('w',encoding='utf-8') as log:
            for index,point in enumerate(grid):
                reduced,forward,full=models[point['sliding_friction_scale']]
                state=Estimate(reduced.limit-point['distance_to_limit_m'],point['speed_m_s'],plan['uncertainty_m'],2,'tracking')
                row={'case':index,**point,'estimate':state.as_dict(),'source_time_s':0,'decision_time_s':point['age_s'],'complete':False}
                try:
                    for name,model in [('reduced',reduced),('contact_forward',forward),('contact_full',full)]:
                        row[name]=model.rollout(state,0,point['age_s'])
                    row['complete']=all(row[k]['status']=='complete' and row[k]['completed_scenarios']==row[k]['expected_scenarios'] for k in ('reduced','contact_forward','contact_full'))
                    if row['complete']:
                        a,b,d=(row[k] for k in ('reduced','contact_forward','contact_full'))
                        row.update(forward_pair=pair(a,b),full_pair=pair(a,d),forward_margin_delta_m=b['margins_m']['CONTINUE']-a['margins_m']['CONTINUE'],
                            invariant_failure=any(d['margins_m'][p]>b['margins_m'][p]+1e-9 for p in ('HOLD','CONTINUE')))
                except Exception as error:row['error']=f'{type(error).__name__}: {error}'
                rows.append(row);log.write(json.dumps(row,allow_nan=False)+'\n');log.flush()
                if (index+1)%24==0:print(f'Boundary: {index+1}/{len(grid)}',flush=True)
                write('partial_summary.json',summarize(rows,len(grid)))
    finally:
        for reduced,forward,full in models.values():
            forward.engine.close();full.engine.close()
    result={'kind':'model_boundary_v1',**summarize(rows,len(grid)),
        'physical_validation':False,'parameter_tuning':False,'control_applied':False,'user_acceptance':'pending',
        'scope':'Exploratory fixed-grid model sensitivity; no independent production trials, diagnostic accuracy, or hard realtime guarantee.'}
    result['groups']=[{'sliding_friction_scale':scale,'age_s':age,**summarize([r for r in rows if r['sliding_friction_scale']==scale and r['age_s']==age],len(plan['distance_to_limit_m'])*len(plan['speed_m_s']))} for scale,age in product(plan['sliding_friction_scale'],plan['age_s'])]
    write('boundary.json',result)
    with (output/'cases.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['case',*AXES,'complete','1d_action','contact_y_action','contact_full_action','contact_y_minus_1d_margin_m'])
        for r in rows:w.writerow([r['case'],*(r[k] for k in AXES),r['complete'],*(r.get(k,{}).get('action') for k in ('reduced','contact_forward','contact_full')),r.get('forward_margin_delta_m')])
    lines=['# Khi nào mô hình 1D và MuJoCo khác nhau?','',
        f"Lưới cố định {result['planned']} đầu vào; ghi được {result['recorded']}; đủ cả ba cách tính {result['complete']}; thiếu/lỗi {result['incomplete_or_error']}.",
        f"Không thay hồ sơ điều khiển. Hạn {plan['functional_budget_s']} giây là hạn chức năng của kế hoạch để đọc đủ mô hình; không phải mục tiêu chu kỳ 20 ms. Các giá trị trong plan.json sửa được và chưa phải số đo vật lý.",
        'Khoảng cách tính từ tâm phôi ước lượng tới giới hạn tâm cho phép; số âm là vượt giới hạn. Tuổi dữ liệu là thời điểm quyết định trừ thời điểm nguồn.',
        'Hệ số ma sát chỉ nhân thành phần trượt của cả băng và phôi. Các thành phần ma sát xoắn/lăn giữ nguyên. Mô hình 1D không có tham số ma sát nên không tự thay công thức theo biến thiên này.','',
        '| Ma sát nhân | Tuổi dữ liệu (s) | Đủ ba nhánh | 1D chạy / tiếp xúc dọc dừng | 1D dừng / tiếp xúc dọc chạy | Thêm ngang/cao làm đổi lệnh |',
        '|---|---:|---:|---:|---:|---:|']
    for g in result['groups']:
        counts=g['forward_decision_pairs'];lines.append(f"| {g['sliding_friction_scale']} | {g['age_s']} | {g['complete']}/{g['planned']} | {counts.get('reduced_continue_contact_hold',0)} | {counts.get('reduced_hold_contact_continue',0)} | {g['extra_constraints_change_action']} |")
    lines+=['','Hai bản tiếp xúc dùng cùng động lực học; một bản chỉ chấm dọc, bản kia chấm thêm ngang/cao. Biên đầy đủ phải không lớn hơn biên chỉ dọc trong dung sai đối chiếu. Vi phạm bất biến này: '+str(result['invariant_failures'])+'.',
        'Khác biệt biên dọc chỉ là khác biệt giữa hai mô hình, không phải sai số so máy thật. MuJoCo cũng chưa hiệu chuẩn; không coi nó là đáp án đúng tuyệt đối. Kết quả cùng một lưới không phải mẫu ngẫu nhiên hay xác suất gặp lỗi.',
        'Các đầu vào ngoài vùng hỗ trợ của băng vẫn được giữ để tìm giới hạn. Không dùng chúng để tuyên bố máy vận hành bình thường. Không tự chọn hệ số dừng mới từ lưới này rồi đánh giá lại trên chính lưới như dữ liệu độc lập.',
        'Đọc cases.csv để lọc từng đầu vào, cases.jsonl để xem đủ ba kết quả. Bản ghi tính thiếu không được tính là đồng ý, mọi lỗi giữ nguyên.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    parser.add_argument('--plan',type=Path,default=HERE/'experiments/model_boundary_20261103.json')
    args=parser.parse_args();r=run(args.output,load_config(args.config),json.loads(args.plan.read_text(encoding='utf-8')))
    raise SystemExit(int(r['recorded']!=r['planned'] or r['incomplete_or_error']>0 or r['invariant_failures']>0))
