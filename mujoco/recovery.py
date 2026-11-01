"""Read-only post-HOLD assessment; no reset, resume or actuator command API."""

def classify(reason):
    if reason in {'telemetry_timeout','sampling_gap'} or reason.startswith('invalid_or_stale:'):
        return 'telemetry_or_signal_quality'
    if reason=='unconfirmed_xy_a2_midstroke_and_vacuum': return 'unconfirmed_motion_or_vacuum'
    if reason in {'nonmonotonic_sample','command_history_unavailable'}: return 'clock_or_history'
    if reason.startswith(('prediction_','predictive_','adaptive_')) or reason in {'pick_uncertainty_exceeded','implausible_command_gain','implausible_transit_speed','run_budget_exceeded'}:
        return 'model_or_computation'
    if reason=='target_outside_workspace': return 'geometry_or_workspace'
    if reason.startswith(('timeout:','contradictory_','reconfiguration:')) or reason in {'ps2_without_ps1','missing_optical_anchors','initial_state_not_confirmed','unexpected_ps1_retrigger'}:
        return 'sensor_or_sequence'
    return 'unclassified_requires_diagnosis'

class RecoveryAssessment:
    def __init__(self,settings,timing,has_transfer=False):
        self.settings=settings.copy()
        self.timing=timing.copy()
        self.has_transfer=has_transfer
        self.enabled=self.settings['enabled']
        self.last_sequence=None
        self.last_source=None
        self.fresh_streak=0
        self.stage='NOT_HOLD'
        self.events=[]
        self.latest=None

    def tick(self,controller,frame,health_record,now):
        if not self.enabled: return None
        previous=self.stage
        blockers=[]
        context=controller.hold_context
        category=classify(controller.reason) if controller.phase=='HOLD' else None
        if controller.phase!='HOLD':
            self.stage='NOT_HOLD'; self.fresh_streak=0
        elif context is None:
            self.stage='MANUAL_INTERVENTION'; blockers=['hold_context_missing']
        else:
            timing=self.timing
            required=['ps1','ps2','a1_retracted','a1_extended','a2_retracted','a2_extended']
            if self.has_transfer: required.append('transfer_present')
            usable=False; fresh=None
            if frame is not None:
                fresh=frame.aged(now,timing['max_age_s'])
                newer=self.last_sequence is None or (frame.sequence>self.last_sequence and frame.source_time_s>self.last_source)
                usable=(newer and frame.source_time_s>context['time_s'] and
                    all(fresh.quality.get(k)=='good' for k in required))
                ordered=(self.last_sequence is None or frame.sequence==self.last_sequence+1) and (
                    self.last_source is None or 0<frame.source_time_s-self.last_source<=timing['max_sample_gap_s'])
                self.fresh_streak=(self.fresh_streak+1 if ordered else 1) if usable else 0
                if newer:
                    self.last_sequence=frame.sequence; self.last_source=frame.source_time_s
            else:
                # Missing one expected receiver tick breaks a continuous streak.
                self.fresh_streak=0
            if not usable: blockers.append('fresh_post_hold_observation_required')
            if self.fresh_streak<self.settings['fresh_samples']: blockers.append('continuous_fresh_streak_incomplete')
            held=now-context['time_s']
            if held<self.settings['settle_wait_s']: blockers.append('command_settle_wait_incomplete')
            if controller.command['front']!=0 or controller.command['long']!=0 or not controller.command['hold']:
                blockers.append('hold_command_not_confirmed')
            if controller.command['vacuum']: blockers.append('possible_held_load_requires_manual_handling')
            if fresh is not None and usable:
                v=fresh.values
                if not (v['a1_retracted'] and not v['a1_extended'] and v['a2_retracted'] and not v['a2_extended']):
                    blockers.append('cylinder_retracted_state_not_confirmed')
            if health_record is None or health_record.get('findings'):
                blockers.append('health_findings_not_cleared')
            if category!='telemetry_or_signal_quality': blockers.append('original_cause_requires_manual_diagnosis')
            if held>self.settings['max_hold_age_s']: blockers.append('hold_too_old_for_review_path')
            manual=any(b in blockers for b in ('possible_held_load_requires_manual_handling',
                'cylinder_retracted_state_not_confirmed','original_cause_requires_manual_diagnosis',
                'hold_too_old_for_review_path','hold_command_not_confirmed'))
            self.stage='MANUAL_INTERVENTION' if manual else 'WAIT_OBSERVATIONS' if blockers else 'OPERATOR_REVIEW'
        record={'time_s':now,'stage':self.stage,'hold_category':category,'blockers':blockers,
                'fresh_streak':self.fresh_streak,'automatic_resume_allowed':False,'restart_command_issued':False,
                'hold_context':context,
                'mandatory_operator_checks':[] if controller.phase!='HOLD' else [
                    'Identify and secure the current product/load; preserve suction if needed.',
                    'Verify actual product location, XY/home, cylinder state and vacuum using real observations.',
                    'Confirm local PLC interlocks/E-stop state; this assessment has no safety acknowledgement.',
                    'Use an explicit reset/reinitialization procedure after state reconciliation; not implemented here.'],
                'unresolved_state':['actual_product_pose','xy_home_feedback','vacuum_feedback','plc_interlocks'] if controller.phase=='HOLD' else []}
        if self.stage!=previous: self.events.append({k:v for k,v in record.items() if k!='hold_context'})
        self.latest=record
        return record

    def summary(self):
        return {'enabled':self.enabled,'stage':self.stage,'events':self.events,'latest':self.latest,
                'scope':'read-only review assessment, not machine safety validation or permission to restart'}
