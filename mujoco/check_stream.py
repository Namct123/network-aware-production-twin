"""Real loopback UDP plus deterministic signal fixtures; no physical equipment."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from queue import Queue
import socket
import threading
import time
from config import load_config
from io_adapter import load_adapter
from stream_input import receive

HERE=Path(__file__).resolve().parent


def sample(info,sequence):
    values={'PS1_pusher':False,'PS2_upstream':False,'PS3_pickup':False,'A1_back':True,'A1_front':False,'A2_up':True,'A2_down':False}
    return {'session_id':info['session_id'],'generation':info['generation'],'sequence':sequence,
        'source_time':max(0,time.perf_counter()-info['clock_origin_monotonic_s'])*1000,
        'values':values,'quality':{k:'good' for k in values}}


def check(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    config=load_config(HERE/'configs/reconfigurable_cell_20261030.json')
    results={};checks={}
    for name in ('gap_then_return','bad_and_repeated','unverified_mapping'):
        mapping=load_adapter(HERE/'configs'/('recording_map_unverified.json' if name=='unverified_mapping' else 'recording_map_example.json')).settings
        ready=Queue();errors=[]
        def serve():
            try:results[name]=receive(output/name,config,mapping,'stream-check',duration_s=.65,on_ready=ready.put)
            except Exception as error:errors.append(str(error))
        thread=threading.Thread(target=serve,daemon=True);thread.start()
        info=ready.get(timeout=5)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sender:
            target=(info['host'],info['port'])
            def send(row):sender.sendto(json.dumps(row).encode(),target)
            first=sample(info,0);send(first);time.sleep(.045)
            if name=='bad_and_repeated':
                send(first);time.sleep(.04)
                wrong=sample(info,1);wrong['session_id']='old';send(wrong);time.sleep(.04)
                sender.sendto(b'not-json',target);time.sleep(.04)
                send(sample(info,2))
            elif name=='gap_then_return':
                send(sample(info,1));time.sleep(.3);send(sample(info,2))
        thread.join(5)
        if thread.is_alive() or errors:raise RuntimeError('stream receiver failed: '+str(errors))
        r=results[name]
        commands=[json.loads(s) for s in (output/name/'commands_dry_run.jsonl').read_text().splitlines()]
        checks[name]=r['controller_state']=='HOLD' and all(c['physical_output'] is False for c in commands)
        if name=='gap_then_return':checks[name]&=r['hold_reason']=='telemetry_timeout' and r['datagrams']==3
        elif name=='bad_and_repeated':checks[name]&=r['invalid_datagrams']==1 and r['message_guard']['rejected']>=2
        else:checks[name]&=r['hold_reason'].startswith('invalid_or_stale:')
    report={'kind':'stream_check_v1','passed':all(checks.values()),'checks':checks,'summaries':results,'physical_validation':False,'physical_output':False}
    (output/'stream_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'report.md').write_text('# Kiểm tra cổng dữ liệu mẫu\n\n'+'\n'.join(f"- {k}: {'đạt' if v else 'cần xem lại'}" for k,v in checks.items())+'\n\nCác gói chỉ đi qua loopback trên máy, các lệnh không được gửi tới PLC.\n',encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(int(not check(parser.parse_args().output)['passed']))
