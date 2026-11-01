"""Package actual acceptance traces for replay, with provenance and no fabricated data."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'output/dt_predictive_acceptance_20261027_final'
LABELS = {
    'predictive_nominal': 'Bình thường · có dự báo',
    'baseline_nominal': 'Bình thường · điều khiển nền',
    'predictive_missing_ps2': 'PS2 kẹt thấp · có dự báo',
    'baseline_missing_ps2': 'PS2 kẹt thấp · điều khiển nền',
    'predictive_delay_20ms': 'Mạng trễ 20 ms',
    'predictive_loss_all': 'Mất toàn bộ gói tin',
    'predictive_strict': 'Thiếu phản hồi · chế độ nghiêm ngặt',
    'predictive_deadline': 'Ép quá ngân sách tính toán',
    'predictive_speed_low': 'Băng tải chậm · 0,10 m/s',
    'predictive_speed_high': 'Băng tải nhanh · 0,24 m/s',
}


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def read_replay(folder, name, label):
    folder = Path(folder)
    source_files = ['summary.json', 'effective_config.json', 'manifest.json', 'controller.jsonl',
                    'ground_truth.jsonl', 'signals.jsonl', 'source_signals.jsonl', 'prediction.jsonl']
    data = {'id': name, 'label': label, 'source': str(folder.relative_to(HERE.parent)).replace('\\', '/'),
            'sha256': {file: hashlib.sha256((folder/file).read_bytes()).hexdigest() for file in source_files}}
    for key, file in [('summary', 'summary.json'), ('config', 'effective_config.json'), ('manifest', 'manifest.json')]:
        data[key] = json.loads((folder/file).read_text(encoding='utf-8'))
    for key, file in [('frames', 'controller.jsonl'), ('truth', 'ground_truth.jsonl'), ('received', 'signals.jsonl'),
                      ('source_signals', 'source_signals.jsonl'), ('predictions', 'prediction.jsonl')]:
        data[key] = read_lines(folder/file)
    return data


def build():
    dest = HERE / 'data'
    dest.mkdir(exist_ok=True)
    index = []
    for name, label in LABELS.items():
        data = read_replay(SOURCE/name, name, label)
        (dest/f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
        index.append({'id': name, 'label': label, 'state': data['summary']['controller_state']})
    (dest/'index.json').write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
    print(f'Exported {len(index)} verified-source replays into {dest}')


if __name__ == '__main__':
    build()
