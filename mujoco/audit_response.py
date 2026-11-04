"""Read-only response audit of a bounded predictive-replay study; no controller tuning."""
import argparse
import base64
import csv
import json
from pathlib import Path
from config import number
from stream_archive import decode, digest, logical, read
from study_predictive_replay import CASES, load_plan


def timeline(rows, activation):
    if not rows or rows[-1].get('final') is not True or any(r.get('final') for r in rows[:-1]):
        raise ValueError('exactly one final command required')
    controls = rows[:-1]
    if type(activation) is not int or not 1 <= activation < len(controls):
        raise ValueError('activation index out of bounds')
    if controls[activation-1].get('prediction') is None:
        raise ValueError('epoch must follow a prediction call')
    previous = -1.
    for r in rows:
        number(r['time_s'], 'tick time', 0)
        if r['time_s'] <= previous or r.get('physical_output') is not False:
            raise ValueError('ordered dry-run ticks required')
        previous = r['time_s']
    epoch = controls[activation]['time_s']
    base_speed = controls[activation-1]['command_message']['payload']['long']
    def first(predicate): return next((r for r in controls[activation:] if predicate(r)), None)
    reduced = first(lambda r: 0 < r['command_message']['payload']['long'] < base_speed-1e-12)
    held = first(lambda r: r['phase'] == 'HOLD')
    rejected = first(lambda r: r.get('input_guard') is not None and not r['input_guard']['accepted'])
    last_pre_input = next((r for r in reversed(controls[:activation]) if r.get('input_guard') is not None and r['input_guard']['accepted']), None)
    result = {'last_accepted_pre_epoch_time_s':last_pre_input['time_s'] if last_pre_input else None,
        'hold_after_last_pre_epoch_input_ms':1000*(held['time_s']-last_pre_input['time_s']) if held and last_pre_input else None,
        'epoch_time_s':epoch, 'pre_epoch_speed_m_s':base_speed,
        'first_hold_reason':held['hold_reason'] if held else None,
        'rejected_signal_packets':sum(r.get('input_guard') is not None and not r['input_guard']['accepted'] for r in controls)}
    for name, row in [('speed_reduction',reduced),('hold',held),('packet_rejection',rejected)]:
        result[name+'_time_s'] = row['time_s'] if row else None
        result[name+'_after_epoch_ms'] = 1000*(row['time_s']-epoch) if row else None
    return result


def comparison_view(row):
    result = logical(row)
    result.pop('command_message', None)
    guard = result.get('input_guard')
    if guard is not None: result['input_guard'] = {k:v for k,v in guard.items() if k != 'session_id'}
    result['command_payload'] = row['command_message']['payload']
    return result


def compare_pair(left, right):
    # Normalize only experiment session labels, not data/times/quality/decisions.
    hold_times = [x['timing']['hold_time_s'] for x in (left,right)]
    until = max(hold_times) if all(t is not None for t in hold_times) else None
    a, b = left['rows'][:-1], right['rows'][:-1]
    equal_count = 0
    for x,y in zip(a,b):
        if comparison_view(x) != comparison_view(y): break
        equal_count += 1
    ax = [r for r in a if until is not None and r['time_s'] <= until]
    bx = [r for r in b if until is not None and r['time_s'] <= until]
    inputs_same = until is not None and [(r['time_s'],left['packets'].get(r['time_s'])) for r in ax] == [(r['time_s'],right['packets'].get(r['time_s'])) for r in bx]
    decisions_same = until is not None and [comparison_view(r) for r in ax] == [comparison_view(r) for r in bx]
    first_difference = min(a[equal_count]['time_s'],b[equal_count]['time_s']) if equal_count < min(len(a),len(b)) else None
    return {'left':left['name'],'right':right['name'],'through_hold_time_s':until,
        'input_trace_equal_through_hold':inputs_same,'logical_trace_equal_through_hold':decisions_same,
        'equal_logical_prefix_ticks':equal_count,'first_logical_difference_time_s':first_difference,
        'scope':'session IDs normalized; fixed sample times and recorded inputs, not byte-identical independent network trials'}


def audit(folder, output, source_manifest):
    folder = Path(folder).resolve(); manifest_path = Path(source_manifest)
    snapshot = decode(read(manifest_path)); hashes = {}
    def get(path):
        path = Path(path)
        if not path.resolve().is_relative_to(folder): raise ValueError('evidence path escapes study')
        data = read(path); hashes[path.relative_to(folder).as_posix()] = digest(data); return data
    study = decode(get(folder/'predictive_replay_study.json'))
    get(folder/'plan.json'); plan = load_plan(folder/'plan.json')
    expected = {f'{i:02}_{case}' for i in range(1,plan['repetitions']+1) for case in CASES}
    trials = study['trials']
    if len(trials) != len(expected) or {t['name'] for t in trials} != expected:
        raise ValueError('complete planned trial matrix required')
    records = {}; metrics = []; reference_config = None; reference_mapping = None
    for trial in trials:
        name = trial['name']; base = folder/name
        if trial['case'] not in CASES or not name.endswith('_'+trial['case']): raise ValueError('case/name mismatch')
        rows = [decode(s) for s in get(base/'commands_dry_run.jsonl').splitlines()]
        summary = decode(get(base/'summary.json')); config = decode(get(base/'effective_config.json'))
        mapping = decode(get(base/'mapping.json')); receiver = decode(get(base/'receiver.json'))
        calls = decode(get(base/'prediction_calls.json'))
        canonical = json.dumps(config,sort_keys=True)
        mapped = json.dumps(mapping,sort_keys=True)
        if reference_mapping is None: reference_mapping = mapped
        if mapped != reference_mapping: raise ValueError('mapping differs between trials')
        if reference_config is None: reference_config = canonical
        if canonical != reference_config: raise ValueError('profiles differ; audit does not pool mixed configurations')
        expected_sources = {Path(n).name for n in snapshot['files'] if Path(n).parent.as_posix()=='mujoco' and n.endswith('.py')}
        if set(summary.get('source_sha256',{})) != expected_sources or any(snapshot['files'].get('mujoco/'+n) != h for n,h in summary['source_sha256'].items()):
            raise ValueError('declared source manifest does not match recorded producer: '+name)
        if len(rows) != trial['ticks'] or len(calls) != trial['prediction_calls'] or len(calls) != sum(r.get('prediction') is not None for r in rows):
            raise ValueError('trial counters differ from logs')
        if summary['invalid_datagrams'] or any(r.get('input_error') for r in rows): raise ValueError('malformed input present')
        timing = timeline(rows,trial['activation_tick'])
        if timing['first_hold_reason'] != trial['hold_reason'] or timing['hold_time_s'] != trial['hold_time_s']:
            raise ValueError('hold summary differs from actual trace')
        packets = {}; last = -1.
        for line in get(base/'raw_datagrams.jsonl').splitlines():
            raw = decode(line); now = raw['time_s']; number(now,'packet time',0)
            if now <= last: raise ValueError('packet times must increase')
            last = now; packet = decode(base64.b64decode(raw['bytes_b64'],validate=True))
            if packet['session_id'] != receiver['session_id'] and trial['case'] != 'wrong_session':
                raise ValueError('unexpected session fixture')
            packets[now] = {k:v for k,v in packet.items() if k != 'session_id'}
        if not set(packets) <= {r['time_s'] for r in rows[:-1]}: raise ValueError('orphan packet')
        if len(packets) != summary['datagrams']: raise ValueError('packet count differs')
        records[name] = {'name':name,'rows':rows,'timing':timing,'packets':packets}
        metrics.append({'name':name,'case':trial['case'],'fault_injected':trial['case']!='nominal',
            'ticks':len(rows),'prediction_calls':len(calls),**timing})
    pairs = [compare_pair(records[f'{i:02}_gap'], records[f'{i:02}_stale_delay']) for i in range(1,plan['repetitions']+1)]
    cfg = json.loads(reference_config)
    report = {'kind':'response_audit_v1','passed':True,'trial_count':len(trials),'metrics':metrics,'delay_vs_gap_pairs':pairs,
        'period_s':cfg['timing']['physics_step_s']*cfg['timing']['sample_steps'],
        'silence_timeout_s':cfg['timing']['silence_timeout_s'],
        'warning_age_s':cfg['reconfiguration']['warning_age_s'],'warning_ticks':cfg['reconfiguration']['warning_ticks'],
        'plan':plan,'input_files_sha256':hashes,'producer_manifest_sha256':digest(read(manifest_path)),
        'producer_source_hashes_checked':True,'physical_validation':False,'physical_output':False,'parameter_tuning':False,
        'scope':'retrospective simulated-clock response analysis; paired traces normalize only session labels; no physical diagnosis accuracy'}
    output = Path(output); output.mkdir(parents=True,exist_ok=False)
    (output/'response_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    with (output/'timing.csv').open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=list(metrics[0])); writer.writeheader(); writer.writerows(metrics)
    labels = {'nominal':'Bình thường','warning_delay':f"Trễ {plan['warning_delay_s']*1000:g} ms",'stale_delay':f"Trễ {plan['stale_delay_s']*1000:g} ms",'gap':f"Mất gói {plan['gap_s']*1000:g} ms",'repeat':'Một gói lặp','wrong_session':'Một gói sai phiên'}
    def span(case,key):
        values = [m[key] for m in metrics if m['case']==case and m[key] is not None]
        return f'{min(values):.1f}–{max(values):.1f}' if values else 'Không có'
    lines = ['# Phản ứng của lõi trước dữ liệu mạng bất thường','',
        'Thời gian dưới đây là thời gian mô phỏng tính từ nhịp đầu áp dụng tình huống. Không phải độ trễ PLC hoặc thời gian xử lý trên máy thật.','',
        '| Tình huống | Lệnh giảm tốc sau mốc (ms) | Dừng chờ sau mốc (ms) | Lý do dừng |',
        '|---|---:|---:|---|']
    for case in CASES:
        reason_vi={'telemetry_timeout':'Quá hạn im lặng dữ liệu','unconfirmed_xy_a2_midstroke_and_vacuum':'Chưa có xác nhận trục XY/đầu hút','pick_uncertainty_exceeded':'Bất định vị trí gắp vượt giới hạn'}
        reasons = sorted({reason_vi.get(m['first_hold_reason'],m['first_hold_reason'] or 'không dừng') for m in metrics if m['case']==case})
        lines.append(f"| {labels[case]} | {span(case,'speed_reduction_after_epoch_ms')} | {span(case,'hold_after_epoch_ms')} | {', '.join(reasons)} |")
    lines += ['', 'Mốc của ca bình thường chỉ dùng so sánh, không có lỗi được chèn. Dừng do thiếu xác nhận XY/giác hút là giới hạn phản hồi hiện tại, không phải phát hiện lỗi mạng.', '',
        f"Có {sum(p['input_trace_equal_through_hold'] and p['logical_trace_equal_through_hold'] for p in pairs)}/{len(pairs)} cặp trễ dài/mất gói có cùng đầu vào và quyết định tới lúc dừng. Vì vậy các phiên này chưa cho phép tách hai nguyên nhân trước lúc dừng.", '',
        'Gói lặp và sai phiên được ghi nhận trong timing.csv ở cột packet_rejection_after_epoch_ms. Giá trị 0 nghĩa là cùng nhịp xử lý, không phải xử lý mất 0 giây trên máy thật. Dừng là phản ứng bảo thủ trước thiếu dữ liệu. Dữ liệu trở lại không tự xóa dừng chờ. Ba lần lặp dùng cùng mô hình và lịch thử; không phải ba máy độc lập hoặc căn cứ tính độ chính xác chẩn đoán. Không thay tham số để làm kết quả đạt.']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',type=Path,required=True)
    p.add_argument('--source-manifest',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); report=audit(a.input,a.output,a.source_manifest)
    print(json.dumps({'passed':report['passed'],'trials':report['trial_count'],'pairs':len(report['delay_vs_gap_pairs'])}))
