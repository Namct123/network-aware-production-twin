"""Rule-based hypotheses from receiver observations, never injected fault labels."""
from clock_checks import elapsed_at_least

class SignalHealth:
    def __init__(self, config):
        self.config=config
        self.settings=config.get('health',{'enabled':False})
        self.enabled=self.settings['enabled']
        self.last_sequence=None
        self.last_source=None
        self.last_received=0.0
        self.high_since={}
        self.events=[]
        self.seen=set()

    def update(self, frame, now, source_commands, estimate):
        if not self.enabled: return None
        findings=[]
        def add(code,signal,explanation):
            item={'code':code,'signal':signal,'interpretation':explanation}
            findings.append(item)
            key=(code,signal)
            if key not in self.seen:
                self.events.append({'first_observed_s':now,**item})
                self.seen.add(key)
        timing=self.config['timing']
        if frame is None:
            if elapsed_at_least(now,self.last_received,timing['silence_timeout_s']):
                add('telemetry_silence',None,'No received observations; transport/source interruption is unresolved.')
        else:
            age=now-frame.source_time_s
            gap=None if self.last_source is None else frame.source_time_s-self.last_source
            monotonic=(self.last_sequence is None or frame.sequence>self.last_sequence) and (gap is None or gap>0)
            if not monotonic:
                add('nonmonotonic_observation',None,'Timestamp/sequence order is inconsistent.')
                self.high_since.clear()
            else:
                if self.last_sequence is not None and frame.sequence>self.last_sequence+1:
                    add('observation_sequence_gap',None,'Receiver missed observations; packet loss, reordering or coalescing cannot be distinguished.')
                if gap is not None and gap>timing['max_sample_gap_s']:
                    add('observation_time_gap',None,'Source-time observation gap exceeds the configured limit.')
                fresh=frame.aged(now,timing['max_age_s'])
                if age>timing['max_age_s']:
                    add('stale_observation',None,'Observation is too old for current control decisions.')
                continuous=(gap is not None and gap<=timing['max_sample_gap_s'] and age<=timing['max_age_s']
                            and frame.sequence==self.last_sequence+1)
                for name,belt in (('ps1','long'),('ps2','long'),('transfer_present','front')):
                    if name=='transfer_present' and 'mechanics' not in self.config: continue
                    quality=fresh.quality.get(name)
                    if quality!='good':
                        self.high_since.pop(name,None)
                        add('required_signal_unusable',name,'Required observation is unavailable or stale; sensor failure is not established.')
                        continue
                    if fresh.values.get(name) is True and source_commands.get(belt,0)>0:
                        if not continuous or name not in self.high_since: self.high_since[name]=frame.source_time_s
                        if frame.source_time_s-self.high_since[name]>=self.settings['max_high_running_s']:
                            add('prolonged_high_while_commanded',name,'Possible stuck-high sensor, stationary/long product or transport/model mismatch.')
                    else: self.high_since.pop(name,None)
                for axis in ('a1','a2'):
                    names=(axis+'_retracted',axis+'_extended')
                    if all(fresh.quality.get(k)=='good' and fresh.values.get(k) is True for k in names):
                        add('contradictory_switches',axis,'Both endpoint switches are active; wiring, sensor or model inconsistency.')
                if fresh.quality.get('ps2')=='good':
                    if fresh.values.get('ps2') is True and estimate.anchors<2:
                        add('unmatched_pickup_observation','ps2','Pickup detection has no valid two-anchor match; missed upstream edge or inconsistent transit model.')
                    if (fresh.values.get('ps2') is False and estimate.anchors==1 and estimate.y_m is not None
                        and estimate.y_m-estimate.uncertainty_m+self.config['geometry']['product_size_m'][1]/2
                        >self.config['geometry']['ps_y_m']['ps2']+self.settings['edge_slack_m']):
                        add('expected_edge_missing','ps2','Model interval passed pickup beam without a rising edge; sensor, transport or model discrepancy remains unresolved.')
                self.last_sequence=frame.sequence
                self.last_source=frame.source_time_s
                self.last_received=now
        return {'time_s':now,'status':'suspect' if findings else 'no_rule_triggered','findings':findings}

    def summary(self):
        return {'enabled':self.enabled,'events':self.events,
                'scope':'rule-based hypotheses, not certified fault isolation or measured detection accuracy; no automatic HOLD recovery'}
