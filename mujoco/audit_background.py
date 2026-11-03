"""Offline comparison of recorded contact replies and reduced forecasts, never actuation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from config import load_config,number
from estimator import Estimate
from predictor import Predictor
from reset_protocol import digest


def compare_receipt(config,session,row,seen):
    """Validate logged association, not cryptographic authenticity or current validity."""
    receipt=row.get('receipt')
    if receipt is None:return None
    result={'receipt_time_s':row.get('time_s'),'comparable':False,'record_valid':False}
    try:
        if row.get('mode')!='observe_only' or row.get('control_applied') is not False:raise ValueError('not_observation_only')
        if type(receipt) is not dict or type(receipt.get('accepted')) is not bool:raise ValueError('invalid_receipt')
        job=receipt['request'];rid=job['request_id']
        if type(rid) is not int or rid<0 or type(receipt.get('request_id')) is not int or receipt['request_id']!=rid:raise ValueError('request_id_mismatch')
        result['request_id']=rid
        if job['profile_sha256']!=digest(config):raise ValueError('profile_mismatch')
        if any(type(job[k]) is not type(v) or job[k]!=v for k,v in session.items()):raise ValueError('session_mismatch')
        if job['clock_domain']!='simulation':raise ValueError('unsupported_clock_domain')
        if type(job['source_sequence']) is not int or job['source_sequence']<0:raise ValueError('invalid_source_sequence')
        for key in ('source_time_s','decision_time_s','submitted_wall_s'):number(job[key],key,0)
        number(row['time_s'],'receipt_time_s',0)
        if not job['source_time_s']<=job['decision_time_s']<=row['time_s']:raise ValueError('invalid_simulation_times')
        if type(receipt.get('reason')) is not str or receipt['accepted']!=(receipt['reason']=='accepted_observation_only'):raise ValueError('receipt_status_mismatch')
        if rid in seen:raise ValueError('duplicate_request')
        p=config['prediction'];expected=2*len(p['position_offsets'])*len(p['speed_offsets_m_s'])*len(p['reaction_delays_s'])
        if type(job['expected_scenarios']) is not int or job['expected_scenarios']!=expected:raise ValueError('scenario_count_mismatch')
        estimate=Estimate(**job['estimate'])
        for key in ('y_m','velocity_m_s','uncertainty_m'):number(getattr(estimate,key),key,0 if key!='y_m' else None)
        physics=receipt.get('prediction')
        json.dumps(job,allow_nan=False);json.dumps(physics,allow_nan=False)
        seen.add(rid)
        result.update(record_valid=True,input_sha256=digest(job),admitted_observation=receipt['accepted'],
            admission_reason=receipt['reason'],source_sequence=job['source_sequence'],
            decision_time_s=job['decision_time_s'],simulation_age_s=row['time_s']-job['decision_time_s'])
        if receipt.get('worker_error') is not None:
            result['reason']='worker_error';return result
        if not isinstance(physics,dict):raise ValueError('missing_prediction')
        result['contact_status']=physics.get('status')
        if physics.get('status') not in ('complete','deadline_exceeded'):raise ValueError('invalid_prediction_status')
        if physics['status']!='complete':
            result['reason']='contact_incomplete';return result
        if physics.get('action') not in ('HOLD','CONTINUE'):raise ValueError('invalid_prediction_action')
        if any(type(physics.get(k)) is not int or physics[k]!=expected for k in ('expected_scenarios','completed_scenarios')):raise ValueError('incomplete_scenario_count')
        for action in ('HOLD','CONTINUE'):number(physics['margins_m'][action],'contact margin')
        # ponytail: deterministic replay disables only the wall clock, not equations.
        # It measures model decisions, never the foreground's actual deadline behavior.
        reduced=Predictor(config,clock=lambda:0.0).rollout(estimate,job['source_time_s'],job['decision_time_s'])
        a,b=reduced['action'],physics['action']
        verdict='agree' if a==b else 'reduced_continue_contact_hold' if a=='CONTINUE' else 'reduced_hold_contact_continue'
        result.update(comparable=True,reason=verdict,reduced_action=a,contact_action=b,
            reduced_margins_m=reduced['margins_m'],contact_margins_m=physics['margins_m'])
    except (KeyError,TypeError,ValueError,OverflowError) as error:
        result.update(record_valid=False,comparable=False,reason=str(error)[:160])
    return result


def audit(source,output):
    source=Path(source);output=Path(output)
    config=load_config(source/'effective_config.json')
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    if manifest['config_sha256']!=digest(config):raise ValueError('manifest/config mismatch')
    session=manifest['session']
    if set(session)!={'session_id','generation'} or type(session['session_id']) is not str or type(session['generation']) is not int:raise ValueError('invalid session')
    if not config['prediction'].get('background',{}).get('enabled'):raise ValueError('background not enabled for this run')
    output.mkdir(parents=True,exist_ok=False)
    hashes={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ('effective_config.json','manifest.json','background.jsonl')}
    rows=[];seen=set();line_count=0
    with (source/'background.jsonl').open(encoding='utf-8') as f:
        for line_count,line in enumerate(f,1):
            try:
                row=json.loads(line)
                if not isinstance(row,dict):raise ValueError('row must be object')
                result=compare_receipt(config,session,row,seen)
            except (ValueError,TypeError) as error:result={'record_valid':False,'comparable':False,'reason':'invalid_json_record: '+str(error)[:100]}
            if result is not None:rows.append({'line':line_count,**result})
    counts=Counter(r['reason'] for r in rows)
    paired=[r for r in rows if r['comparable']]
    groups={}
    for admitted in (True,False):
        subset=[r for r in paired if r['admitted_observation'] is admitted]
        groups['admitted' if admitted else 'discarded_at_receipt']={'pairs':len(subset),'outcomes':dict(Counter(r['reason'] for r in subset))}
    report={'kind':'background_model_audit_v1','control_applied':False,'physical_validation':False,
        'log_lines':line_count,'receipts':len(rows),'invalid_records':sum(not r['record_valid'] for r in rows),
        'comparable_pairs':len(paired),'outcomes':dict(counts),'groups':groups,
        'source_files_sha256':hashes,'audit_source_sha256':{n:hashlib.sha256((Path(__file__).parent/n).read_bytes()).hexdigest() for n in ('audit_background.py','predictor.py','config.py','estimator.py','reset_protocol.py')},
        'logged_predictor_sha256':manifest.get('source_sha256',{}).get('predictor.py'),
        'replay_predictor_matches_logged_source':manifest.get('source_sha256',{}).get('predictor.py')==hashlib.sha256((Path(__file__).parent/'predictor.py').read_bytes()).hexdigest(),
        'scope':'Offline same-snapshot model comparison; reduced wall clock disabled. Not actual foreground decisions, physical accuracy, authenticated provenance, current motion permission, or equal constraint sets.'}
    (output/'pairs.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows),encoding='utf-8')
    (output/'audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    lines=['# Đối chiếu dự báo từ cùng dữ liệu đầu vào','',
        'Đây là đọc lại ngoại tuyến. Không thay đổi lệnh, hồ sơ hay tệp gốc. Nhánh 1D tính lại từ đúng ảnh đầu vào của yêu cầu MuJoCo; đồng hồ tính toán bị tắt để xem đủ kết quả mô hình. Đây không phải quyết định thực tế đã phát ở nhánh nhanh.','',
        f"Đọc {line_count} dòng; {len(rows)} kết quả nhận; {report['invalid_records']} bản ghi không hợp lệ; {len(paired)} cặp đủ điều kiện so sánh.",
        '', '| Khi nhận kết quả | Cặp so được | Cùng khuyến nghị | 1D chạy, MuJoCo dừng | 1D dừng, MuJoCo chạy |','|---|---:|---:|---:|---:|']
    for key,title in [('admitted','Được nhận để quan sát'),('discarded_at_receipt','Bị loại tại thời điểm nhận')]:
        g=groups[key];o=g['outcomes'];lines.append(f"| {title} | {g['pairs']} | {o.get('agree',0)} | {o.get('reduced_continue_contact_hold',0)} | {o.get('reduced_hold_contact_continue',0)} |")
    lines+=['','Kết quả thiếu hoặc bản ghi sai không được tính thành cặp đồng ý. Khuyến nghị dừng vì hết thời gian tính chưa phải dự báo dừng hoàn chỉnh.',
        'Một kết quả quá cũ có thể được so ngoại tuyến nhưng vẫn bị loại khi chạy. So cùng đầu vào không cấp lại quyền dùng nó để điều khiển.',
        'Hai mô hình khác cách tính và ràng buộc: 1D xét khoảng dừng dọc băng; MuJoCo còn xét ngang và cao. Không trừ hai biên tổng hợp để gọi là sai số vật lý. Cùng khuyến nghị không chứng minh mô hình đúng; khác khuyến nghị không tự xác định bên nào đúng.',
        'Các kết quả cùng một chu trình có tương quan. Không coi tỷ lệ đồng ý là độ chính xác phát hiện lỗi hoặc bằng chứng an toàn. Xem pairs.jsonl để truy từng mẫu và audit.json để xem mã băm nguồn.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=audit(args.source,args.output)
    print(json.dumps(report,indent=2));raise SystemExit(int(report['invalid_records']>0))
