"""Replay local stream ticks, or hash and transport their evidence; no device writes."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zipfile
from config import load_config, number
from stream_input import StreamCore, reject_constant

HERE = Path(__file__).resolve().parent
FILES = ('effective_config.json', 'mapping.json', 'receiver.json', 'summary.json',
         'raw_datagrams.jsonl', 'commands_dry_run.jsonl')
LIMIT = 64 * 1024 * 1024


def read(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > LIMIT:
        raise ValueError('regular evidence file <=64 MiB required')
    return path.read_bytes()


def decode(data):
    return json.loads(data.decode('utf-8'), parse_constant=reject_constant)


def digest(data): return hashlib.sha256(data).hexdigest()


def payloads(folder):
    folder = Path(folder)
    return {name: read(folder/name) for name in FILES}


def verify(archive):
    """Check a small, fixed allowlist in memory. Never extract archive paths."""
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(FILES)+1 or set(names) != set(FILES)|{'manifest.json'}:
            raise ValueError('unexpected, duplicate or missing archive members')
        if any(i.file_size > LIMIT or i.flag_bits & 1 for i in z.infolist()):
            raise ValueError('oversized or encrypted member')
        if sum(i.file_size for i in z.infolist()) > 128*1024*1024:
            raise ValueError('archive uncompressed limit exceeded')
        manifest = decode(z.read('manifest.json'))
        if manifest.get('kind') != 'stream_evidence_bundle_v1' or set(manifest.get('files', {})) != set(FILES):
            raise ValueError('invalid archive manifest')
        for name in FILES:
            data = z.read(name)
            if manifest['files'][name] != {'bytes': len(data), 'sha256': digest(data)}:
                raise ValueError('evidence hash mismatch: '+name)
    return {'kind': 'stream_bundle_check_v1', 'passed': True, 'files': len(FILES),
            'physical_validation': False, 'authenticity_verified': False}


def bundle(folder, target):
    data = payloads(folder)
    if sum(map(len, data.values())) > 128*1024*1024: raise ValueError('evidence total limit exceeded')
    manifest = {'kind': 'stream_evidence_bundle_v1', 'files': {
        name: {'bytes': len(value), 'sha256': digest(value)} for name, value in data.items()},
        'scope': 'integrity only; hashes do not authenticate sender or validate physics'}
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED) as z:
        for name, value in data.items(): z.writestr(name, value)
        z.writestr('manifest.json', json.dumps(manifest, indent=2))
    return {**verify(target), 'sha256': digest(target.read_bytes())}


def replay(folder, output):
    """Use saved reception/tick times, including silence, rather than wall pacing."""
    data = payloads(folder)
    summary = decode(data['summary.json']); info = decode(data['receiver.json'])
    config = load_config(Path(folder)/'effective_config.json')
    if summary.get('failure') or summary.get('kind') != 'stream_input_v1':
        raise ValueError('completed stream session required')
    if config['prediction'].get('background', {}).get('enabled'):
        raise ValueError('asynchronous observer replay is not supported; original profile kept unchanged')
    sources = summary.get('source_sha256', {})
    if not sources: raise ValueError('source hashes required')
    for name, expected in sources.items():
        if Path(name).name != name or not (HERE/name).is_file() or digest(read(HERE/name)) != expected:
            raise ValueError('runtime source differs: '+name)
    raw = [decode(line) for line in data['raw_datagrams.jsonl'].splitlines()]
    ticks = [decode(line) for line in data['commands_dry_run.jsonl'].splitlines()]
    if not ticks or ticks[-1].get('final') is not True or any(t.get('final') for t in ticks[:-1]):
        raise ValueError('exactly one final command at end required')
    previous = -1
    for tick in ticks:
        now = tick['time_s']; number(now, 'saved tick time', 0)
        if now <= previous or tick.get('physical_output') is not False:
            raise ValueError('strictly increasing local dry-run ticks required')
        previous = now
    packets = {}; previous = -1
    for row in raw:
        now = row['time_s']; number(now, 'saved packet time', 0)
        if now <= previous: raise ValueError('packet times must increase')
        previous = now
        packets[now] = base64.b64decode(row['bytes_b64'], validate=True)
    if not set(packets) <= {t['time_s'] for t in ticks[:-1]}:
        raise ValueError('packet has no corresponding receiver tick')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    core = StreamCore(config, decode(data['mapping.json']), info['session_id'], info['generation'])
    mismatches = []
    try:
        with (output/'replayed_commands.jsonl').open('w', encoding='utf-8') as log:
            for index, expected in enumerate(ticks):
                now = expected['time_s']
                actual = core.finish(now) if expected.get('final') else core.tick(packets.get(now), now)
                log.write(json.dumps(actual, allow_nan=False)+'\n')
                # Computation duration is measured again, never compared as a logical result.
                stable = lambda row: {k: v for k, v in row.items() if k != 'core_step_ms'}
                if stable(actual) != stable(expected): mismatches.append(index)
    finally: core.close()
    report = {'kind': 'stream_replay_v1', 'passed': not mismatches, 'ticks': len(ticks),
              'datagrams': len(raw), 'mismatch_tick_indices': mismatches,
              'input_files_sha256': {k: digest(v) for k, v in data.items()},
              'source_sha256': sources, 'physical_output': False, 'physical_validation': False,
              'scope': 'same input and recorded ticks; excludes compute duration; not wall-time or physical reproducibility'}
    (output/'replay.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (output/'report.md').write_text('# Phát lại phiên dữ liệu\n\n'
        f"{len(ticks)} nhịp, {len(raw)} gói; {len(mismatches)} nhịp khác kết quả cũ.\n\n"
        'Giữ cả các nhịp không có gói, thời điểm nhận và lệnh dừng cuối. Không so thời gian tính toán; '
        'không gửi lệnh tới thiết bị. Cùng kết quả không chứng minh mô hình vật lý chính xác.\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for mode in ('replay', 'bundle'):
        p = sub.add_parser(mode); p.add_argument('--input', type=Path, required=True)
        p.add_argument('--output', type=Path, required=True)
    sub.add_parser('verify').add_argument('--input', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.input) if args.mode == 'verify' else (
        replay(args.input, args.output) if args.mode == 'replay' else bundle(args.input, args.output))
    print(json.dumps(result, indent=2))
    raise SystemExit(int(not result['passed']))
