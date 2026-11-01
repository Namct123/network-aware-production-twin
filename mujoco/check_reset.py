"""Simulation reset/start demonstration: two plant runs plus separate message probes."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import uuid
from config import load_config
from experiment import run,write_json
from reset_protocol import ResetCoordinator,CONFIRMATIONS,digest,validate_settings

HERE=Path(__file__).parent
SETTINGS=HERE/'experiments/reset_protocol.json'
DEFAULT=HERE/'configs/hold_review_cell_20261031.json'

def reset_message(c,profile_hash,t):
    return {'environment':'simulation','session_id':c.session_id,'request_id':'reset_1','generation':c.generation,
        'issued_at_s':t,'hold_id':c.hold_id,'profile_sha256':profile_hash,
        'operator_confirmations':dict.fromkeys(CONFIRMATIONS,True)}

def ack_message(c,p,t,scene='probe_scene'):
    return {'environment':'simulation','session_id':c.session_id,'request_id':p['request_id'],
        'previous_generation':c.generation,'new_generation':c.generation+1,'profile_sha256':p['profile_sha256'],
        'scene_id':scene,'reset_complete':True,'ack_at_s':t}

def start_message(c,a,t):
    return {'environment':'simulation','session_id':c.session_id,'request_id':'start_1','generation':c.generation,
        'issued_at_s':t,'profile_sha256':c.profile_sha,'reset_ticket':a['reset_ticket']}

LABELS={
 'complete':'Đúng trình tự: đặt lại, xác nhận, rồi bắt đầu riêng',
 'missing_check':'Thiếu một xác nhận của người kiểm tra',
 'blocked_review':'Chưa đủ điều kiện để xem xét khôi phục',
 'expired_review':'Bản đánh giá sau dừng đã quá cũ',
 'early_start':'Gửi lệnh bắt đầu trước khi đặt lại được xác nhận',
 'ack_wrong_id':'Xác nhận nhầm yêu cầu',
 'ack_wrong_epoch':'Xác nhận nhầm số lần khởi tạo',
 'ack_wrong_profile':'Xác nhận nhầm bộ thông số',
 'ack_wrong_session':'Xác nhận thuộc phiên làm việc khác',
 'ack_late':'Xác nhận đặt lại đến quá muộn',
 'ack_missing':'Không nhận được xác nhận, hết thời gian chờ',
 'ack_failed':'Bên nhận báo chưa đặt lại thành công',
 'start_old_epoch':'Lệnh bắt đầu dùng số lần khởi tạo cũ',
 'start_wrong_ticket':'Lệnh bắt đầu không gắn với xác nhận hợp lệ',
 'start_duplicate':'Lệnh bắt đầu bị gửi lặp: chỉ được lấy quyền chạy một lần'}

def message_probes(settings,review,profile_hash):
    results=[]; t=review['time_s']
    for name,label in LABELS.items():
        r=deepcopy(review)
        if name=='blocked_review': r['stage']='MANUAL_INTERVENTION'
        if name=='expired_review': r['time_s']=t-settings['review_max_age_s']-.1
        c=ResetCoordinator(settings,r,session_id='probe_'+name)
        p=reset_message(c,profile_hash,t+.01); claims=0; checked=None
        if name=='missing_check': p['operator_confirmations']['local_interlocks_checked']=False
        if name=='early_start':
            a={'reset_ticket':'not_confirmed'}; checked=c.handle('start',start_message(c,a,t+.01),t+.01)
        else:
            response=c.handle('reset',p,t+.01)
            if name in {'missing_check','blocked_review','expired_review'}: checked=response
            else:
                a=ack_message(c,p,t+.02)
                if name=='ack_wrong_id': a['request_id']='old_reset'
                if name=='ack_wrong_epoch': a['new_generation']=9
                if name=='ack_wrong_profile': a['profile_sha256']='f'*64
                if name=='ack_wrong_session': a['session_id']='old_session'
                if name=='ack_failed': a['reset_complete']=False
                at=t+.02
                if name=='ack_late': at=t+.02+settings['reset_ack_timeout_s']; a['ack_at_s']=at
                if name=='ack_missing':
                    c.poll(t+.02+settings['reset_ack_timeout_s'])
                    response=c.events[-1]
                else:
                    response=c.handle('ack',a,at)
                if name.startswith('ack_'): checked=response
                else:
                    s=start_message(c,response,t+.03)
                    if name=='start_old_epoch': s['generation']=0
                    if name=='start_wrong_ticket': s['reset_ticket']='wrong'
                    response=c.handle('start',s,t+.03); checked=response
                    if c.take_start() is not None: claims+=1
                    if name=='start_duplicate':
                        checked=c.handle('start',s,t+.04)
                        if c.take_start() is not None: claims+=1
        expected_claims=1 if name in {'complete','start_duplicate'} else 0
        passed=(checked['accepted']==(name=='complete') and claims==expected_claims
                and all(e['old_cycle_resume_allowed'] is False for e in c.events))
        results.append({'case':name,'description_vi':label,'pass':passed,'stage':c.stage,
                        'start_claim_count':claims,'last_response':checked,'events':c.events,'scope':'message_protocol_only'})
    return results

def check(output,base=None,settings=None):
    base=load_config(DEFAULT) if base is None else base
    settings=json.loads(SETTINGS.read_text()) if settings is None else settings
    validate_settings(settings)
    if not base.get('recovery',{}).get('enabled'): raise ValueError('Review-enabled profile required')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    before=deepcopy(base); before['prediction']['wall_budget_s']=1.0
    before['network']['outage_windows_s']=[[5.4,5.56]]
    after=deepcopy(before); after['network']['outage_windows_s']=[]
    write_json(output/'settings.json',settings)
    write_json(output/'before_config.json',before); write_json(output/'after_config.json',after)
    from run_cell import Cell
    shared_session=uuid.uuid4().hex
    old_cell=Cell(before)
    held=run(output/'held_cycle',config=before,assume_open_loop=True,prepared_cell=old_cell,session_context={"session_id":shared_session,"generation":0})
    assert held['controller_state']=='HOLD' and held['recovery_assessment']['stage']=='OPERATOR_REVIEW'
    old_state=deepcopy(old_cell.observe())
    review=held['recovery_assessment']['latest']; t=review['time_s']
    probes=message_probes(settings,review,digest(after)); write_json(output/'message_cases.json',probes)
    assert all(r['pass'] for r in probes),'Inspect message_cases.json'
    coordinator=ResetCoordinator(settings,review,session_id=shared_session)
    request=reset_message(coordinator,digest(after),t+.01)
    response=coordinator.handle('reset',request,t+.01); assert response['accepted']
    # Simulator-side action: create a separate fresh scene, never reset/move old_cell.
    new_cell=Cell(after); scene_id='scene_'+uuid.uuid4().hex
    assert new_cell is not old_cell and new_cell.data.time==0 and new_cell.last_command is None
    ack=ack_message(coordinator,request,t+.02,scene_id)
    accepted=coordinator.handle('ack',ack,t+.02); assert accepted['accepted']
    assert coordinator.take_start() is None  # Confirmation alone cannot start.
    started=coordinator.handle('start',start_message(coordinator,accepted,t+.03),t+.03)
    assert started['accepted']
    grant=coordinator.take_start(); assert grant and grant['scene_id']==scene_id and grant['profile_sha256']==digest(new_cell.config)
    write_json(output/'handshake_before_start.json',{'environment':'simulation','simulated_operator_confirmations':True,
        'request':request,'ack':ack,'grant':grant,'events':coordinator.events,'old_cycle_resume_allowed':False})
    completed=run(output/'new_cycle',config=after,assume_open_loop=True,prepared_cell=new_cell,session_context={"session_id":grant["session_id"],"generation":grant["generation"]})
    assert completed['controller_state']=='DONE' and completed['placement_pass_evaluator_only'] is True
    assert coordinator.take_start() is None
    coordinator.finish(scene_id,True,t+.03+completed['simulation_time_s'])
    assert old_cell.observe()==old_state,'Old held scene must remain unchanged'
    reuse_rejected=False
    try: run(output/'forbidden_reuse',config=after,prepared_cell=new_cell)
    except ValueError: reuse_rejected=True
    assert reuse_rejected and not (output/'forbidden_reuse').exists()
    receipt={'session_id':coordinator.session_id,'environment':'simulation',
        'simulated_operator_confirmations':True,'settings':settings,'request':request,'ack':ack,'grant':grant,
        'events':coordinator.events,'stage':coordinator.stage,'held_cycle_state':held['controller_state'],
        'new_cycle_state':completed['controller_state'],'new_cycle_placement':completed['placement_pass_evaluator_only'],
        'old_scene_unchanged':True,'prepared_scene_reuse_rejected':reuse_rejected,
        'physical_runs':2,'message_cases':len(probes),'message_case_failures':sum(not r['pass'] for r in probes),
        'old_cycle_resume_allowed':False,
        'scope':'simulation-only separate new-cycle reset demonstration; synthetic human confirmations; no real PLC, authentication, old-product resume or physical safety proof'}
    write_json(output/'receipt.json',receipt)
    write_json(output/'study_manifest.json',{'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'protocol_sha256':hashlib.sha256((HERE/'reset_protocol.py').read_bytes()).hexdigest(),'before_config_sha256':digest(before),
        'after_config_sha256':digest(after),'settings_sha256':digest(settings)})
    lines=['# Báo cáo thử đặt lại và chạy một chu trình mới','',
        'Phạm vi: chỉ mô phỏng. Các xác nhận của người kiểm tra trong phép thử được tạo giả lập, không phải xác nhận ngoài máy thật.','',
        'Có **2 lượt mô phỏng chuyển động bằng MuJoCo** (phần mềm mô phỏng cơ học): lượt đầu dừng chờ do mất dữ liệu; lượt sau khởi tạo riêng và đặt phôi thành công.',
        '**Không tiếp tục phôi của lượt cũ.** Cảnh cũ giữ nguyên sau dừng. Lỗi mất dữ liệu đã được bỏ khỏi cấu hình lượt mới một cách công khai, không phải hệ thống tự sửa mạng.','',
        f"Có {len(probes)} tình huống thử bản tin riêng, không tính thành {len(probes)} lượt máy chạy thật.",'',
        '| Tình huống | Kết quả đúng yêu cầu | Số lần lấy quyền chạy mới |', '|---|---|---:|']
    for r in probes: lines.append(f"| {r['description_vi']} | {'Đạt' if r['pass'] else 'Chưa đạt'} | {r['start_claim_count']} |")
    lines+=['','## Trình tự đã thực hiện','',
        '1. Lượt cũ đang theo dõi phôi thì mất dữ liệu ngắn; bộ điều khiển dừng chờ (HOLD).',
        '2. Dữ liệu trở lại; có đủ chuỗi mẫu mới để người kiểm tra xem xét. Máy vẫn dừng.',
        '3. Bộ thử giả lập xác nhận đã kiểm tra nguyên nhân, chuẩn bị lại phôi, trục/xi lanh, chân không/tải và liên động.',
        '4. Gửi yêu cầu đặt lại, có mã phiên làm việc, mã yêu cầu và mã kiểm tra bộ thông số.',
        '5. Phía mô phỏng tạo cảnh mới, xác nhận đúng yêu cầu và tăng số lần khởi tạo. Chưa chạy băng.',
        '6. Có lệnh bắt đầu riêng, gắn đúng xác nhận đó; quyền chạy được lấy một lần.',
        '7. Chính cảnh mới đã chuẩn bị được dùng để chạy; phôi mới được đặt đúng hộp. Cảnh cũ không bị thay đổi.','',
        '## Cách đọc dữ liệu','',
        '`receipt.json` là biên bản trình tự; `message_cases.json` là các phép thử bản tin; `held_cycle` và `new_cycle` giữ hai bộ nhật ký độc lập.',
        'Các mã tiếng Anh trong dữ liệu: HOLD = dừng chờ; READY_NEW_CYCLE = chờ lệnh bắt đầu lượt mới; RUNNING = đã cấp quyền chạy mới; COMPLETE = lượt mới hoàn tất; BLOCKED = bị chặn, cần xem xét lại.',
        'Thời gian trong phép thử bản tin là thời gian giả lập, không phải phép đo độ trễ truyền thông thực. Bộ dự báo dùng ngân sách tính 1 giây cho kiểm tra chức năng, chưa chứng minh đáp ứng 20 mili giây.',
        'Chưa có kết nối PLC thật (bộ điều khiển máy), chưa có xác thực người dùng thật hoặc mã phiên gắn vào toàn bộ luồng cảm biến. Chưa có tự phục hồi phôi đang dang dở hay đồng bộ đầy đủ CAD V5.','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'PASS: {len(probes)}/{len(probes)} message cases; 2 MuJoCo runs; held old scene unchanged; new cycle DONE',flush=True)
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,default=DEFAULT); p.add_argument('--settings',type=Path,default=SETTINGS)
    a=p.parse_args(); check(a.output,load_config(a.config),json.loads(a.settings.read_text(encoding='utf-8-sig')))
