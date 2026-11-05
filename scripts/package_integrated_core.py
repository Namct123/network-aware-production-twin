"""Package allowlisted integrated source and easy Vietnamese instructions, no experiment execution."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent.parent

def package(target):
    target=Path(target)
    if target.exists(): raise FileExistsError('Không ghi đè gói đã có; chọn tên mới.')
    files=[]
    for folder,extensions in [('mujoco',{'.py','.json','.xml','.urdf','.csv','.md'}),('web',{'.py','.js','.html','.css','.json','.md','.cmd'})]:
        files += [p for p in (ROOT/folder).rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix in extensions]
    docs=['gioi_han_xung_va_mang_20261105.md','du_doan_tu_xung_PS2_20261105.md','hieu_chuan_mien_du_doan_20261105.md','huong_nghien_cuu_hien_tai.md','sai_lech_du_doan_quan_sat.md','don_du_an_20261105.md','truc_quan_anatomy.md','nghien_cuu_cam_bien_va_truyen_dong_20261104.md','phan_tich_phan_ung_mang.md','ket_qua_phan_ung_mang_20261104.md','chuyen_sang_o_D_va_bo_unity.md','phat_lai_va_dong_goi_phien.md','phan_mem_truoc_khi_do_may.md','nghien_cuu_gioi_han_mo_hinh.md','bao_cao_bien_mo_hinh_20261103.md','doi_chieu_du_bao.md','du_bao_nen_quan_sat.md','bao_cao_du_bao_nen_20261103.md','bao_cao_toi_uu_20261103.md','toi_uu_du_bao_mujoco.md','bao_cao_danh_gia_20261102.md','danh_gia_co_doi_chung.md','bao_cao_tich_hop_so1.md','nhat_ky_cong_viec.md','ban_tich_hop_phan_mem.md','bao_cao_tien_do_de_hieu.md','modular_twin.md','parameterized_core.md','docker.md']
    files += [ROOT/'docs'/n for n in docs]
    files += [ROOT/p for p in ['scripts/export_anatomy.py','scripts/build_anatomy.mjs','scripts/anatomy/iso-kit.mjs','scripts/anatomy/LICENSE','scripts/anatomy/check_actions.json','scripts/docker_dt.ps1','scripts/portable_bundle/launch.py','docker/Dockerfile','docker/build_image.py',
        'docker/snapshot.py','docker/requirements.lock','docker/RELEASES.md','docker/evidence/candidate-20261031-integrated-core-v1.json','docker/evidence/candidate-20261102-qualification.json','docker/evidence/candidate-20261103-native-physics.json',
        'docker/evidence/candidate-20261103-background-observer.json',
        'docker/evidence/candidate-20261103-model-audit.json',
        'docker/evidence/candidate-20261103-boundary-study.json',
        'docker/evidence/candidate-20261103-software-v2.json',
        'docker/evidence/accepted-20261103-software-v2.json',
        'docker/evidence/candidate-20261104-stream-evidence.json',
        'docker/evidence/candidate-20261104-mujoco-only.json',
        'docker/evidence/candidate-20261104-time-boundary.json',
        'docker/evidence/candidate-20261104-sensor-drive.json',
        'docker/evidence/candidate-20261104-sensor-drive-v2.json',
        'docker/evidence/candidate-20261105-anatomy.json',
        'docker/evidence/candidate-20261105-residual-focus.json',
        'docker/evidence/candidate-20261105-interval-calibration.json',
        'docker/evidence/candidate-20261105-pulse.json',
        'docker/evidence/candidate-20261105-pulse-network.json',
        'compose.yaml','.dockerignore','AGENTS.md','scripts/package_integrated_core.py','scripts/export_cad_parts.py','scripts/analyze_sensor_drive.py','fusion/ProductionTwin_V0/ProductionTwin_V0.py','cad_reference/production_twin_v0_parts.csv']]
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
    target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name in manifest: z.write(ROOT/name,'DT_Core/'+name)
        z.writestr('DT_Core/GOI_MA_NGUON.json',json.dumps(manifest,indent=2))
        z.writestr('DT_Core/DOC_TRUOC.txt','Lõi Digital Twin MuJoCo.\nĐọc docs/chuyen_sang_o_D_va_bo_unity.md và docs/nhat_ky_cong_viec.md.\n'
            'Trang theo dõi: mở web/tong_quan.html hoặc chạy web/server.py rồi vào /tong_quan.html.\n'
            'Mô phỏng cần MuJoCo hoặc Docker. Không có kết nối điều khiển PLC thật.\n'
            'Không coi mã đã đóng gói là đã đo/hiệu chuẩn hoặc được người dùng nghiệm thu.\n')
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None: raise ValueError('ZIP integrity check failed')
    return {'file':str(target),'files':len(manifest),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True)
    print(json.dumps(package(p.parse_args().output),ensure_ascii=False))
