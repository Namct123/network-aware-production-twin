"""Replay retains silence and rejects altered sources; bundles never extract paths."""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile
from config import load_config
from io_adapter import load_adapter
from stream_input import StreamCore
from stream_archive import HERE, FILES, bundle, replay, verify


class StreamArchiveTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.folder = self.root/'session'; self.folder.mkdir()
        config = load_config(HERE/'configs/reconfigurable_cell_20261030.json')
        mapping = load_adapter(HERE/'configs/recording_map_example.json').settings
        values = {'PS1_pusher': False, 'PS2_upstream': False, 'PS3_pickup': False,
                  'A1_back': True, 'A1_front': False, 'A2_up': True, 'A2_down': False}
        def packet(seq, t):
            return json.dumps({'session_id': 'archive', 'generation': 0, 'sequence': seq,
                'source_time': t*1000, 'values': values, 'quality': {k:'good' for k in values}}).encode()
        packets = [(0., packet(0, 0)), (.1, None), (.4, None), (.42, packet(1, .42)), (.44, b'not-json')]
        core = StreamCore(config, mapping, 'archive')
        try:
            ticks = [core.tick(p, t) for t, p in packets]; ticks.append(core.finish(.46))
            summary = dict(core.summary(), failure=None,
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')})
        finally: core.close()
        self.write('effective_config.json', config); self.write('mapping.json', mapping)
        self.write('receiver.json', {'session_id':'archive', 'generation':0}); self.write('summary.json', summary)
        (self.folder/'commands_dry_run.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in ticks))
        (self.folder/'raw_datagrams.jsonl').write_text(''.join(json.dumps({'time_s': t,
            'bytes_b64': base64.b64encode(p).decode(), 'peer':['127.0.0.1', 1]})+'\n' for t, p in packets if p is not None))

    def write(self, name, obj): (self.folder/name).write_text(json.dumps(obj))

    def test_silence_return_malformed_and_final_are_reproduced(self):
        report = replay(self.folder, self.root/'replay')
        self.assertTrue(report['passed']); self.assertEqual(report['ticks'], 6)
        rows = [json.loads(s) for s in (self.root/'replay/replayed_commands.jsonl').read_text().splitlines()]
        self.assertEqual(rows[2]['hold_reason'], 'telemetry_timeout')
        self.assertEqual(rows[3]['hold_reason'], 'telemetry_timeout')
        self.assertIsNotNone(rows[4]['input_error']); self.assertTrue(rows[-1]['final'])

    def test_changed_command_is_reported_not_silently_replaced(self):
        path = self.folder/'commands_dry_run.jsonl'; rows = [json.loads(s) for s in path.read_text().splitlines()]
        rows[0]['phase'] = 'DONE'
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        report = replay(self.folder, self.root/'replay')
        self.assertFalse(report['passed']); self.assertEqual(report['mismatch_tick_indices'], [0])

    def test_changed_source_and_orphan_packet_rejected(self):
        summary = json.loads((self.folder/'summary.json').read_text()); original = deepcopy(summary)
        summary['source_sha256']['runtime.py'] = '0'*64; self.write('summary.json', summary)
        with self.assertRaisesRegex(ValueError, 'source differs'): replay(self.folder, self.root/'a')
        self.write('summary.json', original)
        with (self.folder/'raw_datagrams.jsonl').open('a') as f: f.write(json.dumps({'time_s':.45, 'bytes_b64':'e30='})+'\n')
        with self.assertRaisesRegex(ValueError, 'no corresponding'): replay(self.folder, self.root/'b')

    def test_bundle_verifies_and_refuses_overwrite_and_modified_content(self):
        target = self.root/'session.zip'; self.assertTrue(bundle(self.folder, target)['passed'])
        self.assertTrue(verify(target)['passed'])
        with self.assertRaises(FileExistsError): bundle(self.folder, target)
        with zipfile.ZipFile(target) as z: data = {n:z.read(n) for n in z.namelist()}
        data['mapping.json'] = b'{}'
        tampered = self.root/'changed.zip'
        with zipfile.ZipFile(tampered, 'w') as z:
            for name, value in data.items(): z.writestr(name, value)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'): verify(tampered)

    def test_archive_traversal_and_duplicate_members_rejected(self):
        target = self.root/'unsafe.zip'
        with zipfile.ZipFile(target, 'w') as z:
            z.writestr('../outside.json', '{}')
        with self.assertRaises(ValueError): verify(target)
        self.assertFalse((self.root/'outside.json').exists())
        duplicate = self.root/'duplicate.zip'; bundle(self.folder, duplicate)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(duplicate, 'a') as z: z.writestr('mapping.json', '{}')
        with self.assertRaises(ValueError): verify(duplicate)

    def test_missing_final_and_async_profile_are_not_silently_approximated(self):
        path = self.folder/'commands_dry_run.jsonl'; original = path.read_text()
        path.write_text('\n'.join(original.splitlines()[:-1])+'\n')
        with self.assertRaisesRegex(ValueError, 'final command'): replay(self.folder, self.root/'a')
        path.write_text(original)
        config = json.loads((self.folder/'effective_config.json').read_text())
        config['prediction']['background'] = load_config(HERE/'configs/background_observer_20261103.json')['prediction']['background']
        self.write('effective_config.json', config)
        with self.assertRaisesRegex(ValueError, 'asynchronous'): replay(self.folder, self.root/'b')


if __name__ == '__main__': unittest.main()
