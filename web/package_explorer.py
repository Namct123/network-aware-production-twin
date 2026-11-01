"""Create a portable, dependency-free teaching bundle from this checkout."""
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def package():
    target=ROOT/'output/DT_Explorer_2026-10-28.zip'
    files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='qa-responsive.html']
    files += [ROOT/'mujoco'/name for name in ['config.py','estimator.py','predictor.py','supervisor.py',
               'signals.py','sensor_model.py','sequence.py','network.py','evaluation.py','experiment.py',
               'model_profile.py','run_cell.py','production_cell.xml',
               'configs/simulation.json','configs/predictive_demo.json','configs/slow_a2_demo.json']]
    files.append(ROOT/'docs/live_experiments.md')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path,'DT_Explorer/'+path.relative_to(ROOT).as_posix())
        archive.writestr('DT_Explorer/MO_GIAO_DIEN.cmd','@echo off\r\ncall "%~dp0web\\START_EXPLORER.cmd"\r\n')
        archive.writestr('DT_Explorer/README.txt',
            'DT Explorer - Windows\r\n1. Install Python 3.10+ if missing.\r\n'
            '2. Double-click MO_GIAO_DIEN.cmd and keep the server window open.\r\n'
            '3. Open http://127.0.0.1:8765 in your browser.\r\n'
            'Vietnamese guide: web/README.md\r\nReplay and 1D prediction need no MuJoCo installation.\r\n'
            'New physical simulation jobs: web/START_SIMULATION_EXPLORER.cmd, require configured MuJoCo in WSL.\r\n')
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
    print(f'{target} ({target.stat().st_size/1024/1024:.2f} MiB)')
    return target


if __name__=='__main__':
    package()
