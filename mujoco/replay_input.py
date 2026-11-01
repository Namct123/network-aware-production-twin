"""Run the shared core against recorded inputs. Writes a dry-run outbox only."""
import argparse
import hashlib
import json
from pathlib import Path
from config import load_config
from io_adapter import load_adapter,readiness
from runtime import RuntimeCore
from experiment import write_json

def replay(source,mapping,config,output,allow_open_loop=False):
    source=Path(source); output=Path(output)
    if source.stat().st_size>64*1024*1024: raise ValueError('recording exceeds 64 MiB')
    adapter=load_adapter(mapping)
    lines=source.read_text(encoding='utf-8-sig').splitlines()
    if not lines or len(lines)>100000: raise ValueError('recording requires 1..100000 rows')
    prepared=[]
    for line in lines:
        if line.strip(): prepared.append(adapter.convert(json.loads(line)))
    if not prepared: raise ValueError('empty recording')
    first=prepared[0][0]
    core=RuntimeCore(config,assume_open_loop=allow_open_loop,
                     session_context={'session_id':first.session_id,'generation':first.generation},clock_domain='mapped_recording')
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'mapping.json',adapter.settings); write_json(output/'effective_config.json',config)
    with (output/'normalized.jsonl').open('w',encoding='utf-8') as normalized, (output/'commands_dry_run.jsonl').open('w',encoding='utf-8') as commands:
        for message,notes in prepared:
            step=core.step(message,message.received_time_s)
            normalized.write(json.dumps({'message':message.as_dict(),'notes':notes,'guard':step['input_guard']},ensure_ascii=False)+'\n')
            commands.write(json.dumps({'command_message':step['command_message'],'physical_output':False},ensure_ascii=False)+'\n')
        if core.controller.phase!='DONE':
            at=core.last_now+config['timing']['physics_step_s']*config['timing']['sample_steps']
            core.stop('recording_finished',at)
            step=core.step(None,at)
            commands.write(json.dumps({'command_message':step['command_message'],'physical_output':False},ensure_ascii=False)+'\n')
    summary={'controller_state':core.controller.phase,'hold_reason':core.controller.reason,'session':core.context,
        'rows':len(prepared),'physical_output_supported':False,'mapping_readiness':readiness(adapter.settings),
        'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mapping_sha256':hashlib.sha256(Path(mapping).read_bytes()).hexdigest(),
        'message_guard':{'accepted':core.guard.accepted,'rejected':core.guard.rejected},
        'scope':'recorded-input dry run only; no plant ground truth, placement grading or hardware actuation'}
    write_json(output/'summary.json',summary)
    (output/'report.md').write_text('# Đọc lại dữ liệu đã ghi\n\n'
        f"Đã nhận {len(prepared)} dòng. Trạng thái cuối: {core.controller.phase} (HOLD nghĩa là dừng chờ).\n\n"
        'Các lệnh chỉ được ghi vào tệp, không gửi tới máy thật. Không có đáp án vị trí thật để chấm việc đặt phôi.\n\n'
        'Tín hiệu hoặc đồng hồ chưa được xác nhận sẽ giữ trạng thái chưa có nguồn dùng được. Kết thúc bản ghi không đồng nghĩa hoàn tất chu trình.\n',encoding='utf-8')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input',type=Path,required=True)
    p.add_argument('--mapping',type=Path,required=True); p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True); p.add_argument('--allow-open-loop',action='store_true')
    a=p.parse_args(); replay(a.input,a.mapping,load_config(a.config),a.output,a.allow_open_loop)
