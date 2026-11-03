"""Diagnostic comparison must not turn missing/invalid forecasts into agreements."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from audit_background import audit,compare_receipt
from config import load_config
from estimator import Estimate
from reset_protocol import digest

HERE=Path(__file__).resolve().parent


class BackgroundAuditTest(unittest.TestCase):
    def setUp(self):
        self.config=load_config(HERE/'configs/background_observer_20261103.json')
        self.session={'session_id':'audit-test','generation':0}
        p=self.config['prediction'];self.expected=2*len(p['position_offsets'])*len(p['speed_offsets_m_s'])*len(p['reaction_delays_s'])
        job={**self.session,'request_id':0,'profile_sha256':digest(self.config),'clock_domain':'simulation',
            'source_sequence':1,'source_time_s':1.0,'decision_time_s':1.0,'submitted_wall_s':99.0,
            'estimate':Estimate(y_m=.0,velocity_m_s=.16,uncertainty_m=.001,reason='tracking').as_dict(),
            'expected_scenarios':self.expected}
        self.row={'time_s':1.06,'mode':'observe_only','control_applied':False,'receipt':{
            'accepted':True,'reason':'accepted_observation_only','request_id':0,'request':job,
            'worker_error':None,'prediction':{'status':'complete','action':'CONTINUE',
                'expected_scenarios':self.expected,'completed_scenarios':self.expected,
                'margins_m':{'HOLD':.01,'CONTINUE':.005}}}}

    def compare(self,row=None):return compare_receipt(self.config,self.session,row or self.row,set())

    def test_same_snapshot_comparison_leaves_inputs_unchanged(self):
        original=deepcopy(self.row);r=self.compare()
        self.assertTrue(r['comparable']);self.assertEqual(r['reason'],'agree')
        self.assertEqual(self.row,original)
        self.assertEqual(r['input_sha256'],digest(self.row['receipt']['request']))

    def test_disagreement_is_not_labeled_as_error_or_accuracy(self):
        self.row['receipt']['prediction']['action']='HOLD'
        self.row['receipt']['prediction']['margins_m']['CONTINUE']=-.001
        self.assertEqual(self.compare()['reason'],'reduced_continue_contact_hold')
        self.row['receipt']['request']['estimate']['y_m']=self.config['geometry']['long_belt_y_m'][1]
        self.row['receipt']['prediction']['action']='CONTINUE'
        self.assertEqual(self.compare()['reason'],'reduced_hold_contact_continue')

    def test_incomplete_hold_is_not_an_agreement(self):
        self.row['receipt'].update(accepted=False,reason='prediction_incomplete')
        self.row['receipt']['prediction'].update(status='deadline_exceeded',action='HOLD',completed_scenarios=0)
        r=self.compare();self.assertTrue(r['record_valid']);self.assertFalse(r['comparable'])
        self.assertEqual(r['reason'],'contact_incomplete')

    def test_discarded_old_reply_stays_separate(self):
        self.row['receipt'].update(accepted=False,reason='expired_simulation_age')
        r=self.compare();self.assertTrue(r['comparable']);self.assertFalse(r['admitted_observation'])

    def test_wrong_identity_counts_nonfinite_duplicates_rejected(self):
        for path,value in [('profile_sha256','wrong'),('generation',True),('clock_domain','wall'),('source_sequence',False),('expected_scenarios',1)]:
            row=deepcopy(self.row);row['receipt']['request'][path]=value
            self.assertFalse(self.compare(row)['record_valid'],path)
        row=deepcopy(self.row);row['receipt']['prediction']['margins_m']['HOLD']=float('nan')
        self.assertFalse(self.compare(row)['comparable'])
        seen=set();compare_receipt(self.config,self.session,self.row,seen)
        self.assertEqual(compare_receipt(self.config,self.session,self.row,seen)['reason'],'duplicate_request')
        self.assertIsNone(compare_receipt(self.config,self.session,{'receipt':None},seen))

    def test_file_audit_preserves_inputs_and_records_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source';source.mkdir();output=Path(temp)/'audit'
            (source/'effective_config.json').write_text(json.dumps(self.config))
            (source/'manifest.json').write_text(json.dumps({'config_sha256':digest(self.config),'session':self.session}))
            (source/'background.jsonl').write_text(json.dumps(self.row)+'\nnot json\n')
            hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()}
            r=audit(source,output)
            self.assertEqual(r['comparable_pairs'],1);self.assertEqual(r['invalid_records'],1)
            self.assertEqual(r['groups']['admitted']['pairs'],1)
            self.assertEqual(hashes,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()})
            with self.assertRaises(FileExistsError):audit(source,output)
            manifest=json.loads((source/'manifest.json').read_text());manifest['config_sha256']='changed'
            (source/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'manifest/config'):audit(source,Path(temp)/'bad')


if __name__=='__main__':unittest.main()
