"""Local teaching UI: replay measured simulation logs and call the existing predictor."""
import argparse
import json
import math
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from urllib.parse import urlparse
from experiments import Experiments, BusyError
from project_status import ProjectStatus

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'mujoco'))
from config import load_config
from estimator import Estimate
from predictor import Predictor


def predict(payload):
    bounds = {'y': (-.3, .23), 'speed': (0, .4), 'uncertainty': (0, .08), 'age': (0, .3)}
    if not isinstance(payload, dict) or set(payload) != set(bounds):
        raise ValueError('Cần đúng bốn tham số: y, speed, uncertainty, age.')
    for name, (low, high) in bounds.items():
        v = payload[name]
        if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f'{name}: ngoài miền [{low}, {high}]')
    config = load_config(ROOT / 'mujoco/configs/predictive_demo.json')
    estimate = Estimate(payload['y'], payload['speed'], payload['uncertainty'], 2, 'tracking')
    result = Predictor(config).rollout(estimate, 0, payload['age'])
    p, period = config['prediction'], config['timing']['physics_step_s'] * config['timing']['sample_steps']
    # Visualization uses the same equations, separate from the timed decision above.
    curves = []
    for policy, advance in [('HOLD', 0), ('CONTINUE', period)]:
        for offset in p['position_offsets']:
            for dv in p['speed_offsets_m_s']:
                for reaction in p['reaction_delays_s']:
                    speed = max(0, payload['speed'] + dv)
                    initial = payload['y'] + offset*(payload['uncertainty'] + config['estimator']['drift_m_s']*payload['age']) + speed*payload['age']
                    cutoff = advance + reaction
                    points = []
                    for i in range(math.ceil(p['horizon_s']/p['step_s']) + 1):
                        t = min(i*p['step_s'], p['horizon_s'])
                        coast = config['estimator']['stop_coast_m']*min(1, max(0, (t-cutoff)/p['step_s']))
                        points.append([t, initial + speed*min(t, cutoff) + coast])
                    curves.append({'policy': policy, 'points': points})
    return {'result': result, 'curves': curves, 'limit': Predictor(config).limit,
            'period': period, 'scope': 'sandbox_input_not_physical_measurement'}


class Handler(SimpleHTTPRequestHandler):
    experiments = Experiments()
    project_status = ProjectStatus()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def json_response(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        try:
            if path=='/api/project-state':
                return self.json_response(self.project_status.read())
            if path=='/api/capabilities':
                return self.json_response(self.experiments.capabilities())
            if path=='/api/experiments':
                return self.json_response(self.experiments.recent())
            if path.startswith('/api/experiments/'):
                parts=path.strip('/').split('/')
                if len(parts)==3:
                    return self.json_response(self.experiments.status(parts[2]))
                if len(parts)==5 and parts[3]=='replay' and parts[4] in {'baseline','predictive'}:
                    status=self.experiments.status(parts[2])
                    if status['state']!='completed':
                        return self.json_response({'error':'Thí nghiệm chưa hoàn tất.'},409)
                    replay=self.experiments.folder(parts[2])/f'{parts[4]}_replay.json'
                    return self.json_response(json.loads(replay.read_text(encoding='utf-8')))
                return self.json_response({'error':'Not found'},404)
        except FileNotFoundError:
            return self.json_response({'error':'Không tìm thấy kết quả.'},404)
        except (ValueError,OSError) as error:
            return self.json_response({'error':str(error)},400)
        return super().do_GET()

    def do_POST(self):
        path=urlparse(self.path).path
        if path not in {'/api/predict','/api/experiments'}:
            return self.json_response({'error': 'Not found'}, 404)
        if self.headers.get('Origin') not in (None, f'http://{self.headers.get("Host")}'):
            return self.json_response({'error': 'Origin rejected'}, 403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 2048:
                raise ValueError('Invalid body size')
            payload=json.loads(self.rfile.read(length))
            if path=='/api/experiments':
                return self.json_response(self.experiments.submit(payload),202)
            self.json_response(predict(payload))
        except BusyError as error:
            self.json_response({'error':str(error)},409)
        except (ValueError, TypeError, OverflowError) as error:
            self.json_response({'error': str(error)}, 400)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--enable-experiments',action='store_true',help='Enable bounded local WSL MuJoCo jobs')
    parser.add_argument('--wsl-distro',default='Ubuntu-24.04')
    parser.add_argument('--simulation-python',default='/home/admin/dt-cpps-venv/bin/python')
    args = parser.parse_args()
    Handler.experiments=Experiments(args.enable_experiments,args.wsl_distro,args.simulation_python)
    print(f'DT Explorer: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
