"""Simulation-only reset/start handshake. Never resumes a held controller."""
from copy import deepcopy
import hashlib
import json
import re
import uuid
from config import exact_keys,number

CONFIRMATIONS=('cause_reviewed','product_reprepared','axes_and_cylinders_checked','vacuum_and_load_checked','local_interlocks_checked')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()

def identifier(value,name):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,96}',value): raise ValueError(name+': invalid identifier')

def validate_settings(settings):
    exact_keys(settings,('reset_ack_timeout_s','start_window_s','review_max_age_s','message_max_age_s'),'reset settings')
    for key,value in settings.items(): number(value,key,0,True)

class ResetCoordinator:
    def __init__(self,settings,review,session_id=None,generation=0):
        validate_settings(settings)
        if type(generation) is not int or generation<0: raise ValueError('invalid generation')
        self.settings=settings.copy(); self.review=deepcopy(review)
        self.session_id=session_id or uuid.uuid4().hex; identifier(self.session_id,'session_id')
        self.generation=generation; self.hold_id=digest(review.get('hold_context'))
        self.stage='HOLD'; self.pending=None; self.ticket=None; self.scene_id=None; self.profile_sha=None
        self.last_time=None; self.used_ids=set(); self.claimed=False; self.events=[]

    def _require(self,condition,reason):
        if not condition: raise ValueError(reason)

    def _record(self,kind,now,accepted,reason):
        row={'time_s':now,'kind':kind,'accepted':accepted,'reason':reason,'stage':self.stage,
             'generation':self.generation,'old_cycle_resume_allowed':False}
        self.events.append(row)
        return deepcopy(row)

    def _advance(self,now):
        number(now,'now',0)
        self._require(self.last_time is None or now>=self.last_time,'clock_moved_backwards')
        self.last_time=now
        if self.stage in {'RESET_PENDING','READY_NEW_CYCLE'} and now>self.deadline:
            self.stage='BLOCKED'; self.pending=None; self.ticket=None
            self._record('timeout',now,False,'confirmation_or_start_expired')

    def _common(self,p,now,keys):
        exact_keys(p,keys,'message')
        self._require(p['environment']=='simulation','simulation_only')
        self._require(p['session_id']==self.session_id,'wrong_session')
        identifier(p['request_id'],'request_id')
        self._require(p['request_id'] not in self.used_ids,'replayed_request')
        number(p['issued_at_s'],'issued_at_s',0)
        self._require(0<=now-p['issued_at_s']<=self.settings['message_max_age_s'],'old_or_future_message')
        self._require(isinstance(p['profile_sha256'],str) and re.fullmatch('[0-9a-f]{64}',p['profile_sha256']),'invalid_profile_hash')

    def handle(self,kind,p,now):
        number(now,'now',0)
        try:
            self._advance(now)
            if kind=='reset':
                self._common(p,now,('environment','session_id','request_id','generation','issued_at_s','hold_id','profile_sha256','operator_confirmations'))
                self._require(self.stage=='HOLD','reset_not_allowed_in_stage')
                self._require(type(p['generation']) is int and p['generation']==self.generation,'wrong_generation')
                self._require(p['hold_id']==self.hold_id,'wrong_hold_context')
                self._require(self.review.get('stage')=='OPERATOR_REVIEW' and not self.review.get('blockers')
                              and self.review.get('hold_context') is not None
                              and self.review.get('hold_category')=='telemetry_or_signal_quality'
                              and self.review.get('automatic_resume_allowed') is False
                              and self.review.get('restart_command_issued') is False,'review_not_ready')
                number(self.review.get('time_s'),'review_time_s',0)
                self._require(0<=now-self.review['time_s']<=self.settings['review_max_age_s'],'review_expired')
                exact_keys(p['operator_confirmations'],CONFIRMATIONS,'operator confirmations')
                self._require(all(v is True for v in p['operator_confirmations'].values()),'operator_confirmation_missing')
                self.used_ids.add(p['request_id']); self.pending=deepcopy(p)
                self.pending_accepted_at=now
                self.profile_sha=p['profile_sha256']; self.stage='RESET_PENDING'
                self.deadline=now+self.settings['reset_ack_timeout_s']
                return self._record(kind,now,True,'reset_request_recorded')
            if kind=='ack':
                exact_keys(p,('environment','session_id','request_id','previous_generation','new_generation',
                              'profile_sha256','scene_id','reset_complete','ack_at_s'),'reset acknowledgement')
                self._require(p['environment']=='simulation' and p['session_id']==self.session_id,'wrong_session_or_environment')
                self._require(self.stage=='RESET_PENDING' and self.pending is not None,'no_pending_reset')
                self._require(p['request_id']==self.pending['request_id'],'wrong_request')
                self._require(type(p['previous_generation']) is int and type(p['new_generation']) is int
                    and p['previous_generation']==self.generation and p['new_generation']==self.generation+1,'wrong_generation')
                self._require(p['profile_sha256']==self.profile_sha,'wrong_profile')
                identifier(p['scene_id'],'scene_id'); number(p['ack_at_s'],'ack_at_s',0)
                self._require(self.pending_accepted_at<=p['ack_at_s']<=now,'old_or_future_ack')
                self._require(type(p['reset_complete']) is bool,'invalid_reset_result')
                if not p['reset_complete']:
                    self.stage='BLOCKED'; self.pending=None
                    return self._record(kind,now,False,'reset_failed_requires_new_review')
                self.generation=p['new_generation']; self.scene_id=p['scene_id']
                self.ticket=uuid.uuid4().hex; self.stage='READY_NEW_CYCLE'
                self.ready_at=now
                self.deadline=now+self.settings['start_window_s']
                row=self._record(kind,now,True,'reset_confirmed_start_still_required')
                row.update(reset_ticket=self.ticket,scene_id=self.scene_id)
                return row
            if kind=='start':
                self._common(p,now,('environment','session_id','request_id','generation','issued_at_s','profile_sha256','reset_ticket'))
                self._require(self.stage=='READY_NEW_CYCLE','start_not_allowed_in_stage')
                self._require(p['issued_at_s']>=self.ready_at,'start_predates_reset_confirmation')
                self._require(type(p['generation']) is int and p['generation']==self.generation,'wrong_generation')
                self._require(p['reset_ticket']==self.ticket and p['profile_sha256']==self.profile_sha,'wrong_ticket_or_profile')
                self.used_ids.add(p['request_id']); self.stage='RUNNING'; self.start_id=p['request_id']
                self.ticket=None
                return self._record(kind,now,True,'new_cycle_grant_created')
            raise ValueError('unknown_message_kind')
        except (ValueError,TypeError) as error:
            return self._record(kind,now,False,str(error))

    def take_start(self):
        """Single-use grant for the separate simulator adapter, never old-cell resume."""
        if self.stage!='RUNNING' or self.claimed: return None
        self.claimed=True
        return {'environment':'simulation','session_id':self.session_id,'generation':self.generation,
                'scene_id':self.scene_id,'profile_sha256':self.profile_sha,'start_id':self.start_id,
                'old_cycle_resume_allowed':False}

    def poll(self,now):
        """Host must call periodically even if no message arrives."""
        self._advance(now)
        return {'stage':self.stage,'generation':self.generation,'old_cycle_resume_allowed':False}

    def finish(self,scene_id,completed,now):
        self._advance(now)
        if self.stage!='RUNNING' or not self.claimed or scene_id!=self.scene_id or type(completed) is not bool:
            return self._record('finish',now,False,'wrong_running_scene')
        self.stage='COMPLETE' if completed else 'BLOCKED'
        return self._record('finish',now,True,'new_cycle_complete' if completed else 'new_cycle_stopped')
