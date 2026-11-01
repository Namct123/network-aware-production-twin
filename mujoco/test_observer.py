"""Observer boundary checks independent of MuJoCo and injected ground truth."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import unittest
from command_history import CommandHistory
from config import load_config,validate_config
from estimator import BeltEstimator,Estimate
from health import SignalHealth
from sequence import Sequence
from supervisor import Supervisor
from signals import SignalFrame

PROFILE=Path(__file__).parent/'configs/observable_cell_20261030.json'

def frame(seq,t,**values):
    v={'ps1':False,'ps2':False,'transfer_present':False,'a1_retracted':True,'a1_extended':False,
       'a2_retracted':True,'a2_extended':False,**values}
    return SignalFrame(seq,t,t,v,{k:'good' for k in v})

class ObserverTest(unittest.TestCase):
    def test_integral_uses_changes_between_samples_and_excludes_end_command(self):
        h=CommandHistory(); h.record(0,.1); h.record(.1,.2); h.record(.2,0); h.record(.3,.15)
        r=h.interval(.05,.3)
        self.assertAlmostEqual(r['distance_m'],.025)
        self.assertAlmostEqual(r['speed_variation_m_s'],.3)
        self.assertEqual(r['stops'],1)
        self.assertEqual(r['end_speed_m_s'],0)
        self.assertAlmostEqual(h.interval(.3,.4)['distance_m'],.015)
        self.assertEqual(h.interval(.3,.4)['end_speed_m_s'],.15)

    def test_negative_or_backwards_commands_rejected(self):
        h=CommandHistory(); h.record(1,.1)
        for t,v in ((.5,.2),(2,-1),(True,.1),(2,float('nan'))):
            with self.assertRaises(ValueError): h.record(t,v)

    def test_two_anchor_gain_with_speed_change_and_stop(self):
        c=load_config(PROFILE); c['estimator']['stop_coast_m']=0
        e=BeltEstimator(config=c); h=CommandHistory(); h.record(0,.1)
        e.update(frame(0,0),.1)
        e.update(frame(1,.2,ps1=True),.1,h.interval(0,.2))
        h.record(.4,.2); h.record(.8,0); h.record(.9,.2)
        # .02 + .08 + 0 + .16 = .26 m between anchors, including an unobserved stop.
        result=e.update(frame(2,1.7,ps2=True),.2,h.interval(.2,1.7))
        self.assertEqual(result.anchors,2)
        self.assertAlmostEqual(result.command_gain,1)
        self.assertAlmostEqual(result.velocity_m_s,.2)
        self.assertEqual(result.reason,'tracking')

    def test_missing_history_rejected_and_no_fabricated_anchor(self):
        e=BeltEstimator(config=load_config(PROFILE)); e.update(frame(0,0),.16)
        result=e.update(frame(1,.02,ps1=True),.16)
        self.assertEqual(result.reason,'command_history_unavailable')
        self.assertEqual(result.anchors,0)

    def test_wrong_interval_timestamp_rejected(self):
        e=BeltEstimator(config=load_config(PROFILE)); e.update(frame(0,0),.16)
        with self.assertRaises(ValueError): e.update(frame(1,.02),.16,CommandHistory().interval(.01,.02))

    def test_false_without_product_is_normal_and_unsupported_signals_ignored(self):
        m=SignalHealth(load_config(PROFILE))
        for i in range(100):
            r=m.update(frame(i,i*.02),i*.02,{'long':.16,'front':.16},Estimate())
            self.assertEqual(r['findings'],[])
        self.assertEqual(m.summary()['events'],[])

    def test_high_hypothesis_requires_running_command_and_resets_after_stop(self):
        c=load_config(PROFILE); c['health']['max_high_running_s']=.05
        m=SignalHealth(c)
        for i in range(5): m.update(frame(i,i*.02,ps1=True),i*.02,{'long':0},Estimate())
        self.assertEqual(m.events,[])
        for i in range(5,10): r=m.update(frame(i,i*.02,ps1=True),i*.02,{'long':.16},Estimate())
        self.assertIn('prolonged_high_while_commanded',[x['code'] for x in r['findings']])
        self.assertIn('Possible',r['findings'][0]['interpretation'])
        r=m.update(frame(10,.20,ps1=True),.20,{'long':0},Estimate())
        self.assertEqual(r['findings'],[])

    def test_silence_and_sequence_gaps_are_not_reported_as_proven_packet_loss(self):
        m=SignalHealth(load_config(PROFILE)); m.update(frame(0,0),0,{},Estimate())
        r=m.update(frame(3,.06),.06,{},Estimate())
        self.assertIn('observation_sequence_gap',[f['code'] for f in r['findings']])
        r=m.update(None,.2,{},Estimate())
        self.assertEqual(r['findings'][0]['code'],'telemetry_silence')

    def test_expected_edge_missing_is_ambiguous_and_uses_estimator_interval(self):
        m=SignalHealth(load_config(PROFILE))
        e=Estimate(.2,.16,.01,1,'tracking')
        r=m.update(frame(0,1),1,{'long':.16},e)
        self.assertIn('expected_edge_missing',[f['code'] for f in r['findings']])
        self.assertIn('model discrepancy',r['findings'][0]['interpretation'])

    def test_bad_schedule_cannot_silently_run_legacy_estimator(self):
        c=load_config(PROFILE); c['motion']['long_speed_schedule']=[{'track_time_s':.2,'speed_m_s':.2}]
        c['estimator']['command_history_enabled']=False
        with self.assertRaises(ValueError): validate_config(c)
        c['estimator']['command_history_enabled']=True
        c['motion']['long_speed_schedule']*=2
        with self.assertRaises(ValueError): validate_config(c)

    def test_delayed_admission_uses_source_time_only_in_history_mode(self):
        ctl=Sequence(config=load_config(PROFILE),assume_open_loop=True)
        ctl._enter('FEED',0)
        f=replace(frame(0,.10,transfer_present=True),received_time_s=.14)
        ctl.tick(f,.14)
        self.assertAlmostEqual(ctl.admission_seen_at,.10)

    def test_distance_budget_still_expires_after_a_speed_change(self):
        c=load_config(PROFILE); ctl=Sequence(config=c,assume_open_loop=True)
        ctl._enter('TRACK',0)
        ctl.tick(frame(0,.02),.02,commanded_track_distance_m=.44)
        self.assertEqual(ctl.reason,'timeout:TRACK:ps2')

    def test_predictor_bound_is_separate_from_estimated_physical_velocity(self):
        c=load_config(PROFILE); c['prediction']['wall_budget_s']=1
        ctl=Sequence(config=c); ctl.phase='TRACK'; ctl.command['long']=.1
        ctl.last_time=1; ctl.prediction_speed_bound_m_s=.24
        ctl.estimator.estimate=Estimate(.1,.1,.003,1,'tracking',1)
        result=Supervisor(c).tick(ctl,1.04)
        self.assertEqual(result['evaluated_speed_bound_m_s'],.24)
        self.assertEqual(ctl.estimator.estimate.velocity_m_s,.1)

    def test_nonmonotonic_and_contradictory_observations(self):
        m=SignalHealth(load_config(PROFILE))
        f=frame(0,0,a1_extended=True)
        r=m.update(f,0,{},Estimate())
        self.assertIn('contradictory_switches',[v['code'] for v in r['findings']])
        r=m.update(f,.01,{},Estimate())
        self.assertIn('nonmonotonic_observation',[v['code'] for v in r['findings']])

if __name__=='__main__': unittest.main()
