"""No restart permission from merely fresh data; post-HOLD evidence is separate."""
from copy import deepcopy
from pathlib import Path
import unittest
from config import load_config,validate_config
from network import Network
from recovery import RecoveryAssessment,classify
from sequence import Sequence
from signals import SignalFrame

PROFILE=Path(__file__).parent/'configs/hold_review_cell_20261031.json'

def frame(seq,t,**changes):
    values={'ps1':False,'ps2':False,'transfer_present':False,'a1_retracted':True,'a1_extended':False,
            'a2_retracted':True,'a2_extended':False,**changes}
    return SignalFrame(seq,t,t,values,{k:'good' for k in values})

def assessment(c):
    return RecoveryAssessment(c['recovery'],c['timing'],'mechanics' in c)

class RecoveryTest(unittest.TestCase):
    def controller(self,reason='telemetry_timeout'):
        c=load_config(PROFILE); ctl=Sequence(config=c); ctl._enter('TRACK',0)
        ctl.hold(reason,1)
        return c,ctl,assessment(c)

    def test_context_captures_first_cause_and_prior_command(self):
        _,ctl,_=self.controller(); context=deepcopy(ctl.hold_context)
        self.assertEqual(context['from_phase'],'TRACK')
        self.assertEqual(context['command_before_hold']['long'],.16)
        self.assertEqual(ctl.command['long'],0)
        ctl.hold('other_reason',2)
        self.assertEqual(ctl.hold_context,context)
        self.assertEqual(ctl.reason,'telemetry_timeout')

    def test_fresh_streak_yields_operator_review_but_never_mutates_controller(self):
        _,ctl,review=self.controller(); before=deepcopy(ctl.__dict__)
        for i in range(1,8): r=review.tick(ctl,frame(i,1+i*.02),{'findings':[]},1+i*.02)
        self.assertEqual(r['stage'],'OPERATOR_REVIEW')
        self.assertFalse(r['automatic_resume_allowed']); self.assertFalse(r['restart_command_issued'])
        self.assertIn('actual_product_pose',r['unresolved_state'])
        # Compare only serializable state: the estimator object has identity equality.
        self.assertEqual(ctl.command,before['command'])
        self.assertEqual(ctl.transitions,before['transitions']); self.assertEqual(ctl.phase,'HOLD')
        self.assertEqual(ctl.estimator.time,before['estimator'].time)

    def test_pre_hold_frames_and_missing_ticks_cannot_complete_streak(self):
        _,ctl,review=self.controller()
        r=review.tick(ctl,frame(0,1),{'findings':[]},1)
        self.assertEqual(r['fresh_streak'],0)
        for i in range(1,4): review.tick(ctl,frame(i,1+i*.02),{'findings':[]},1+i*.02)
        r=review.tick(ctl,None,{'findings':[]},1.08)
        self.assertEqual(r['fresh_streak'],0)
        r=review.tick(ctl,frame(4,1.10),{'findings':[]},1.10)
        self.assertNotEqual(r['stage'],'OPERATOR_REVIEW')

    def test_sensor_and_compute_holds_need_manual_diagnosis_even_after_good_frames(self):
        self.assertEqual(classify('predictive_stop_margin'),'model_or_computation')
        self.assertEqual(classify('target_outside_workspace'),'geometry_or_workspace')
        for reason in ['reconfiguration:expected_edge_missing','prediction_deadline_exceeded',
                       'unconfirmed_xy_a2_midstroke_and_vacuum','nonmonotonic_sample','unknown_reason']:
            _,ctl,review=self.controller(reason)
            for i in range(1,8): r=review.tick(ctl,frame(i,1+i*.02),{'findings':[]},1+i*.02)
            self.assertEqual(r['stage'],'MANUAL_INTERVENTION',reason)
            self.assertIn('original_cause_requires_manual_diagnosis',r['blockers'])

    def test_duplicate_observation_never_counts_as_new_fresh_evidence(self):
        _,ctl,review=self.controller()
        first=frame(1,1.02)
        review.tick(ctl,first,{'findings':[]},1.02)
        r=review.tick(ctl,first,{'findings':[]},1.04)
        self.assertEqual(r['fresh_streak'],0)
        self.assertNotEqual(r['stage'],'OPERATOR_REVIEW')

    def test_vacuum_and_cylinder_state_remain_manual_blockers(self):
        _,ctl,review=self.controller(); ctl.command['vacuum']=True
        for i in range(1,8): r=review.tick(ctl,frame(i,1+i*.02,a2_retracted=False),{'findings':[]},1+i*.02)
        self.assertEqual(r['stage'],'MANUAL_INTERVENTION')
        self.assertIn('possible_held_load_requires_manual_handling',r['blockers'])
        self.assertTrue(ctl.command['vacuum'])

    def test_timed_out_review_and_invalid_config(self):
        c,ctl,_=self.controller(); c['recovery']['max_hold_age_s']=.2; review=assessment(c)
        for i in range(1,15): r=review.tick(ctl,frame(i,1+i*.02),{'findings':[]},1+i*.02)
        self.assertEqual(r['stage'],'MANUAL_INTERVENTION')
        self.assertIn('hold_too_old_for_review_path',r['blockers'])
        for windows in ([[2,1]],[[1,2],[1.5,3]],[[0,50]],[[False,1]]):
            bad=load_config(PROFILE); bad['network']['outage_windows_s']=windows
            with self.assertRaises(ValueError): validate_config(bad)
        for key,value in [('fresh_samples',True),('fresh_samples',1),('settle_wait_s',3),('max_hold_age_s',0)]:
            bad=load_config(PROFILE); bad['recovery'][key]=value
            with self.assertRaises(ValueError): validate_config(bad)

    def test_outage_is_half_open_and_transport_recovers(self):
        c=load_config(PROFILE)['network']; c['outage_windows_s']=[[.02,.06]]
        n=Network(c); observed=[]
        for i in range(5):
            f=frame(i,i*.02); n.send(f,i*.02)
            r=n.receive(i*.02)
            if r: observed.append(r.sequence)
        self.assertEqual(observed,[0,3,4])
        self.assertEqual(n.stats['dropped'],2)

if __name__=='__main__': unittest.main()
