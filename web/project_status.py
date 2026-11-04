"""Read-only, bounded summary of existing results and implementation journal."""
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parent.parent
VI={'INIT':'Khởi tạo','FEED':'Cấp phôi','PUSH':'Đẩy phôi','RETRACT':'Thu xi lanh',
    'TRACK':'Theo dõi phôi','ALIGN':'Căn điểm gắp','LOWER':'Hạ đầu hút','GRIP':'Hút phôi',
    'LIFT':'Nâng phôi','MOVE':'Chuyển tới hộp','LOWER_BIN':'Hạ xuống hộp','RELEASE':'Thả phôi',
    'RAISE':'Nâng đầu hút','RETURN':'Về vị trí đầu','DONE':'Hoàn tất','HOLD':'Dừng chờ'}

def diagnostic(obj,name):
    if not isinstance(obj,dict):return None
    kind=obj.get('kind');passed=obj.get('passed')
    if kind=='model_boundary_v1':
        counts=obj.get('forward_decision_pairs',{})
        text=f"Đủ {obj.get('complete')}/{obj.get('planned')} đầu vào; bất đồng 1D chạy/tiếp xúc dừng: {counts.get('reduced_continue_contact_hold',0)}; ngược lại: {counts.get('reduced_hold_contact_continue',0)}."
        passed=None
    elif kind=='background_model_audit_v1':
        text=f"{obj.get('comparable_pairs')} cặp so được; {obj.get('invalid_records')} bản ghi sai. Cùng khuyến nghị chưa phải độ chính xác."
    elif kind=='stream_input_v1':
        text=f"{obj.get('datagrams')} gói; {obj.get('invalid_datagrams')} gói sai; cuối lượt {obj.get('controller_state')}: {obj.get('hold_reason')}. Chỉ ghi lệnh tệp."
    elif kind=='stream_replay_v1':
        text=f"Phát lại {obj.get('ticks')} nhịp; {len(obj.get('mismatch_tick_indices',[]))} nhịp khác. Không so thời gian tính toán."
    elif kind in ('stream_check_v1','software_check_v2','stream_archive_check_v1','stream_bundle_check_v1'):
        checks=obj.get('checks',{});text=f"{len(checks)} mục kiểm tra; xem báo cáo để biết phạm vi. Không kiểm chứng máy thật."
    else:return None
    return {'name':name,'kind':kind,'passed':passed,'summary_vi':text}

class ProjectStatus:
    def __init__(self,root=ROOT): self.root=Path(root); self.cached=None; self.updated=0
    def _json(self,path,limit=2*1024*1024):
        if path.is_symlink() or path.stat().st_size>limit: raise ValueError('file unavailable or too large')
        return json.loads(path.read_text(encoding='utf-8-sig'))
    def read(self):
        if self.cached is not None and time.monotonic()-self.updated<3: return self.cached
        manifest=self.root/'mujoco/software_release_v2.json'
        if not manifest.exists():manifest=self.root/'mujoco/implementation_manifest.json'
        state=self._json(manifest) if manifest.exists() else {'phase':'unknown','items':[]}
        output=self.root/'output/docker'; runs=[]; qualifications=[]; diagnostics=[]
        if output.exists():
            directories=sorted((p for p in output.iterdir() if p.is_dir() and not p.is_symlink() and not p.name.startswith('qualification_')),
                               key=lambda p:p.stat().st_mtime,reverse=True)[:24]
            for directory in directories:
                qualification=directory/'qualification.json'
                if qualification.is_file():
                    try:
                        q=self._json(qualification)
                        if q.get('kind')=='qualification_v1': qualifications.append({'name':directory.name,**q})
                    except (OSError,ValueError,TypeError): pass
                candidates=[directory/'summary.json']
                candidates += [p/'summary.json' for p in list(directory.iterdir())[:200] if p.is_dir() and not p.is_symlink()]
                for parent in [directory]+[p for p in list(directory.iterdir())[:200] if p.is_dir() and not p.is_symlink()]:
                    for filename in ('summary.json','boundary.json','audit.json','stream_check.json','software_check.json','replay.json','stream_archive_check.json'):
                        path=parent/filename
                        if not path.is_file():continue
                        try:
                            item=diagnostic(self._json(path),str(parent.relative_to(output)))
                            if item is not None:diagnostics.append(item)
                        except (OSError,ValueError,TypeError):pass
                for path in candidates:
                    if not path.is_file(): continue
                    try:
                        s=self._json(path)
                        if not isinstance(s,dict) or not s.get('controller_state'):continue
                        r=s.get('recovery_assessment',{})
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
        self.cached={'implementation':state,'runs':runs[:30],'qualifications':qualifications[:5],'diagnostics':diagnostics[:30],'journal':text,'physical_connection':False,
                     'scope':'chỉ đọc nhật ký và kết quả; không điều khiển máy hoặc chạy thí nghiệm'}
        self.updated=time.monotonic(); return self.cached
