"""One bounded observation-only worker. It never receives or modifies a controller."""
from copy import deepcopy
import json
import math
import multiprocessing as mp
from queue import Empty,Full
import time
from config import exact_keys,number
from estimator import Estimate
from reset_protocol import digest


def worker_config(config):
    c=deepcopy(config)
    c['prediction']['backend']='mujoco_belt'
    c['prediction']['wall_budget_s']=c['prediction']['background']['compute_budget_s']
    c['prediction']['background']['enabled']=False
    return c


def worker_main(config,context,clock_domain,inbox,outbox):
    """Spawn target: no plant, actuator writer or foreground controller is passed."""
    actual=worker_config(config); profile=digest(config); worker_profile=digest(actual)
    try:
        from physics_predictor import MuJoCoBeltPredictor
        predictor=MuJoCoBeltPredictor(actual)
        outbox.put_nowait({'kind':'ready',**context,'clock_domain':clock_domain,
                          'profile_sha256':profile,'worker_profile_sha256':worker_profile})
    except Exception as error:
        outbox.put_nowait({'kind':'startup_error','error':f'{type(error).__name__}: {error}'[:512]})
        return
    while True:
        job=inbox.get()
        if job is None:return
        reply={'kind':'forecast',**context,'clock_domain':clock_domain,'profile_sha256':profile,
               'worker_profile_sha256':worker_profile,'request_id':job['request_id'],'request_hash':digest(job)}
        try:
            if job['profile_sha256']!=profile:raise ValueError('worker profile mismatch')
            reply['prediction']=predictor.rollout(Estimate(**job['estimate']),job['source_time_s'],job['decision_time_s'])
        except Exception as error:reply['error']=f'{type(error).__name__}: {error}'[:512]
        # One request can be in flight; a full outbox indicates a broken contract.
        try:outbox.put_nowait(reply)
        except Full:return


def inspect_result(reply,pending,current,now,wall_now,context,clock_domain,profile,worker_profile,settings,timing,drift):
    """Fresh/context-compatible observation is not an authorization to actuate."""
    if pending is None:return 'no_pending_request'
    try:
        if not isinstance(reply,dict):return 'malformed_result'
        if reply.get('kind')!='forecast':return 'malformed_result'
        if reply.get('session_id')!=context['session_id']:return 'wrong_session'
        if type(reply.get('generation')) is not int or reply['generation']!=context['generation']:return 'wrong_generation'
        if reply.get('clock_domain')!=clock_domain:return 'wrong_clock_domain'
        if reply.get('profile_sha256')!=profile or reply.get('worker_profile_sha256')!=worker_profile:return 'wrong_profile'
        if type(reply.get('request_id')) is not int or reply['request_id']!=pending['request_id']:return 'wrong_request'
        if reply.get('request_hash')!=digest(pending):return 'input_snapshot_mismatch'
        if 'error' in reply:return 'worker_error'
        for v in (now,wall_now):number(v,'result evaluation time',0)
        age=now-pending['decision_time_s']; wall_age=wall_now-pending['submitted_wall_s']
        if age<0 or wall_age<0 or pending['source_time_s']>now:return 'future_result'
        if age>settings['max_sim_age_s'] or now-pending['source_time_s']>timing['max_age_s']:return 'expired_simulation_age'
        if wall_age>settings['max_wall_age_s']:return 'expired_wall_age'
        if current['phase']!='TRACK' or current['command_revision']!=pending['command_revision']:return 'changed_operating_state'
        lag=current['source_sequence']-pending['source_sequence']
        if lag<0 or lag>settings['max_lag_sequences']:return 'source_sequence_outside_window'
        delta=current['source_time_s']-pending['source_time_s']
        if delta<0:return 'source_clock_moved_backwards'
        estimate=current['estimate']; original=pending['estimate']
        for item in (estimate,original):
            for k in ('y_m','velocity_m_s','uncertainty_m'):number(item[k],k,0 if k!='y_m' else None)
        projected=original['y_m']+original['velocity_m_s']*delta
        allowance=original['uncertainty_m']+estimate['uncertainty_m']+drift*delta
        if abs(estimate['y_m']-projected)>allowance+1e-12:return 'estimated_state_mismatch'
        p=reply['prediction']
        if p['status']!='complete':return 'prediction_incomplete'
        if p['action'] not in ('HOLD','CONTINUE'):return 'invalid_prediction_action'
        if type(p['expected_scenarios']) is not int or type(p['completed_scenarios']) is not int or p['expected_scenarios']!=pending['expected_scenarios'] or p['completed_scenarios']!=p['expected_scenarios']:return 'prediction_incomplete'
        json.dumps(p,allow_nan=False)
    except (KeyError,TypeError,ValueError,OverflowError):return 'malformed_result'
    return 'accepted_observation_only'


class BackgroundForecast:
    def __init__(self,config,context,clock_domain='simulation',clock=None):
        self.config=deepcopy(config);self.context=dict(context);self.domain=clock_domain
        self.settings=self.config['prediction']['background'];self.clock=clock or time.perf_counter
        self.profile=digest(config);self.worker_profile=digest(worker_config(config))
        self.started=self.clock();self.ready=False;self.failed=False;self.closed=False
        self.failure_reason=None
        self.pending=None;self.next_request=0;self.revision=0;self.last_command=None
        self.counts={'submitted':0,'busy_skips':0,'accepted_observations':0,'discarded':0,'worker_failures':0,'worker_timeouts':0}
        self.reasons={};self.max_poll_ms=0.0;self.last_record=None
        spawn=mp.get_context('spawn')
        self.inbox=spawn.Queue(maxsize=1);self.outbox=spawn.Queue(maxsize=1)
        self.process=spawn.Process(target=worker_main,args=(self.config,self.context,self.domain,self.inbox,self.outbox),daemon=True)
        try:self.process.start()
        except (OSError,RuntimeError):self.failed=True;self.failure_reason='worker_start_failed';self.counts['worker_failures']+=1

    def _failure(self,reason):
        if not self.failed:
            self.failed=True;self.counts['worker_failures']+=1
            self.failure_reason=reason
            if reason.endswith('timeout'):self.counts['worker_timeouts']+=1
        return reason

    def tick(self,estimate,source_sequence,source_time_s,phase,command,now):
        started=self.clock();signature=digest(command)
        if signature!=self.last_command:self.revision+=1;self.last_command=signature
        current={'estimate':deepcopy(estimate),'source_sequence':source_sequence,'source_time_s':source_time_s,
                 'phase':phase,'command_revision':self.revision}
        record={'time_s':now,'mode':'observe_only','control_applied':False,'state':'idle','receipt':None}
        if self.closed:record['state']='closed';return record
        try:message=self.outbox.get_nowait()
        except Empty:message=None
        except (OSError,EOFError,ValueError):message=None;self._failure('worker_channel_error')
        if message is not None:
            if not isinstance(message,dict):
                self.counts['discarded']+=1;record['receipt']={'accepted':False,'reason':'malformed_result'}
                self.reasons['malformed_result']=self.reasons.get('malformed_result',0)+1
            elif message.get('kind')=='ready':
                if (message.get('worker_profile_sha256')==self.worker_profile and
                    all(type(message.get(k)) is type(v) and message.get(k)==v for k,v in self.context.items()) and
                    message.get('clock_domain')==self.domain and message.get('profile_sha256')==self.profile):self.ready=True
                else:record['state']=self._failure('worker_profile_mismatch')
            elif message.get('kind')=='startup_error':record['state']=self._failure('worker_startup_error')
            else:
                reason=inspect_result(message,self.pending,current,now,started,self.context,self.domain,
                    self.profile,self.worker_profile,self.settings,self.config['timing'],self.config['estimator']['drift_m_s'])
                if self.failed:reason='worker_already_failed'
                accepted=reason=='accepted_observation_only'
                self.counts['accepted_observations' if accepted else 'discarded']+=1
                self.reasons[reason]=self.reasons.get(reason,0)+1
                try:json.dumps(message.get('prediction'),allow_nan=False);payload=message.get('prediction')
                except (TypeError,ValueError):payload=None
                record['receipt']={'accepted':accepted,'reason':reason,'request_id':message.get('request_id'),
                    'prediction':payload,'request':self.pending,'worker_error':message.get('error')}
                if self.pending is not None and message.get('kind')=='forecast' and all(type(message.get(k)) is type(self.pending.get(k)) and message.get(k)==self.pending.get(k) for k in ('session_id','generation','request_id','clock_domain','profile_sha256')) and message.get('request_hash')==digest(self.pending) and message.get('worker_profile_sha256')==self.worker_profile:
                    self.pending=None
        if not self.failed and not self.process.is_alive():record['state']=self._failure('worker_exited')
        if not self.failed and not self.ready and started-self.started>self.settings['startup_timeout_s']:
            record['state']=self._failure('worker_startup_timeout')
        if not self.failed and self.pending is not None and started-self.pending['submitted_wall_s']>self.settings['worker_timeout_s']:
            record['state']=self._failure('worker_response_timeout')
        if self.failed:record['state']='worker_unavailable'
        elif not self.ready:record['state']='worker_starting'
        elif self.pending is not None:
            self.counts['busy_skips']+=1;record['state']='worker_busy'
        elif phase=='TRACK' and command.get('long',0)>0 and estimate.get('reason')=='tracking' and source_time_s is not None:
            job={**self.context,'clock_domain':self.domain,'profile_sha256':self.profile,'request_id':self.next_request,
                 'source_sequence':source_sequence,'source_time_s':source_time_s,'decision_time_s':now,
                 'submitted_wall_s':started,'command_revision':self.revision,'estimate':deepcopy(estimate)}
            p=self.config['prediction']
            job['expected_scenarios']=2*len(p['position_offsets'])*len(p['speed_offsets_m_s'])*len(p['reaction_delays_s'])
            try:
                for key in ('y_m','velocity_m_s','uncertainty_m'):number(estimate[key],key,0 if key!='y_m' else None)
                if type(source_sequence) is not int or source_sequence<0:raise ValueError('source sequence required')
                json.dumps(job,allow_nan=False);self.inbox.put_nowait(job)
                self.pending=job;self.next_request+=1;self.counts['submitted']+=1;record['state']='submitted'
            except Full:record['state']='inbox_full'
            except (ValueError,TypeError,KeyError):record['state']='input_not_available'
        record['control_side_ms']=1000*(self.clock()-started)
        record['worker_failure_reason']=self.failure_reason
        self.max_poll_ms=max(self.max_poll_ms,record['control_side_ms']);self.last_record=record
        return record

    def wait_ready(self,timeout):
        """Initialization only, never called by RuntimeCore.step."""
        until=self.clock()+timeout
        while not self.ready and not self.failed and self.clock()<until:
            self.tick({},-1,None,'INIT',{},0);time.sleep(.01)
        return self.ready and not self.failed

    def close(self):
        if self.closed:return
        self.closed=True
        try:self.inbox.put_nowait(None)
        except Full:pass
        if self.process.pid is not None:
            self.process.join(self.settings['close_timeout_s'])
            if self.process.is_alive():self.process.terminate();self.process.join(self.settings['close_timeout_s'])
            if self.process.is_alive():self.process.kill();self.process.join(self.settings['close_timeout_s'])
        self.inbox.cancel_join_thread();self.outbox.cancel_join_thread()
        self.inbox.close();self.outbox.close()

    def summary(self):
        return {'enabled':True,'mode':'observe_only','control_applied':False,**self.counts,
            'discard_reasons':self.reasons,'max_control_side_ms':self.max_poll_ms,'ready':self.ready,
            'closed':self.closed,'worker_alive':self.process.is_alive(),'profile_sha256':self.profile,
            'worker_failure_reason':self.failure_reason,
            'worker_profile_sha256':self.worker_profile,
            'scope':'bounded background observations, not permission to continue, stop or reset; no hard realtime or physical validation'}
