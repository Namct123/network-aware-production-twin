"""Record the exact runtime files baked into this image (no host paths)."""
import hashlib
import json
from pathlib import Path
import platform
import mujoco
import numpy

root = Path(__file__).resolve().parents[1]
paths = [p for p in (root/'mujoco').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [p for p in (root/'web').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [root/'launch.py', root/'requirements.txt', root/'docker/snapshot.py',
          root/'unity/Assets/ProductionTwin/parts.csv']
snapshot = {'python':platform.python_version(), 'mujoco':mujoco.__version__,
            'numpy':numpy.__version__, 'review_status_at_build':'candidate-awaiting-human-validation',
            'geometry':'parameterized user-reported envelope available; legacy baseline preserved; neither physically calibrated',
            'files':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(paths)}}
(root/'source_manifest.json').write_text(json.dumps(snapshot,indent=2)+'\n',encoding='utf-8')
