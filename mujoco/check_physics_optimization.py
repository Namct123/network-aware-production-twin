"""Compare native and reference contact forecasts, retaining failures and deadline misses."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import platform
import os
from config import load_config
from estimator import Estimate
from experiment import write_json
from physics_predictor import MuJoCoBeltPredictor,ReferenceMuJoCoBeltPredictor
from qualify import benchmark

HERE=Path(__file__).resolve().parent

def compare(output,config):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    import mujoco,numpy
    write_json(output/'base_config.json',config)
    write_json(output/'manifest.json',{'python':platform.python_version(),'mujoco':mujoco.__version__,
        'numpy':numpy.__version__,'platform':platform.platform(),
        'cpu_count':os.cpu_count(),'cpu_affinity_count':len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
        'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in
                         ['physics_predictor.py','check_physics_optimization.py','qualify.py']},
        'scope':'native thread counts 1/4/8; same physical models; no physical parameter calibration'})
    cases=[(.1,0,0),(.5,.16,0),(.9,.16,.02),(.7,.2,.06),(1.02,.16,.06),(.99,.24,.1)]
    rows=[]
    for variant in ('baseline','off_grid_stop'):
        c=deepcopy(config);c['prediction']['wall_budget_s']=5.0
        if variant=='off_grid_stop':
            c['timing']['physics_step_s']=.003
            c['prediction']['reaction_delays_s']=[0,.013,.027]
        write_json(output/(variant+'_functional_config.json'),c)
        reference=ReferenceMuJoCoBeltPredictor(c)
        a,b=c['geometry']['long_belt_y_m']
        for index,(fraction,speed,age) in enumerate(cases):
            state=Estimate(a+(b-a)*fraction,speed,.005,2,'tracking')
            row={'variant':variant,'case':index,'input':state.as_dict(),'age_s':age}
            try:
                left=reference.rollout(state,0,age)
                comparisons=[]
                for threads in (1,4,8):
                    threaded=deepcopy(c);threaded['prediction']['native_threads']=threads
                    right=MuJoCoBeltPredictor(threaded).rollout(state,0,age)
                    comparisons.append(right)
                expected_steps=left['expected_scenarios']*math.ceil(c['prediction']['horizon_s']/c['timing']['physics_step_s'])
                errors=[max(abs(left['margins_m'][k]-r['margins_m'][k]) for k in ('HOLD','CONTINUE')) if left['status']==r['status']=='complete' else None for r in comparisons]
                row.update(reference=left,native_variants=comparisons,margin_max_error_m=max(e for e in errors if e is not None) if any(e is not None for e in errors) else None,
                    passed=all(e is not None and e<=1e-9 and left['action']==r['action'] and
                    left['completed_scenarios']==r['completed_scenarios']==left['expected_scenarios'] and
                    left['rollout_steps']==r['rollout_steps']==expected_steps for e,r in zip(errors,comparisons)))
            except Exception as error:row.update(passed=False,error=f'{type(error).__name__}: {error}')
            rows.append(row);write_json(output/'equivalence.json',rows)
            print(variant,index,'PASS' if row['passed'] else 'FAIL',flush=True)
    settings=json.loads((HERE/'experiments/qualification_20261102.json').read_text(encoding='utf-8'))['benchmark']
    def native_factory(threads):
        def create(c):
            c=deepcopy(c);c['prediction']['native_threads']=threads
            return MuJoCoBeltPredictor(c)
        return create
    timing=benchmark(config,settings,output,{'physics_reference':ReferenceMuJoCoBeltPredictor,
        **{f'physics_native_t{n}':native_factory(n) for n in (1,4,8)}})
    report={'kind':'physics_optimization_v1','equivalence_cases':len(rows),'equivalence_failures':sum(not r['passed'] for r in rows),
        'max_margin_error_m':max((r['margin_max_error_m'] for r in rows if r.get('margin_max_error_m') is not None),default=None),
        'benchmark_groups':timing['groups'],'realtime_certified':False,'physical_validation':False,
        'physical_parameter_tuning':False,'compute_variants':[1,4,8],'user_acceptance':'pending'}
    write_json(output/'optimization.json',report)
    lines=['# Tối ưu dự báo MuJoCo','',
        f"Đối chiếu {len(rows)} trường hợp; sai khác vượt tiêu chí: {report['equivalence_failures']}.",
        'Tiêu chí: cùng hành động, đủ kịch bản, cùng số bước, sai khác biên nhỏ hơn hoặc bằng một phần tỷ mét.',
        'Mức sai khác này chỉ để kiểm tra hai cách tính của cùng mô hình, không phải độ chính xác máy thật.',
        'Biến thể thời điểm dừng lệch lưới chỉ dùng đối chiếu; không thay hồ sơ điều khiển đang dùng.','',
        '| Cách tính | Hạn | Mẫu | Trung vị (ms) | p95 (ms) | Tính đủ | Quá hạn |',
        '|---|---|---:|---:|---:|---:|---:|']
    for g in timing['groups']:
        label='Vòng lặp gốc' if g['backend']=='physics_reference' else 'Gom MuJoCo, '+g['backend'].split('_t')[-1]+' luồng'
        budget='Đang cấu hình' if g['budget_kind']=='configured' else 'Chức năng'
        lines.append(f"| {label} | {budget} | {g['samples']} | {g['median_ms']:.3f} | {g['p95_ms']:.3f} | {g['complete']} | {g['deadline_misses']} |")
    lines+=['','Lượt làm nóng và khởi tạo ghi riêng. Thời gian ngoài hàm dùng để so hạn; không chỉ lấy số tự báo bên trong.',
        'Mã máy không thể bị ngắt ngay ở giữa một nhóm bước; quá hạn quan sát được trả dừng chờ, chưa có bảo đảm thời gian thực cứng.',
        'Đo lần lượt bản gốc và bản gom 1/4/8 luồng; không đổi số kịch bản, bước vật lý, chân không hoặc tốc độ sản xuất để đạt số đẹp.',
        'Nhánh mặc định vẫn là tính một chiều. Cả hai cách dự báo chỉ mô hình băng/phôi, chưa phải toàn bộ robot/khí nén đã hiệu chuẩn.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    a=p.parse_args();r=compare(a.output,load_config(a.config));raise SystemExit(int(r['equivalence_failures']>0))
