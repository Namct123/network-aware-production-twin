"""Acceptance against the running local server and actual WSL MuJoCo, not mocks."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent.parent
BASE={'profile':'simulation','speed':.16,'fault':'none','delay_ms':0,'jitter_ms':0,'loss_pct':0,
      'seed':0,'bin':1,'predictive':True,'assume_open_loop':True,'compare':True}


def check(url, output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    def api(path, body=None):
        req=Request(url+path,json.dumps(body).encode() if body is not None else None,
                    {'Content-Type':'application/json'})
        with urlopen(req,timeout=15) as response:return json.load(response)
    rows=[]
    for name,changes,expected,reason in [
        ('nominal_pair',{},'DONE',''),
        ('ps2_pair',{'fault':'ps2_stuck_low'},'HOLD',None),
        ('strict_single',{'compare':False,'assume_open_loop':False},'HOLD','unconfirmed_xy_a2_midstroke_and_vacuum'),
        ('loss_pair',{'loss_pct':100},'HOLD','telemetry_timeout')]:
        job=api('/api/experiments',{**BASE,**changes})
        start=time.monotonic()
        while job['state'] in {'queued','running'} and time.monotonic()-start<180:
            time.sleep(1)
            job=api('/api/experiments/'+job['id'])
        passed=job['state']=='completed'
        configs=[]
        if passed:
            for trial in job['result']['trials']:
                s=trial['summary']
                passed &= s['controller_state']==expected
                if reason is not None:passed &= s['hold_reason']==reason
                passed &= (s['placement_pass_evaluator_only'] is True if expected=='DONE'
                           else s['hold_product_supported_evaluator_only'] is True)
                replay=api(f'/api/experiments/{job["id"]}/replay/{trial["trial"]}')
                configs.append(replay['config'])
                assert len(replay['frames'])==len(replay['truth'])
                folder=(ROOT/replay['source']).resolve()
                assert folder.is_relative_to(ROOT/'output/web_experiments')
                for file,digest in replay['sha256'].items():
                    assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==digest
                for file,digest in replay['manifest']['source_sha256'].items():
                    assert hashlib.sha256((ROOT/'mujoco'/file).read_bytes()).hexdigest()==digest
            if len(configs)==2:
                configs[0]['prediction']['enabled']=True
                assert configs[0]==configs[1], 'Pair changed more than prediction enable'
            if name=='ps2_pair':
                passed &= abs(job['result']['comparison']['earlier_hold_s']-.04)<1e-8
        rows.append({'case':name,'pass':bool(passed),'job':job})
        (output/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'{name}: {"PASS" if passed else "FAIL"}; {job["id"]}; {job["state"]}',flush=True)
        if not passed:raise AssertionError('Inspect saved job and worker logs; do not change expected outcome')
    print(f'PASS {len(rows)}/{len(rows)} real server/WSL cases',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8765')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    check(args.url,args.output)
