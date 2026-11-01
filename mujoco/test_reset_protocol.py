"""Simulation handshake checks: identity, timing, separate start and single consumption."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from reset_protocol import ResetCoordinator,CONFIRMATIONS,digest

SETTINGS=json.loads((Path(__file__).parent/'experiments/reset_protocol.json').read_text())

def review():
    return {'time_s':1.0,'stage':'OPERATOR_REVIEW','blockers':[],
        'hold_context':{'time_s':.5,'reason':'telemetry_timeout','from_phase':'TRACK'},
        'hold_category':'telemetry_or_signal_quality','automatic_resume_allowed':False,'restart_command_issued':False}

def request(c,request_id='reset_1',now=1.01):
    return {'environment':'simulation','session_id':c.session_id,'request_id':request_id,
            'generation':c.generation,'issued_at_s':now,'hold_id':c.hold_id,'profile_sha256':digest({'test':1}),
            'operator_confirmations':dict.fromkeys(CONFIRMATIONS,True)}

def acknowledgement(c,p,now=1.02):
    return {'environment':'simulation','session_id':c.session_id,'request_id':p['request_id'],
        'previous_generation':c.generation,'new_generation':c.generation+1,'profile_sha256':p['profile_sha256'],
        'scene_id':'scene_1','reset_complete':True,'ack_at_s':now}

def start(c,ack,now=1.03):
    return {'environment':'simulation','session_id':c.session_id,'request_id':'start_1','generation':c.generation,
            'issued_at_s':now,'profile_sha256':c.profile_sha,'reset_ticket':ack['reset_ticket']}

class ResetTest(unittest.TestCase):
    def coordinator(self): return ResetCoordinator(SETTINGS,review(),session_id='test_session')

    def ready(self,c):
        p=request(c); self.assertTrue(c.handle('reset',p,1.01)['accepted'])
        ack=c.handle('ack',acknowledgement(c,p),1.02)
        self.assertTrue(ack['accepted']); return p,ack

    def test_reset_ack_never_starts_until_distinct_start_then_claim_once(self):
        c=self.coordinator(); _,ack=self.ready(c)
        self.assertEqual(c.stage,'READY_NEW_CYCLE'); self.assertIsNone(c.take_start())
        s=start(c,ack); self.assertTrue(c.handle('start',s,1.03)['accepted'])
        self.assertEqual(c.take_start()['generation'],1)
        self.assertIsNone(c.take_start()); self.assertFalse(c.handle('start',s,1.04)['accepted'])
        self.assertFalse(any(e['old_cycle_resume_allowed'] for e in c.events))
        self.assertTrue(c.finish('scene_1',True,2)['accepted']); self.assertEqual(c.stage,'COMPLETE')

    def test_missing_human_checks_and_blocked_review(self):
        for altered in ('confirmation','stage','stale','context'):
            r=review()
            if altered=='stage': r['stage']='MANUAL_INTERVENTION'
            if altered=='stale': r['time_s']=0
            c=ResetCoordinator(SETTINGS,r); p=request(c)
            if altered=='confirmation': p['operator_confirmations']['local_interlocks_checked']=False
            if altered=='context': p['hold_id']='wrong'
            self.assertFalse(c.handle('reset',p,1.01)['accepted']); self.assertEqual(c.stage,'HOLD')

    def test_mismatched_ack_does_not_destroy_matching_pending_request(self):
        for key,value in [('request_id','old_reset'),('session_id','other'),('new_generation',9),
                          ('profile_sha256','f'*64),('environment','physical')]:
            c=self.coordinator(); p=request(c); c.handle('reset',p,1.01)
            a=acknowledgement(c,p); a[key]=value
            self.assertFalse(c.handle('ack',a,1.02)['accepted']); self.assertEqual(c.stage,'RESET_PENDING')
            self.assertTrue(c.handle('ack',acknowledgement(c,p,1.03),1.03)['accepted'])

    def test_timeouts_block_unknown_outcome_and_late_ack(self):
        c=self.coordinator(); p=request(c); c.handle('reset',p,1.01)
        self.assertEqual(c.poll(2)['stage'],'BLOCKED')
        self.assertFalse(c.handle('ack',acknowledgement(c,p,2),2)['accepted'])
        self.assertEqual(c.stage,'BLOCKED'); self.assertIsNone(c.take_start())
        c=self.coordinator(); _,a=self.ready(c)
        self.assertFalse(c.handle('start',start(c,a,2),2)['accepted']); self.assertEqual(c.stage,'BLOCKED')

    def test_old_generation_wrong_ticket_and_early_start(self):
        c=self.coordinator()
        p={'environment':'simulation','session_id':c.session_id,'request_id':'s','generation':0,
           'issued_at_s':1.01,'profile_sha256':'a'*64,'reset_ticket':'none'}
        self.assertFalse(c.handle('start',p,1.01)['accepted'])
        c=self.coordinator(); _,a=self.ready(c)
        for key,value in [('generation',0),('reset_ticket','wrong')]:
            p=start(c,a); p[key]=value
            self.assertFalse(c.handle('start',p,1.03)['accepted']); self.assertEqual(c.stage,'READY_NEW_CYCLE')
        self.assertFalse(c.handle('start',start(c,a,1.015),1.03)['accepted'])
        c=self.coordinator(); p=request(c,now=1.0); c.handle('reset',p,1.01)
        self.assertFalse(c.handle('ack',acknowledgement(c,p,1.005),1.02)['accepted'])

    def test_schema_clock_and_settings_reject_invalid_inputs(self):
        with self.assertRaises(ValueError): ResetCoordinator({**SETTINGS,'start_window_s':0},review())
        c=self.coordinator(); p=request(c); p['extra']=True
        self.assertFalse(c.handle('reset',p,1.01)['accepted'])
        with self.assertRaises(ValueError): c.handle('reset',request(c),float('nan'))
        self.assertFalse(c.handle('reset',request(c,now=1),.9)['accepted'])

if __name__=='__main__': unittest.main()
