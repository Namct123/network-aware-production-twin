"""Cycle-latched speed degradation and conservative HOLD from received evidence."""
from speed_policy import speed_limit

class Reconfiguration:
    STOP_CODES={'telemetry_silence','stale_observation','required_signal_unusable',
                'nonmonotonic_observation','contradictory_switches','prolonged_high_while_commanded',
                'unmatched_pickup_observation','expected_edge_missing'}

    def __init__(self,config):
        self.config=config
        self.settings=config.get('reconfiguration',{'enabled':False})
        self.enabled=self.settings['enabled']
        self.mode='NORMAL'
        self.warning_ticks=0
        self.last_source=None
        self.last_tick=None
        self.events=[]
        self.adaptive=self.settings.get('adaptive',{}).get('enabled',False)
        self.age_high=0.0
        self.gap_high=config['timing']['physics_step_s']*config['timing']['sample_steps']
        self.cap=config['motion']['test_speed_range_m_s'][1]

    def tick(self,controller,frame,health_record,now,source_window=None):
        if not self.enabled: return None
        if self.last_tick is not None and now<=self.last_tick:
            raise ValueError('reconfiguration requires increasing decision times')
        self.last_tick=now
        previous=self.mode
        requested=controller.command['long']
        codes={f['code'] for f in (health_record or {}).get('findings',[])}
        if frame is not None:
            if self.last_source is not None:
                self.gap_high=max(self.gap_high,frame.source_time_s-self.last_source)
            self.last_source=frame.source_time_s
        age=None if self.last_source is None else now-self.last_source
        if age is not None: self.age_high=max(self.age_high,age)
        warning=(age is not None and age+1e-9>=self.settings['warning_age_s']) or bool(
            codes & {'observation_sequence_gap','observation_time_gap'})
        reason='no_reconfiguration'
        if controller.phase=='HOLD':
            self.mode='HOLD'; reason=controller.reason
        elif controller.phase=='DONE':
            self.mode='COMPLETE'; reason='cycle_complete'
        elif self.mode=='HOLD' or health_record is None:
            reason='reconfiguration_reset_required' if self.mode=='HOLD' else 'reconfiguration_health_unavailable'
            controller.hold(reason,now); self.mode='HOLD'
        elif codes & self.STOP_CODES:
            reason='reconfiguration:'+sorted(codes & self.STOP_CODES)[0]
            controller.hold(reason,now)
            self.mode='HOLD'
        elif self.mode!='DEGRADED':
            self.warning_ticks=self.warning_ticks+1 if warning else 0
            if self.warning_ticks>=self.settings['warning_ticks']:
                self.mode='DEGRADED'; reason='persistent_telemetry_warning'
        applied=False
        adaptive_result=None
        if self.adaptive and controller.phase=='TRACK' and self.mode!='HOLD':
            try:
                adaptive_result=speed_limit(self.config,controller.estimator.estimate,self.age_high,self.gap_high,source_window)
                self.cap=min(self.cap,adaptive_result['cap_m_s'])
                if requested>0 and self.cap<self.config['motion']['test_speed_range_m_s'][0]-1e-12:
                    reason='adaptive_no_admissible_speed'; controller.hold(reason,now); self.mode='HOLD'
                else:
                    controller.command['long']=min(requested,self.cap)
                    applied=controller.command['long']<requested
                    if applied: self.mode='DEGRADED'; reason='adaptive_speed_cap'
            except (ValueError,OverflowError) as error:
                reason='adaptive_invalid_inputs'; controller.hold(reason,now); self.mode='HOLD'
                adaptive_result={'error':str(error)}
        elif self.mode=='DEGRADED' and controller.phase=='TRACK':
            controller.command['long']=min(requested,self.settings['degraded_long_speed_m_s'])
            applied=controller.command['long']<requested
            if applied: reason='degraded_speed_cap'
        record={'time_s':now,'mode':self.mode,'phase':controller.phase,'reason':reason,
                'observation_age_s':age,'warning_ticks':self.warning_ticks,'evidence_codes':sorted(codes),
                'requested_long_speed_m_s':requested,'selected_long_speed_m_s':controller.command['long'],
                'speed_cap_applied':applied}
        if self.adaptive:
            record.update(adaptive=adaptive_result,latched_cap_m_s=self.cap,
                          observed_age_high_s=self.age_high,observed_gap_high_s=self.gap_high)
        if self.mode!=previous:
            self.events.append({'previous_mode':previous,**record})
        return record

    def summary(self):
        return {'enabled':self.enabled,'adaptive_enabled':self.adaptive,'mode':self.mode,'events':self.events,
                'scope':'rule-based per-cycle speed cap and HOLD; no sensor bypass, automatic HOLD reset or physical validation'}
