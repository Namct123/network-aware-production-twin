"""Bounded local MuJoCo jobs. Request values never become shell commands or paths."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT/'mujoco'))
from config import load_config, validate_config
from build_replays import read_replay

PROFILES = {'simulation': 'simulation.json', 'slow_a2': 'slow_a2_demo.json'}
FAULTS = {'none', 'ps1_stuck_low', 'ps2_stuck_low', 'a1_extended_stuck_low'}


def validate_request(value):
    keys = {'profile', 'speed', 'fault', 'delay_ms', 'jitter_ms', 'loss_pct', 'seed',
            'bin', 'predictive', 'assume_open_loop', 'compare'}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError('Các tham số thí nghiệm thiếu hoặc không được hỗ trợ.')
    if type(value['profile']) is not str or value['profile'] not in PROFILES:
        raise ValueError('Profile không hợp lệ.')
    if type(value['fault']) is not str or value['fault'] not in FAULTS:
        raise ValueError('Lỗi cảm biến không được hỗ trợ.')
    bounds = {'speed': (.10, .24), 'delay_ms': (0, 200), 'jitter_ms': (0, 100), 'loss_pct': (0, 100)}
    for key, (low, high) in bounds.items():
        v=value[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not low<=v<=high:
            raise ValueError(f'{key}: cần số hữu hạn trong [{low}, {high}].')
    for key, low, high in [('seed',0,2147483647), ('bin',1,6)]:
        if type(value[key]) is not int or not low<=value[key]<=high:
            raise ValueError(f'{key}: cần số nguyên trong [{low}, {high}].')
    for key in ['predictive','assume_open_loop','compare']:
        if type(value[key]) is not bool:
            raise ValueError(f'{key}: cần boolean.')
    return deepcopy(value)


def trial_config(request, predictive):
    c=load_config(ROOT/'mujoco/configs'/PROFILES[request['profile']])
    c['motion']['long_speed_m_s']=request['speed']
    c['prediction']['enabled']=predictive
    c['network'].update(delay_s=request['delay_ms']/1000, jitter_s=request['jitter_ms']/1000,
                        drop_probability=request['loss_pct']/100, seed=request['seed'])
    return validate_config(c)


def write_json(path, value):
    path=Path(path)
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False),encoding='utf-8')
    temporary.replace(path)


def paired_comparison(a,b):
    # Only hold times of the same stop-margin vs missing-PS2 timeout fixture are
    # comparable as an earlier-stop observation. Other HOLDs have different causes.
    same_ps2=(a['hold_reason']=='timeout:TRACK:ps2' and
              b['hold_reason']=='predictive_stop_margin')
    return {'baseline_state':a['controller_state'], 'predictive_state':b['controller_state'],
            'earlier_hold_s':a['hold_time_s']-b['hold_time_s'] if same_ps2 else None,
            'cycle_time_delta_s':a['simulation_time_s']-b['simulation_time_s']
                if a['controller_state']==b['controller_state']=='DONE' and
                   a['placement_pass_evaluator_only'] is True and b['placement_pass_evaluator_only'] is True else None,
            'scope':'one paired simulation; not fault accuracy, physical speedup, or a safety proof'}


def worker(request_path, folder):
    from experiment import run
    request=validate_request(json.loads(Path(request_path).read_text(encoding='utf-8')))
    folder=Path(folder)
    trials=[('baseline',False),('predictive',True)] if request['compare'] else [
        ('predictive' if request['predictive'] else 'baseline', request['predictive'])]
    results=[]
    for number,(name,enabled) in enumerate(trials,1):
        write_json(folder/'progress.json',{'trial':name,'number':number,'total':len(trials),'stage':'simulating'})
        summary=run(folder/name,bin_number=request['bin'],assume_open_loop=request['assume_open_loop'],
                    fault=request['fault'], config=trial_config(request,enabled))
        label=f'Thí nghiệm mới · {name} · {request["fault"]}'
        replay=read_replay(folder/name, folder.name+'_'+name, label)
        write_json(folder/f'{name}_replay.json',replay)
        results.append({'trial':name,'summary':summary})
    result={'trials':results,'comparison':paired_comparison(results[0]['summary'],results[1]['summary'])
            if request['compare'] else None}
    write_json(folder/'result.json',result)
    write_json(folder/'progress.json',{'stage':'finished','number':len(trials),'total':len(trials)})


def wsl_path(path):
    path=Path(path).resolve()
    if not re.fullmatch(r'[A-Za-z]:',path.drive):
        raise ValueError('WSL runner cần đường dẫn ổ đĩa Windows cục bộ.')
    return '/mnt/'+path.drive[0].lower()+path.as_posix()[2:]


class BusyError(RuntimeError):
    pass


class Experiments:
    def __init__(self, enabled=False, distro='Ubuntu-24.04', python='/home/admin/dt-cpps-venv/bin/python', directory=None):
        self.enabled=enabled
        self.distro=distro
        self.python=python
        self.directory=Path(directory) if directory else ROOT/'output/web_experiments'
        self.lock=threading.Lock()
        self.active=None

    def capabilities(self):
        return {'enabled':self.enabled,'backend':'WSL MuJoCo', 'distro':self.distro,
                'active_job':self.active,'wall_timeout_s':150,'host_timeout_s':170,
                'note':'Chạy mô phỏng mới; kết quả có thể HOLD hoặc đặt phôi không đạt. Không kết nối PLC.'}

    def folder(self, job):
        if not re.fullmatch(r'[a-f0-9]{32}',job):
            raise ValueError('ID không hợp lệ.')
        return self.directory/job

    def submit(self, value):
        request=validate_request(value)
        if not self.enabled:
            raise BusyError('Chưa bật bộ chạy WSL. Mở START_SIMULATION_EXPLORER.cmd trên máy đã có MuJoCo WSL.')
        with self.lock:
            if self.active:
                raise BusyError('Đang có một thí nghiệm chạy. Hãy chờ kết quả.')
            job=uuid.uuid4().hex
            folder=self.folder(job)
            folder.mkdir(parents=True,exist_ok=False)
            status={'id':job,'state':'queued','created_at':datetime.now(timezone.utc).isoformat(),
                    'request':request,'result':None,'error':None}
            write_json(folder/'request.json',request)
            write_json(folder/'job.json',status)
            self.active=job
            threading.Thread(target=self.execute,args=(job,),daemon=True).start()
        return self.status(job)

    def status(self, job):
        folder=self.folder(job)
        status=json.loads((folder/'job.json').read_text(encoding='utf-8'))
        if (folder/'progress.json').is_file():
            status['progress']=json.loads((folder/'progress.json').read_text(encoding='utf-8'))
        if status['state'] in {'running','queued'} and job!=self.active:
            status['state']='interrupted'
            status['error']='Máy chủ đã khởi động lại. Không coi lượt dở dang là kết quả hoàn tất.'
        return status

    def recent(self):
        if not self.directory.exists(): return []
        paths=sorted(self.directory.glob('*/job.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:20]
        rows=[]
        for path in paths:
            try:
                row=self.status(path.parent.name)
                rows.append(row)
            except (ValueError,OSError):
                continue
        return rows

    def execute(self, job):
        folder=self.folder(job)
        status=self.status(job)
        try:
            status['state']='running'
            write_json(folder/'job.json',status)
            if not shutil.which('wsl'):
                raise RuntimeError('Không tìm thấy WSL. Chỉ phát lại và phòng dự báo 1D vẫn dùng được.')
            command=['wsl','-d',self.distro,'--','timeout','--signal=TERM','--kill-after=5s','150s',
                     self.python,'-u',wsl_path(HERE/'experiments.py'),'--worker',
                     wsl_path(folder/'request.json'),'--output',wsl_path(folder)]
            # ponytail: one bounded job at a time; use a persistent queue only if
            # this becomes a multi-user service. No shell and no user command text.
            with (folder/'worker.log').open('wb') as log:
                process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=170,
                                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if process.returncode:
                raise RuntimeError(f'WSL worker kết thúc mã {process.returncode}. Xem worker.log trong thư mục thí nghiệm.')
            status['result']=json.loads((folder/'result.json').read_text(encoding='utf-8'))
            status['state']='completed'
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as error:
            status.update(state='failed',error=str(error))
        finally:
            status['finished_at']=datetime.now(timezone.utc).isoformat()
            try:
                write_json(folder/'job.json',status)
            finally:
                with self.lock: self.active=None


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    worker(args.worker,args.output)
