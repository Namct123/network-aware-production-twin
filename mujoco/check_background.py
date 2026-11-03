"""Paced virtual cycles and failure probe for the observation-only worker."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from config import load_config
from experiment import run,write_json
from runtime import RuntimeCore
from audit_background import audit

HERE=Path(__file__).resolve().parent

def read_rows(path):return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]

def latency(rows,key):
    xs=sorted(r[key] for r in rows if r.get(key) is not None)
    return {'samples':len(xs),'median_ms':xs[len(xs)//2] if xs else None,
            'p95_ms':xs[math.ceil(.95*len(xs))-1] if xs else None,'max_ms':xs[-1] if xs else None,
            'observed_over_20ms':sum(x>20 for x in xs)}

def check(output,base):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    write_json(output/'base_config.json',base)
    write_json(output/'manifest.json',{'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in
        ['background_forecast.py','runtime.py','experiment.py','check_background.py']},
        'scope':'paced shared-clock simulation; background advice never applied; not a physical or hard-realtime trial'})
    results={};traces={};timings={}
    for name in ('baseline','observer','incomplete_worker'):
        c=deepcopy(base)
        if name=='baseline':c['prediction']['background']['enabled']=False
        if name=='incomplete_worker':c['prediction']['background']['compute_budget_s']=1e-9
        result=run(output/name,config=c,assume_open_loop=True,pace_wall_time=True)
        results[name]=result
        traces[name]=[(r['time_s'],r['phase'],r['command'],r['estimate']) for r in read_rows(output/name/'controller.jsonl')]
        timings[name]=latency(read_rows(output/name/'control_timing.jsonl'),'core_step_ms')
        print(name,result['controller_state'],result['background_forecast'].get('accepted_observations',0),flush=True)
        write_json(output/'partial_results.json',results)
    audits={name:audit(output/name,output/(name+'_audit')) for name in ('observer','incomplete_worker')}
    checks={'terminal_placement':all(r['controller_state']=='DONE' and r['placement_pass_evaluator_only'] is True for r in results.values()),
        'identical_control_traces':traces['baseline']==traces['observer']==traces['incomplete_worker'],
        'worker_observations_received':results['observer']['background_forecast']['accepted_observations']>0,
        'incomplete_results_discarded':results['incomplete_worker']['background_forecast']['discard_reasons'].get('prediction_incomplete',0)>0,
        'workers_closed':all(not r['background_forecast'].get('worker_alive',False) for r in results.values()),
        'offline_same_snapshot_pairs':audits['observer']['comparable_pairs']>0 and all(a['invalid_records']==0 and a['replay_predictor_matches_logged_source'] for a in audits.values()),
        'incomplete_excluded_from_agreement':audits['incomplete_worker']['comparable_pairs']==0}
    with RuntimeCore(base) as core:
        ready=core.background.wait_ready(base['prediction']['background']['startup_timeout_s'])
        core.background.process.terminate();core.background.process.join(2)
        step=core.step(None,0)
        checks['crashed_worker_does_not_stop_foreground_call']=ready and step['command_error'] is None and step['background']['state']=='worker_unavailable'
    report={'kind':'background_observer_v1','checks':checks,'passed':all(checks.values()),'control_applied':False,
        'latency':timings,'summaries':results,'offline_audits':audits,'realtime_certified':False,'physical_validation':False,'user_acceptance':'pending'}
    write_json(output/'background_check.json',report)
    lines=['# Dự báo nền ở chế độ chạy quan sát','',
        'Nhánh 1 chiều vẫn quyết định lệnh. MuJoCo ở tiến trình riêng, chỉ có một yêu cầu đang xử lý, không xếp hàng vô hạn.',
        'Bộ thử chạy ba chu trình có nhịp thời gian mô phỏng gần thời gian trên máy; chưa đồng bộ đồng hồ PLC thật.','',
        '| Kiểm tra | Kết quả |','|---|---|']
    names={'terminal_placement':'Đặt phôi ở cả ba chu trình','identical_control_traces':'Dấu vết lệnh/ước lượng giống nhau',
        'worker_observations_received':'Có kết quả nền được nhận để quan sát','incomplete_results_discarded':'Kết quả tính thiếu bị loại',
        'workers_closed':'Các tiến trình nền đã đóng','crashed_worker_does_not_stop_foreground_call':'Tiến trình nền bị dừng vẫn gọi được bước lõi',
        'offline_same_snapshot_pairs':'So ngoại tuyến đúng ảnh đầu vào, không bản ghi sai',
        'incomplete_excluded_from_agreement':'Không tính kết quả thiếu thành cặp đồng ý'}
    lines += [f"| {names[k]} | {'Đạt' if v else 'Cần xem lại'} |" for k,v in checks.items()]
    lines+=['','| Chu trình | Mẫu bước lõi | Trung vị (ms) | p95 (ms) | Lớn nhất (ms) | Mẫu >20 ms |',
        '|---|---:|---:|---:|---:|---:|']
    for name,t in timings.items():
        label={'baseline':'Không chạy nền','observer':'MuJoCo nền quan sát','incomplete_worker':'Nền luôn tính thiếu'}[name]
        lines.append(f"| {label} | {t['samples']} | {t['median_ms']:.3f} | {t['p95_ms']:.3f} | {t['max_ms']:.3f} | {t['observed_over_20ms']} |")
    lines+=['','Bảng đo RuntimeCore.step, không gồm bước cơ học, ghi tệp, nhịp chờ hoặc khởi tạo tiến trình. Số mẫu này không chứng minh hạn thời gian thực.',
        'Kết quả nhận để quan sát không được dùng để cho chạy, dừng hoặc đặt lại. Quy tắc tuổi/trạng thái hiện tại chưa chứng minh đủ điều kiện để áp lệnh từ dự báo cũ.',
        'Mọi kết quả không đạt vẫn được giữ. Không có phép đo trên hệ vật lý trong bộ thử này.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,default=HERE/'configs/background_observer_20261103.json')
    a=p.parse_args();r=check(a.output,load_config(a.config));raise SystemExit(int(not r['passed']))
