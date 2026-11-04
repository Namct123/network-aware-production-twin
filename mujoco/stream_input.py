"""Loopback UDP input rehearsal. Commands are logged locally, never transmitted."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import socket
import time
from config import exact_keys,load_config,number
from io_adapter import RecordingAdapter,load_adapter,readiness
from runtime import RuntimeCore

HERE=Path(__file__).resolve().parent
MAX_DATAGRAM=16384


def reject_constant(value):raise ValueError('nonfinite JSON constant: '+value)


class StreamCore:
    def __init__(self,config,mapping,session_id,generation=0):
        self.adapter=RecordingAdapter(mapping)
        self.core=RuntimeCore(config,session_context={'session_id':session_id,'generation':generation},clock_domain='mapped_recording')
        self.received=0;self.invalid=0;self.ticks=0;self.finished=False

    def tick(self,packet,now):
        if self.finished:raise RuntimeError('stream already finished')
        message=None;notes=[];error=None
        if packet is not None:
            self.received+=1
            try:
                if len(packet)>MAX_DATAGRAM:raise ValueError('datagram exceeds 16 KiB')
                row=json.loads(packet.decode('utf-8'),parse_constant=reject_constant)
                exact_keys(row,('session_id','generation','sequence','source_time','values','quality'),'stream row')
                # The sender cannot supply or override local reception time.
                message,notes=self.adapter.convert({**row,'received_time_s':now})
            except (ValueError,TypeError,UnicodeError,KeyError) as exc:
                self.invalid+=1;error=f'{type(exc).__name__}: {exc}'[:256]
        step=self.core.step(message,now);self.ticks+=1
        return {'time_s':now,'input_error':error,'notes':notes,'input_guard':step['input_guard'],
            'phase':self.core.controller.phase,'hold_reason':self.core.controller.reason,
            'command_message':step['command_message'],'physical_output':False,'core_step_ms':step['step_compute_ms']}

    def finish(self,now):
        if self.finished:return None
        if self.core.controller.phase!='DONE':self.core.stop('stream_finished',now)
        step=self.core.step(None,now);self.finished=True
        return {'time_s':now,'command_message':step['command_message'],'physical_output':False,'final':True}

    def close(self):self.core.close()

    def summary(self):
        return {'kind':'stream_input_v1','controller_state':self.core.controller.phase,'hold_reason':self.core.controller.reason,
            'session':self.core.context,'datagrams':self.received,'invalid_datagrams':self.invalid,'ticks':self.ticks,
            'message_guard':{'accepted':self.core.guard.accepted,'rejected':self.core.guard.rejected},
            'mapping_readiness':readiness(self.adapter.settings),'physical_output_supported':False,
            'local_loopback_only':True,'physical_validation':False,
            'scope':'UDP tag-contract rehearsal through mapped-recording clock semantics; no S7 driver, PLC actuation or physical clock synchronization'}


def receive(output,config,mapping,session_id,generation=0,port=0,duration_s=5,on_ready=None):
    number(duration_s,'duration_s',0,True)
    if duration_s>60 or type(port) is not int or not 0<=port<=65535:raise ValueError('duration <=60 s and valid local UDP port required')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    core=StreamCore(config,mapping,session_id,generation)
    period=config['timing']['physics_step_s']*config['timing']['sample_steps']
    def write(name,obj):(output/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    origin=time.perf_counter();late=0;max_lateness=0.;failure=None
    try:
        write('effective_config.json',config);write('mapping.json',mapping)
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock, (output/'raw_datagrams.jsonl').open('w',encoding='utf-8') as raw, (output/'commands_dry_run.jsonl').open('w',encoding='utf-8') as log:
            sock.bind(('127.0.0.1',port));sock.setblocking(False)
            origin=time.perf_counter()
            info={'host':'127.0.0.1','port':sock.getsockname()[1],'clock_origin_monotonic_s':origin,
                'session_id':session_id,'generation':generation,'duration_s':duration_s,'physical_output_supported':False}
            write('receiver.json',info)
            if on_ready:on_ready(info)
            next_tick=origin
            while True:
                time.sleep(max(0,next_tick-time.perf_counter()))
                now=time.perf_counter()-origin
                if now>duration_s:break
                lateness=max(0,origin+now-next_tick);max_lateness=max(max_lateness,lateness)
                if lateness>period:late+=1
                try:packet,peer=sock.recvfrom(MAX_DATAGRAM+1)
                except BlockingIOError:packet=None
                if packet is not None:raw.write(json.dumps({'time_s':now,'bytes_b64':base64.b64encode(packet).decode(),'peer':peer})+'\n')
                result=core.tick(packet,now);log.write(json.dumps(result,allow_nan=False)+'\n');log.flush()
                # No unbounded catch-up loop when the OS or computation falls behind.
                next_tick=max(next_tick+period,origin+now)
            final=core.finish(max(core.core.last_now or 0,time.perf_counter()-origin))
            if final:log.write(json.dumps(final,allow_nan=False)+'\n')
    except Exception as exc:
        failure=f'{type(exc).__name__}: {exc}'[:512]
        try:
            final=core.finish(max(core.core.last_now or 0,time.perf_counter()-origin))
            write('aborted_final_command_dry_run.json',final)
        except Exception as stop_error:write('abort_error.json',{'error':str(stop_error)[:256],'physical_output':False})
        raise
    finally:
        core.close()
        summary={**core.summary(),'elapsed_wall_s':time.perf_counter()-origin,'late_ticks':late,'max_tick_lateness_s':max_lateness,
            'failure':failure,'user_acceptance':'pending','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}}
        write('summary.json',summary)
    (output/'report.md').write_text('# Nhận dữ liệu mẫu liên tục\n\n'
        f"Nhận {summary['datagrams']} gói, sai định dạng {summary['invalid_datagrams']}. Trạng thái cuối {summary['controller_state']}: {summary['hold_reason']}.\n\n"
        'Thời điểm nhận được ghi tại cổng. Thiếu gói vẫn chạy kiểm tra im lặng. Dữ liệu trở lại không tự xóa HOLD. Các lệnh chỉ ghi tệp, không gửi tới thiết bị.\n\n'
        'Đây là thử hợp đồng dữ liệu qua UDP trên cùng máy, chưa phải trình đọc S7, kết nối PLC hay đồng bộ đồng hồ vật lý. Không bảo đảm chu kỳ thời gian thực.\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--config',type=Path,default=HERE/'configs/reconfigurable_cell_20261030.json')
    parser.add_argument('--mapping',type=Path,default=HERE/'configs/recording_map_unverified.json')
    parser.add_argument('--session',required=True);parser.add_argument('--generation',type=int,default=0)
    parser.add_argument('--port',type=int,default=0);parser.add_argument('--duration',type=float,default=5)
    args=parser.parse_args()
    receive(args.output,load_config(args.config),load_adapter(args.mapping).settings,args.session,args.generation,args.port,args.duration)
