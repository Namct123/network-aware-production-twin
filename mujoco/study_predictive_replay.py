"""Closed-loop MuJoCo digital signals through the stream boundary, then offline replay."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import patch
from config import exact_keys, load_config, number
from io_adapter import load_adapter
from model_profile import write_model
from predictor import Predictor
from sensor_model import SensorModel
from stream_input import StreamCore
from stream_archive import replay

HERE = Path(__file__).resolve().parent
CASES = ('nominal', 'warning_delay', 'stale_delay', 'gap', 'repeat', 'wrong_session')


def write(path, value): path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def load_plan(path):
    p = json.loads(Path(path).read_text(encoding='utf-8'))
    exact_keys(p, ('kind','repetitions','replays_per_trial','warning_delay_s','stale_delay_s','gap_s','cases','scope'), 'replay plan')
    if p['kind'] != 'predictive_replay_plan_v1' or p['cases'] != list(CASES): raise ValueError('fixed six cases required')
    for key in ('repetitions','replays_per_trial'):
        if type(p[key]) is not int or not 1 <= p[key] <= 5: raise ValueError('bounded 1..5 repetitions required')
    for key in ('warning_delay_s','stale_delay_s','gap_s'):
        number(p[key], key, 0, True)
        if p[key] > 1: raise ValueError('fixture delays <=1 s required')
    return p


def capture(folder, config, mapping, case, plan, session):
    from run_cell import Cell
    folder.mkdir(parents=True, exist_ok=False)
    model = write_model(config, folder/'effective_model.xml')
    cell = Cell(config, model); sensor = SensorModel(config=config)
    core = StreamCore(config, mapping, session)
    write(folder/'effective_config.json', config); write(folder/'mapping.json', mapping)
    write(folder/'receiver.json', {'session_id':session, 'generation':0,
        'transport':'synthetic_scheduled_packets_not_udp', 'physical_output_supported':False})
    period = config['timing']['physics_step_s']*config['timing']['sample_steps']
    activated = None; queue = []; previous_packet = None; last = None; count = 0; calls = []
    try:
        with (folder/'raw_datagrams.jsonl').open('w',encoding='utf-8') as raw, (folder/'commands_dry_run.jsonl').open('w',encoding='utf-8') as log:
            # ponytail: one bounded product; packets may wait in a short synthetic queue.
            for index in range(math.ceil(config['timing']['run_budget_s']/period)+1):
                state = cell.observe(); now = state['time_s']; frame, _ = sensor.sample(state)
                row = {'session_id':session, 'generation':0,'sequence':frame.sequence,
                    'source_time':now/mapping['clock']['source_scale_s'],
                    'values':{m['input_key']:frame.values.get(name) for name,m in mapping['signals'].items()},
                    'quality':{m['input_key']:frame.quality.get(name,'unavailable') for name,m in mapping['signals'].items()}}
                active = activated is not None and index >= activated
                delay = plan[case+'_s'] if active and case in ('warning_delay','stale_delay') else 0
                packet = json.dumps(row,allow_nan=False).encode()
                if active and index == activated and case == 'repeat': packet = previous_packet
                if active and index == activated and case == 'wrong_session':
                    row['session_id'] = 'old-session'; packet = json.dumps(row).encode()
                drop = active and case == 'gap' and index-activated < math.ceil(plan['gap_s']/period)
                if not drop: queue.append((index+math.ceil(delay/period),packet))
                incoming = queue.pop(0)[1] if queue and queue[0][0] <= index else None
                if incoming is not None:
                    raw.write(json.dumps({'time_s':now,'bytes_b64':base64.b64encode(incoming).decode(),'peer':None})+'\n')
                last = core.tick(incoming,now); log.write(json.dumps(last,allow_nan=False)+'\n'); count += 1
                if last['prediction'] is not None:
                    calls.append({'tick':index,'time_s':now,**last['prediction']})
                    if activated is None: activated = index+1
                previous_packet = json.dumps({**row,'session_id':session}).encode()
                cell.apply(last['command_message']['payload'])
                context = core.core.controller.hold_context
                if context and now-context['time_s'] >= config['timing']['hold_settle_s']: break
                cell.step()
            final = core.finish(cell.data.time+period); log.write(json.dumps(final,allow_nan=False)+'\n')
    finally: core.close()
    summary = {**core.summary(),'failure':None,'transport':'synthetic_scheduled_packets_not_udp',
        'local_loopback_only':False,'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}}
    write(folder/'summary.json',summary); write(folder/'prediction_calls.json',calls)
    return {'case':case,'ticks':count+1,'prediction_calls':len(calls),
        'complete_predictions':sum(c['status']=='complete' for c in calls),
        'deadline_misses':sum(c['status']=='deadline_exceeded' for c in calls),
        'activation_tick':activated,'end_state':summary['controller_state'],'hold_reason':summary['hold_reason'],
        'invalid_datagrams':summary['invalid_datagrams'],'message_guard':summary['message_guard'],
        'hold_time_s':(core.core.controller.hold_context or {}).get('time_s'),
        'reconfiguration':core.core.reconfiguration.summary(),
        'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest()}


def injected_deadline(original):
    """Controlled negative fixture, not an observed CPU timing measurement."""
    def rollout(self,*args,**kwargs):
        saved = self.clock; values = iter((0.,self.parameters['wall_budget_s']+1,self.parameters['wall_budget_s']+1))
        self.clock = lambda: next(values)
        try: return original(self,*args,**kwargs)
        finally: self.clock = saved
    return rollout


def study(output, plan_path=HERE/'experiments/predictive_replay_20261104.json', config_path=HERE/'configs/reconfigurable_cell_20261030.json'):
    plan = load_plan(plan_path); config = load_config(config_path)
    period = config['timing']['physics_step_s']*config['timing']['sample_steps']
    if config['timing']['run_budget_s']/period > 10000: raise ValueError('study limited to 10000 ticks per trial')
    if not config['prediction']['enabled'] or config['prediction'].get('backend','numeric_1d')!='numeric_1d' or config['prediction'].get('background',{}).get('enabled'):
        raise ValueError('study requires numeric_1d prediction and no asynchronous observer')
    if not plan['warning_delay_s'] < config['timing']['max_age_s'] < plan['stale_delay_s']:
        raise ValueError('plan delays must bracket profile max observation age')
    mapping = load_adapter(HERE/'configs/recording_map_example.json').settings
    # Simulation timestamps already use seconds. Avoid a synthetic seconds/ms round trip;
    # keep strict source <= reception validation unchanged in the production boundary.
    mapping['clock']['source_scale_s'] = 1.0
    output = Path(output); output.mkdir(parents=True,exist_ok=False); write(output/'plan.json',plan)
    trials = []; negative = None
    for repetition in range(plan['repetitions']):
        for case in CASES:
            name = f'{repetition+1:02}_{case}'; folder = output/name
            print('Predictive replay:',name,flush=True)
            result = capture(folder,config,mapping,case,plan,'study-'+name)
            result['name'] = name; result['replays'] = []
            for index in range(plan['replays_per_trial']):
                r = replay(folder,output/(name+f'_replay_{index+1}'))
                result['replays'].append({'passed':r['passed'],'mismatches':len(r['mismatch_tick_indices']),
                    'first_mismatch':r['mismatch_tick_indices'][0] if r['mismatch_tick_indices'] else None})
            if negative is None and case == 'nominal' and result['complete_predictions']:
                with patch.object(Predictor,'rollout',injected_deadline(Predictor.rollout)):
                    negative = replay(folder,output/'injected_deadline_replay')
                negative = {'detected':not negative['passed'],'mismatch_ticks':len(negative['mismatch_tick_indices']),
                    'first_mismatch':next(iter(negative['mismatch_fields'].items()),None),
                    'scope':'injected elapsed-time fixture, not measured latency or physical fault'}
            trials.append(result); write(output/'partial_trials.json',trials)
    comparisons = [r for t in trials for r in t['replays']]
    report = {'kind':'predictive_replay_study_v1','passed':all(t['prediction_calls'] and t['invalid_datagrams']==0 for t in trials) and
        all(r['passed'] for r in comparisons) and bool(negative and negative['detected']),
        'trials':trials,'trial_count':len(trials),'replay_count':len(comparisons),
        'matching_replays':sum(r['passed'] for r in comparisons),'negative_control':negative,
        'physical_validation':False,'physical_output':False,'parameter_tuning':False,
        'scope':'closed-loop virtual plant, synthetic packet schedule, strict feedback; replay uses fixed observations, not a new physical trajectory',
        'limits':['not actual UDP timing','no hardware calibration or fault-detection accuracy',
            'natural replay differences may reflect real compute deadlines','strict cycle stops before unconfirmed XY/vacuum actuation']}
    write(output/'predictive_replay_study.json',report)
    (output/'report.md').write_text('# Nghiên cứu phát lại trong pha dự báo\n\n'
        f"{len(trials)} phiên; {report['matching_replays']}/{len(comparisons)} lần phát lại giống kết quả logic.\n\n"
        f"Đối chứng chủ động ép quá hạn tính toán phát hiện được: {bool(negative and negative['detected'])}.\n\n"
        'Không coi tỷ lệ giống là độ chính xác phát hiện lỗi. Dữ liệu cảm biến sinh trong MuJoCo, '
        'gói được lập lịch trong bộ thử, không truyền UDP hoặc đi qua PLC. Tham số và ngưỡng sản phẩm giữ nguyên.\n',encoding='utf-8')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--plan',type=Path,default=HERE/'experiments/predictive_replay_20261104.json')
    p.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    a = p.parse_args(); raise SystemExit(int(not study(a.output,a.plan,a.config)['passed']))
