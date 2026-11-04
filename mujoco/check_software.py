"""Inventory all six software items, then run the pre-hardware regression suite."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def inventory(root=ROOT):
    root=Path(root).resolve()
    manifest=json.loads((root/'mujoco/software_release_v2.json').read_text(encoding='utf-8'))
    if {i['id'] for i in manifest['items']}!={f'S{i:02}' for i in range(1,7)} or len(manifest['items'])!=6:raise ValueError('six software items required')
    files={}
    for item in manifest['items']:
        if item['status']!='implemented':raise ValueError('implement every item before running checks')
        for name in item['files']:
            p=(root/name).resolve()
            if not p.is_relative_to(root) or not p.is_file():raise ValueError('missing/unsafe implementation file: '+name)
            if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'))
            elif p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'))
            files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'items':manifest['items'],'files_sha256':files,'user_acceptance':'pending','limits':manifest['limits']}


def check(output):
    assembled=inventory()
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    report={'kind':'software_check_v2','passed':False,'inventory':assembled,'checks':{},
        'parameter_tuning':False,'physical_validation':False,'physical_output':False,'user_acceptance':'pending'}
    commands={'core_logic':[sys.executable,'-m','unittest','discover','-s','mujoco','-p','test_*.py'],
              'web_logic':[sys.executable,'-m','unittest','discover','-s','web','-p','test_*.py']}
    for name,script in [('stream','check_stream.py'),('integration','check_integration.py'),('reset','check_reset.py'),
                        ('background','check_background.py'),('boundary','study_model_boundary.py'),('qualification','qualify.py'),
                        ('stream_archive','check_stream_archive.py')]:
        commands[name]=[sys.executable,str(ROOT/'mujoco'/script),'--output',str(output/name)]
    for name,command in commands.items():
        print('Software check:',name,flush=True)
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,encoding='utf-8',errors='replace')
        (output/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        report['checks'][name]={'exit_code':result.returncode,'log':name+'.log'}
        (output/'partial_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        if result.returncode:print((result.stdout+result.stderr)[-1200:],flush=True)
    report['passed']=all(v['exit_code']==0 for v in report['checks'].values())
    report['scope']='pre-hardware software rehearsal; raw signals and commands are synthetic or logged only; no S7 driver or physical feedback qualification'
    (output/'software_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'report.md').write_text('# Kiểm tra tổng hợp phần mềm trước khi đo máy\n\n'
        'Sáu mục được kiểm kê trước khi chạy các phép thử. Các kết quả không đạt vẫn giữ lại trong tệp log.\n\n'+
        '\n'.join(f"- {k}: {'đạt' if v['exit_code']==0 else 'cần xem lại'}." for k,v in report['checks'].items())+
        '\n\nĐạt kiểm tra phần mềm không phải nghiệm thu của người dùng, hiệu chuẩn vật lý, kết nối S7 hoặc bảo đảm 20 ms. Không có lệnh gửi tới máy thật.\n',encoding='utf-8')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    raise SystemExit(int(not check(parser.parse_args().output)['passed']))
