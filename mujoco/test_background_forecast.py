"""Identity/age/state guards and bounded parent scheduling, without slow processes."""
from copy import deepcopy
import json
from pathlib import Path
from queue import Queue
import unittest
from unittest.mock import patch
from background_forecast import BackgroundForecast,inspect_result,worker_config
from config import load_config,validate_config
from reset_protocol import digest

HERE=Path(__file__).parent

class FakeQueue(Queue):
    def cancel_join_thread(self):pass
    def close(self):pass

class FakeProcess:
    pid=123
    def __init__(self,**kwargs):self.alive=True;self.joins=0
    def start(self):pass
    def is_alive(self):return self.alive
    def join(self,timeout):self.joins+=1;self.alive=False
    def terminate(self):self.alive=False
    def kill(self):self.alive=False

class FakeContext:
    def Queue(self,maxsize):return FakeQueue(maxsize)
    def Process(self,**kwargs):return FakeProcess(**kwargs)

class BackgroundTests(unittest.TestCase):
    def setUp(self):
        self.c=load_config(HERE/'configs/background_observer_20261103.json')
        self.ctx={'session_id':'session','generation':1};self.wall=100.0
        with patch('background_forecast.mp.get_context',return_value=FakeContext()):
            self.observer=BackgroundForecast(self.c,self.ctx,clock=lambda:self.wall)
        self.estimate={'y_m':0.0,'velocity_m_s':.1,'uncertainty_m':.005,'reason':'tracking','anchors':1,'command_gain':1.0}
        self.command={'front':0.0,'long':.16,'targets':{},'vacuum':False,'hold':False}
        self.observer.outbox.put_nowait({'kind':'ready',**self.ctx,'clock_domain':'simulation','profile_sha256':self.observer.profile,'worker_profile_sha256':self.observer.worker_profile})
        self.observer.tick(self.estimate,1,0,'TRACK',self.command,0)
        self.job=deepcopy(self.observer.pending)

    def tearDown(self):self.observer.close()

    def reply(self):
        return {'kind':'forecast',**self.ctx,'clock_domain':'simulation','profile_sha256':self.observer.profile,
            'worker_profile_sha256':self.observer.worker_profile,'request_id':0,'request_hash':digest(self.job),
            'prediction':{'status':'complete','action':'CONTINUE','expected_scenarios':54,'completed_scenarios':54,'compute_ms':50,'margins_m':{'HOLD':.1,'CONTINUE':.1}}}

    def inspect(self,reply=None,current=None,now=.04,wall=100.05):
        current=current or {'estimate':{**self.estimate,'y_m':.004},'source_sequence':3,'source_time_s':.04,'phase':'TRACK','command_revision':self.job['command_revision']}
        return inspect_result(reply or self.reply(),self.job,current,now,wall,self.ctx,'simulation',self.observer.profile,self.observer.worker_profile,
            self.c['prediction']['background'],self.c['timing'],self.c['estimator']['drift_m_s'])

    def test_valid_observation_never_authorizes_a_command(self):
        self.assertEqual(self.inspect(),'accepted_observation_only')
        self.observer.inbox.get_nowait();self.observer.outbox.put_nowait(self.reply())
        before=deepcopy(self.command);self.wall=100.05
        record=self.observer.tick({**self.estimate,'y_m':.004},3,.04,'TRACK',self.command,.04)
        self.assertTrue(record['receipt']['accepted']);self.assertFalse(record['control_applied'])
        self.assertEqual(self.command,before)

    def test_identity_and_snapshot_rejections(self):
        for key,value,reason in [('session_id','other','wrong_session'),('generation',0,'wrong_generation'),
            ('generation',True,'wrong_generation'),('clock_domain','mapped_recording','wrong_clock_domain'),
            ('profile_sha256','other','wrong_profile'),('request_id',99,'wrong_request'),('request_hash','other','input_snapshot_mismatch')]:
            reply=self.reply();reply[key]=value;self.assertEqual(self.inspect(reply),reason)

    def test_two_clock_ages_and_context_changes_are_rejected(self):
        self.assertEqual(self.inspect(now=.2),'expired_simulation_age')
        self.assertEqual(self.inspect(wall=101),'expired_wall_age')
        current={'estimate':self.estimate,'source_sequence':3,'source_time_s':.04,'phase':'HOLD','command_revision':1}
        self.assertEqual(self.inspect(current=current),'changed_operating_state')
        current.update(phase='TRACK',command_revision=self.job['command_revision'],source_sequence=99)
        self.assertEqual(self.inspect(current=current),'source_sequence_outside_window')
        current.update(source_sequence=3,estimate={**self.estimate,'y_m':1.0})
        self.assertEqual(self.inspect(current=current),'estimated_state_mismatch')

    def test_incomplete_or_nonfinite_predictions_are_not_accepted(self):
        r=self.reply();r['prediction']['completed_scenarios']=1
        self.assertEqual(self.inspect(r),'prediction_incomplete')
        r=self.reply();r['prediction']['compute_ms']=float('nan')
        self.assertEqual(self.inspect(r),'malformed_result')

    def test_busy_or_wrong_reply_does_not_add_another_request(self):
        bad=self.reply();bad['request_id']=99
        self.observer.outbox.put_nowait(bad)
        record=self.observer.tick(self.estimate,2,.02,'TRACK',self.command,.02)
        self.assertFalse(record['receipt']['accepted']);self.assertEqual(self.observer.pending,self.job)
        self.assertEqual(self.observer.counts['submitted'],1);self.assertEqual(self.observer.inbox.qsize(),1)
        self.assertEqual(self.observer.process.joins,0)

    def test_worker_timeout_or_exit_is_contained_and_close_is_idempotent(self):
        self.wall=102
        self.assertEqual(self.observer.tick(self.estimate,2,.02,'TRACK',self.command,.02)['state'],'worker_unavailable')
        self.assertEqual(self.observer.counts['worker_timeouts'],1)
        self.assertEqual(self.observer.process.joins,0)
        self.observer.close();self.observer.close()
        self.assertFalse(self.observer.summary()['worker_alive'])

    def test_enabled_background_requires_fast_path_and_declared_settings(self):
        c=deepcopy(self.c);c['prediction']['backend']='mujoco_belt'
        with self.assertRaises(ValueError):validate_config(c)
        c=deepcopy(self.c);c['prediction']['background']['mode']='control'
        with self.assertRaises(ValueError):validate_config(c)
        from calibrate import parameter_report
        fields={r['path']:r for r in parameter_report(self.c)}
        self.assertEqual(fields['prediction.background.max_lag_sequences']['unit'],'1')
        self.assertEqual(worker_config(self.c)['prediction']['backend'],'mujoco_belt')

if __name__=='__main__':unittest.main()
