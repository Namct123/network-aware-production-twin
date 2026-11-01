"""Snapshot all implementation items first; optional checks run only after all are written."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent

def inventory(root=ROOT):
    root=Path(root).resolve()
    manifest=json.loads((root/'mujoco/implementation_manifest.json').read_text(encoding='utf-8'))
    if len(manifest['items'])!=6 or {i['id'] for i in manifest['items']}!={'M01','M02','M03','M04','M05','M06'}:
        raise ValueError('six implementation items required')
    files={}
    for item in manifest['items']:
        if item['status']!='implemented': raise ValueError('all items must be implemented before checks: '+item['id'])
        for name in item['files']:
            p=(root/name).resolve()
            if not p.is_relative_to(root) or not p.is_file() or p.stat().st_size==0: raise ValueError('missing/unsafe implementation file: '+name)
            if p.suffix=='.py': ast.parse(p.read_text(encoding='utf-8-sig'),filename=name)
            if p.suffix=='.json': json.loads(p.read_text(encoding='utf-8-sig'))
            files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'phase':'implementation_complete_not_experimentally_validated','batch_id':manifest['batch_id'],
            'items':manifest['items'],'files':files,'user_acceptance':'pending','physical_validation':False,
            'limits':manifest['limits']}

def assemble(output,validate=False):
    report=inventory()
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    (output/'assembly.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report['checks']={}
    if validate:
        commands={'logic':[sys.executable,'-m','unittest','discover','-s','mujoco','-p','test_*.py'],
                  'integration':[sys.executable,'mujoco/check_integration.py','--output',str(output/'integration')]}
        for name,cmd in commands.items():
            r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
            (output/(name+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
            report['checks'][name]={'exit_code':r.returncode,'log':str(output/(name+'.log'))}
        report['phase']='checks_passed_no_parameter_tuning' if all(r['exit_code']==0 for r in report['checks'].values()) else 'checks_need_attention'
    (output/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'report.md').write_text('# Bản ghép phần mềm số 1\n\n'
        'Sáu mục đã được viết và ghép trước khi cho phép chạy kiểm tra. Chưa tối ưu thông số trong bước này.\n\n'
        +'\n'.join(f"- {i['id']}: {i['title_vi']} — đã triển khai." for i in report['items'])
        +'\n\nKết quả kiểm tra, nếu được yêu cầu, nằm trong validation.json. Không có kết luận đã nghiệm thu trên máy thật.\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--validate',action='store_true',help='Run checks only after all six items are implemented')
    a=p.parse_args(); r=assemble(a.output,a.validate)
    print(r['phase'],flush=True)
    raise SystemExit(int(r['phase']=='checks_need_attention'))
