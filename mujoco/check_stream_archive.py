"""Exercise replay and portable evidence on actual loopback fault fixtures."""
import argparse
import json
from pathlib import Path
from check_stream import check as check_stream
from stream_archive import bundle, replay, verify


def check(output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    stream = check_stream(output/'stream')
    checks = {'loopback': stream['passed']}
    for name in stream['checks']:
        folder = output/'stream'/name
        checks[name+'_replay'] = replay(folder, output/(name+'_replay'))['passed']
        checks[name+'_bundle'] = bundle(folder, output/(name+'.zip'))['passed']
        checks[name+'_verify'] = verify(output/(name+'.zip'))['passed']
    report = {'kind': 'stream_archive_check_v1', 'passed': all(checks.values()),
              'checks': checks, 'physical_validation': False, 'physical_output': False}
    (output/'stream_archive_check.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (output/'report.md').write_text('# Hai mục: phát lại và hồ sơ di chuyển\n\n'+
        '\n'.join(f"- {k}: {'đạt' if v else 'cần xem lại'}" for k, v in checks.items())+
        '\n\nChỉ thử phần mềm, không xác nhận cảm biến hoặc điều khiển máy thật.\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True)
    raise SystemExit(int(not check(p.parse_args().output)['passed']))
