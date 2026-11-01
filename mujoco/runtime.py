"""Shared controller path for simulation and recorded input; no plant truth input."""
import uuid
from copy import deepcopy
from command_history import CommandHistory
from sequence import Sequence
from supervisor import Supervisor
from health import SignalHealth
from recovery import RecoveryAssessment
from reconfiguration import Reconfiguration
from session import Envelope,MessageGuard,CommandGate
from config import number

class RuntimeCore:
    def __init__(self,config,bin_number=1,assume_open_loop=False,session_context=None,clock_domain='simulation'):
        ctx=session_context or {'session_id':uuid.uuid4().hex,'generation':0}
        if set(ctx)!={'session_id','generation'}: raise ValueError('session context requires session_id and generation')
        Envelope(ctx['session_id'],ctx['generation'],'command',0,0,0,clock_domain,{})
        self.config=config; self.context=dict(ctx); self.clock_domain=clock_domain
        self.controller=Sequence(bin_number,assume_open_loop=assume_open_loop,config=config)
        self.supervisor=Supervisor(config); self.health=SignalHealth(config)
        self.reconfiguration=Reconfiguration(config)
        self.recovery=RecoveryAssessment(config.get('recovery',{'enabled':False}),config['timing'],'mechanics' in config)
        self.history=CommandHistory(); self.front_history=CommandHistory()
        self.guard=MessageGuard(ctx['session_id'],ctx['generation'],clock_domain)
        self.gate=CommandGate(config); self.tick_count=0; self.last_now=None
        self.schedule_index=0; self.schedule_events=[]

    def wrap(self,frame): return Envelope.signal(frame,**self.context)

    def stop(self,reason,now):
        self.controller.command=deepcopy(self.gate.last)
        self.controller.hold(reason,now)
        self.controller.command=self.gate.stop()

    def step(self,message,now):
        number(now,'runtime time',0)
        if self.last_now is not None and now<self.last_now: raise ValueError('runtime clock moved backwards')
        self.last_now=now
        ctl=self.controller; before=ctl.phase; frame=None; receipt=None
        if message is not None:
            receipt=self.guard.accept(message,now,'signal')
            if receipt['accepted']:
                try: frame=message.frame()
                except (ValueError,TypeError) as error:
                    receipt=dict(receipt,accepted=False,reason='invalid_signal_body',error=str(error))
        if frame is not None:
            start=ctl.estimator.time
            integral=self.history.interval(start,frame.source_time_s) if start is not None else None
            track_distance=self.history.interval(ctl.entered,now)['distance_m'] if before=='TRACK' else 0.0
            source_commands={'long':self.history.interval(frame.source_time_s,frame.source_time_s)['end_speed_m_s'],
                             'front':self.front_history.interval(frame.source_time_s,frame.source_time_s)['end_speed_m_s']}
            ctl.tick(frame,now,source_belt_command=source_commands['long'],command_interval=integral,
                     commanded_track_distance_m=track_distance,source_to_now_interval=self.history.interval(frame.source_time_s,now))
        else:
            source_commands={}; ctl.watchdog(now)
        if ctl.phase=='TRACK':
            schedule=self.config['motion'].get('long_speed_schedule',[])
            while self.schedule_index<len(schedule) and now-ctl.entered+1e-9>=schedule[self.schedule_index]['track_time_s']:
                entry=schedule[self.schedule_index]; ctl.command['long']=entry['speed_m_s']
                self.schedule_events.append({'issued_time_s':now,**entry}); self.schedule_index+=1
        h=self.health.update(frame,now,source_commands,ctl.estimator.estimate)
        estimate_time=ctl.estimator.time
        window=self.history.interval(estimate_time,now) if estimate_time is not None else None
        policy=self.reconfiguration.tick(ctl,frame,h,now,source_window=window)
        if ctl.estimator.history_mode:
            past=self.history.interval(ctl.last_time or now,now)
            ctl.prediction_speed_bound_m_s=max(past['max_speed_m_s'],ctl.command['long'])*self.config['estimator']['command_gain_range'][1]
        prediction=self.supervisor.tick(ctl,now)
        if now>=self.config['timing']['run_budget_s'] and ctl.phase not in {'HOLD','DONE'}: ctl.hold('run_budget_exceeded',now)
        command_error=None
        try: command=self.gate.validate(ctl.command)
        except ValueError as error:
            command_error=str(error); self.stop('invalid_command',now); command=self.gate.validate(ctl.command)
        review=self.recovery.tick(ctl,frame,h,now)
        outgoing=Envelope(self.context['session_id'],self.context['generation'],'command',self.tick_count,now,now,self.clock_domain,command)
        outgoing_check=self.guard.accept(outgoing,now,'command')
        if not outgoing_check['accepted']: raise ValueError('internal command ordering failure')
        self.history.record(now,command['long']); self.front_history.record(now,command['front']); self.tick_count+=1
        return {'frame':frame,'before_phase':before,'command':command,'prediction':prediction,'health':h,'policy':policy,
                'recovery':review,'received_message':message.as_dict() if message is not None else None,
                'input_guard':receipt,'output_guard':outgoing_check,'command_message':outgoing.as_dict(),
                'command_error':command_error}
