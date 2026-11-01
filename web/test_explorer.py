"""Small end-to-end checks for the teaching UI boundary and replay integrity."""
import json
import math
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import Handler, ThreadingHTTPServer, predict


class ExplorerTests(unittest.TestCase):
    def test_actual_predictor_and_plot_agree(self):
        for payload, expected in [
            ({'y': .12, 'speed': .16, 'uncertainty': .006, 'age': .02}, 'CONTINUE'),
            ({'y': .2, 'speed': .16, 'uncertainty': .006, 'age': 0}, 'HOLD'),
            ({'y': .18, 'speed': .16, 'uncertainty': .006, 'age': .18}, 'HOLD')]:
            data = predict(payload)
            r = data['result']
            self.assertEqual(len(data['curves']), 54)
            # A real machine can preempt a timing budget; that is a valid HOLD.
            if r['status'] == 'complete':
                self.assertEqual(r['action'], expected)
                for policy in ['HOLD', 'CONTINUE']:
                    worst = min(data['limit']-y for curve in data['curves'] if curve['policy']==policy for _,y in curve['points'])
                    self.assertAlmostEqual(worst, r['margins_m'][policy], places=12)
            self.assertTrue(all(len(c['points'])==26 for c in data['curves']))

    def test_input_boundary(self):
        good = {'y': .12, 'speed': .16, 'uncertainty': .006, 'age': .02}
        for key, value in [('y', math.nan), ('speed', True), ('age', -.1), ('uncertainty', .2)]:
            with self.assertRaises(ValueError):
                predict({**good, key:value})
        for payload in [None, [], {**good,'extra':1}, {'y':0}]:
            with self.assertRaises(ValueError):
                predict(payload)

    def test_replays_have_aligned_sequences_and_provenance(self):
        root = Path(__file__).parent/'data'
        rows = json.loads((root/'index.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rows), 10)
        for row in rows:
            data = json.loads((root/f'{row["id"]}.json').read_text(encoding='utf-8'))
            self.assertEqual(len(data['frames']),len(data['truth']))
            self.assertEqual(len(data['sha256']),8)
            for f,t in zip(data['frames'],data['truth']):
                self.assertEqual(f['sequence'],t['sequence'])
                self.assertAlmostEqual(f['time_s'],t['time_s'])
            self.assertEqual(data['frames'][-1]['phase'],data['summary']['controller_state'])
            self.assertTrue(all(t['to'] in {f['phase'] for f in data['frames']} for t in data['summary']['transitions']))

    def test_http(self):
        server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base) as response:
                self.assertEqual(response.status,200)
                self.assertIn('DT EXPLORER',response.read().decode())
            with urlopen(base+'/api/capabilities') as response:
                self.assertFalse(json.load(response)['enabled'])
            from test_experiments import REQUEST
            with self.assertRaises(HTTPError) as caught:
                urlopen(Request(base+'/api/experiments',json.dumps(REQUEST).encode(),{'Content-Type':'application/json'}))
            self.assertEqual(caught.exception.code,409)
            body=json.dumps({'y':.12,'speed':.16,'uncertainty':.006,'age':.02}).encode()
            with urlopen(Request(base+'/api/predict',body,{'Content-Type':'application/json'})) as response:
                self.assertIn(json.load(response)['result']['action'],['CONTINUE','HOLD'])
            for body, origin, status in [(b'{}',None,400),(b'{}','https://example.com',403)]:
                headers={'Content-Type':'application/json'}
                if origin: headers['Origin']=origin
                with self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base+'/api/predict',body,headers))
                self.assertEqual(caught.exception.code,status)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__=='__main__':
    unittest.main()
