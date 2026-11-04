"""Package a portable snapshot using explicit local file allowlists."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'ProductionTwin_MuJoCo_CAD_DT_20261104'

def package():
    files = {}
    def add(path, destination=None):
        path = ROOT/path
        if not path.is_file():
            raise FileNotFoundError(path)
        files[destination or path.relative_to(ROOT).as_posix()] = path
    for folder in ('mujoco', 'web', 'fusion/ProductionTwin_V0', 'fusion/ProductionTwin_V5'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                if path.name in ('commissioning.csv', 'preview.ppm', 'qa-responsive.html'):
                    continue
                add(path.relative_to(ROOT))
    for path in (ROOT/'docs').glob('*.md'):
        add(path.relative_to(ROOT))
    for path in sorted((ROOT/'output/cad').glob('production_twin_v5*')):
        if path.is_file() and path.suffix in ('.step', '.glb', '.png', '.json'):
            add(path.relative_to(ROOT))
    for path in ('cad_reference/production_twin_v4.step', 'cad_reference/production_twin_v4.f3d',
                 'cad_reference/production_twin_v0_parts.csv', 'scenes/production_twin_v5.py',
                 'scenes/check_production_twin_v5.py', 'scripts/export_cad_parts.py',
                 'scripts/export_viewer_glb.py'):
        add(path)
    for path in (ROOT/'scripts/portable_bundle').iterdir():
        if path.is_file():
            add(path.relative_to(ROOT), path.name)
    manifest = {'bundle':NAME, 'created_date':'2026-11-04',
                'reference_runtime':{'python':'3.12.3', 'mujoco':'3.16.0', 'numpy':'2.5.4', 'os':'WSL Ubuntu 24.04'},
                'geometry_status':'CAD V5 measured envelope; MuJoCo remains uncalibrated baseline',
                'files':{key:{'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                         for key,p in sorted(files.items())}}
    target = ROOT/'output'/f'{NAME}.zip'
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for key,path in sorted(files.items()):
            z.write(path, f'{NAME}/{key}')
        z.writestr(f'{NAME}/MANIFEST.json', json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for key,fact in manifest['files'].items():
            assert hashlib.sha256(z.read(f'{NAME}/{key}')).hexdigest() == fact['sha256']
    print(target, f'{target.stat().st_size/1048576:.2f} MiB; {len(files)} files + manifest')
    print('SHA256', hashlib.sha256(target.read_bytes()).hexdigest())
    return target

if __name__ == '__main__':
    package()
