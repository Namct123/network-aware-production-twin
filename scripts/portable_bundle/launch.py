"""Portable entry point; delegates to the unchanged DT core."""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', default='demo',
                        choices=['demo', 'fault', 'strict', 'acceptance', 'predictive-check', 'measured-check', 'observer-check', 'reconfiguration-check', 'robustness-check', 'adaptive-check', 'recovery-check', 'reset-check', 'integration-check'])
    parser.add_argument('--view', action='store_true')
    parser.add_argument('--bin', type=int, choices=range(1, 7), default=1)
    parser.add_argument('--config', type=Path, help='Optional validated machine profile JSON')
    parser.add_argument('--plan',type=Path,help='Experiment plan JSON for robustness-check or adaptive-check')
    parser.add_argument('--settings',type=Path,help='Reset timing settings JSON for reset-check only')
    args = parser.parse_args()
    if args.settings and args.mode!='reset-check': parser.error('--settings requires reset-check')
    if args.plan and args.mode not in ('robustness-check','adaptive-check'): parser.error('--plan requires robustness-check or adaptive-check')
    if args.view and os.environ.get('DT_CONTAINER_HEADLESS') == '1':
        parser.error('This Docker image is headless; use the local viewer outside Docker')
    if args.view and args.mode in ('acceptance', 'predictive-check', 'measured-check', 'observer-check', 'reconfiguration-check', 'robustness-check', 'adaptive-check', 'recovery-check', 'reset-check', 'integration-check'):
        parser.error('--view is only available for demo, fault, or strict')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT/'output'/(args.mode+'_'+stamp+'_'+uuid.uuid4().hex[:8])
    out.parent.mkdir(exist_ok=True)
    script = {'acceptance':'check_twin.py', 'predictive-check':'check_prediction.py', 'measured-check':'check_measured.py', 'observer-check':'check_observer.py', 'reconfiguration-check':'check_reconfiguration.py', 'robustness-check':'check_robustness.py', 'adaptive-check':'check_robustness.py', 'recovery-check':'check_recovery.py', 'reset-check':'check_reset.py', 'integration-check':'check_integration.py'}.get(args.mode, 'run_twin.py')
    command = [sys.executable, str(ROOT/'mujoco'/script), '--output', str(out)]
    if args.mode=='adaptive-check':
        if not args.config: command += ['--config', str(ROOT/'mujoco/configs/adaptive_cell_20261031.json')]
        if not args.plan: command += ['--plan', str(ROOT/'mujoco/experiments/adaptive_speed_20261031.json')]
    if args.plan:
        command += ['--plan', str(args.plan.resolve())]
    if args.settings:
        command += ['--settings', str(args.settings.resolve())]
    if args.config:
        command += ['--config', str(args.config.resolve())]
    if args.mode in ('demo', 'fault', 'strict'):
        if not args.config:
            command += ['--config', str(ROOT/os.environ.get('DT_DEFAULT_PROFILE','mujoco/configs/predictive_demo.json'))]
        command += ['--bin', str(args.bin)]
        if args.mode != 'strict':
            command += ['--assume-open-loop']
        if args.mode == 'fault':
            command += ['--fault', 'ps2_stuck_low']
        if args.view:
            command += ['--view']
    print('Results:', out, flush=True)
    return subprocess.run(command, cwd=ROOT, check=False).returncode

if __name__ == '__main__':
    raise SystemExit(main())
