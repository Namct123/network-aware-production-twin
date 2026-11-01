"""Read-only, bounded summary of existing results and implementation journal."""
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parent.parent
VI={'INIT':'Khởi tạo','FEED':'Cấp phôi','PUSH':'Đẩy phôi','RETRACT':'Thu xi lanh',
    'TRACK':'Theo dõi phôi','ALIGN':'Căn điểm gắp','LOWER':'Hạ đầu hút','GRIP':'Hút phôi',
    'LIFT':'Nâng phôi','MOVE':'Chuyển tới hộp','LOWER_BIN':'Hạ xuống hộp','RELEASE':'Thả phôi',
    'RAISE':'Nâng đầu hút','RETURN':'Về vị trí đầu','DONE':'Hoàn tất','HOLD':'Dừng chờ'}

class ProjectStatus:
    def __init__(self,root=ROOT): self.root=Path(root); self.cached=None; self.updated=0
    def _json(self,path,limit=2*1024*1024):
        if path.is_symlink() or path.stat().st_size>limit: raise ValueError('file unavailable or too large')
        return json.loads(path.read_text(encoding='utf-8-sig'))
    def read(self):
        if self.cached is not None and time.monotonic()-self.updated<3: return self.cached
        manifest=self.root/'mujoco/implementation_manifest.json'
        state=self._json(manifest) if manifest.exists() else {'phase':'unknown','items':[]}
        output=self.root/'output/docker'; runs=[]
        if output.exists():
            directories=sorted((p for p in output.iterdir() if p.is_dir() and not p.is_symlink() and not p.name.startswith('qualification_')),
                               key=lambda p:p.stat().st_mtime,reverse=True)[:24]
            for directory in directories:
                candidates=[directory/'summary.json']
                candidates += [p/'summary.json' for p in list(directory.iterdir())[:200] if p.is_dir() and not p.is_symlink()]
                for path in candidates:
                    if not path.is_file(): continue
                    try:
                        s=self._json(path); r=s.get('recovery_assessment',{})
                        runs.append({'name':str(path.parent.relative_to(output)),'state':s.get('controller_state'),
                            'state_vi':VI.get(s.get('controller_state'),'Chưa biết'),'reason':s.get('hold_reason'),
                            'simulation_time_s':s.get('simulation_time_s'),'placement_pass':s.get('placement_pass_evaluator_only'),
                            'session':s.get('session'),'message_guard':s.get('message_guard'),
                            'recovery_stage':r.get('stage') if r.get('enabled') else 'DISABLED',
                            'profile':s.get('profile_name'),'prediction_model':s.get('prediction',{}).get('model')})
                    except (OSError,ValueError,TypeError): continue
                if len(runs)>=30: break
        journal=self.root/'docs/nhat_ky_cong_viec.md'
        text=journal.read_text(encoding='utf-8') if journal.exists() and journal.stat().st_size<300000 else ''
        self.cached={'implementation':state,'runs':runs[:30],'journal':text,'physical_connection':False,
                     'scope':'chỉ đọc nhật ký và kết quả; không điều khiển máy hoặc chạy thí nghiệm'}
        self.updated=time.monotonic(); return self.cached
