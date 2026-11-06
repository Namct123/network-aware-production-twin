"""Send only allowed source files as a tar context, avoiding WSL/NTFS xattr issues."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def context_files(scope='full'):
    if scope=='monitoring':
        names=json.loads((ROOT/'research_scope.json').read_text(encoding='utf-8'))['runtime_files']
        paths=[ROOT/n for n in names]
        if len(set(names))!=len(names) or any(not p.resolve().is_relative_to(ROOT) or not p.is_file() or p.is_symlink() for p in paths):raise ValueError('invalid focused source allowlist')
        return sorted(paths)
    if scope!='full':raise ValueError('unknown build scope')
    paths = [p for p in (ROOT/'mujoco').rglob('*') if p.is_file()
             and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.xml','.urdf','.csv','.md'}
             and p.name != 'commissioning.csv']
    paths += [ROOT/p for p in ('docker/Dockerfile', 'docker/snapshot.py', 'docker/requirements.lock',
              'scripts/portable_bundle/launch.py',
              'cad_reference/production_twin_v0_parts.csv')]
    paths += [p for p in (ROOT/'web').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.js','.html','.css','.json','.md','.cmd'}]
    return sorted(paths)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', default=os.environ.get('DT_IMAGE_TAG','candidate-20261104-sensor-drive-v2'))
    parser.add_argument('--scope',choices=['full','monitoring'],default='full')
    args = parser.parse_args()
    if not re.fullmatch(r'candidate-[a-zA-Z0-9_.-]+',args.tag):
        parser.error('Build a candidate tag; accepted tags require explicit user validation.')
    paths = context_files(args.scope)
    with tempfile.TemporaryFile() as stream:
        with tarfile.open(fileobj=stream,mode='w') as archive:
            for path in paths:
                if path.is_symlink() or not path.is_file():
                    raise ValueError(f'Expected a regular source file: {path}')
                info = archive.gettarinfo(str(path),arcname=path.relative_to(ROOT).as_posix())
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                with path.open('rb') as source:
                    archive.addfile(info,source)
        print(f'Build context: {len(paths)} allowed files; {stream.tell()} bytes',flush=True)
        stream.seek(0)
        return subprocess.run(['docker','build','-f','docker/monitoring.Dockerfile' if args.scope=='monitoring' else 'docker/Dockerfile',
                   '-t',f'production-twin-dt:{args.tag}',
                   '--build-arg',f'DT_VERSION={args.tag}','-'],stdin=stream,cwd=ROOT).returncode

if __name__ == '__main__':
    raise SystemExit(main())
