"""Scoped wire messages and a local simulation command boundary."""
from copy import deepcopy
from dataclasses import dataclass,asdict,replace
import json
import math
import re
from config import exact_keys,number
from signals import SignalFrame

@dataclass(frozen=True)
class Envelope:
    session_id:str
    generation:int
    kind:str
    sequence:int
    source_time_s:float
    received_time_s:float
    clock_domain:str
    payload:dict

    def __post_init__(self):
        if not isinstance(self.session_id,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,96}',self.session_id): raise ValueError('invalid session')
        if type(self.generation) is not int or self.generation<0: raise ValueError('invalid generation')
        if self.kind not in {'signal','command'}: raise ValueError('invalid message kind')
        if type(self.sequence) is not int or self.sequence<0: raise ValueError('invalid message sequence')
        for v in (self.source_time_s,self.received_time_s): number(v,'message time',0)
        if self.received_time_s<self.source_time_s: raise ValueError('reception precedes source')
        if self.clock_domain not in {'simulation','mapped_recording'} or not isinstance(self.payload,dict): raise ValueError('invalid domain/payload')
        json.dumps(self.payload,allow_nan=False)

    @classmethod
    def signal(cls,frame,session_id,generation):
        return cls(session_id,generation,'signal',frame.sequence,frame.source_time_s,frame.received_time_s,
                   frame.clock_domain,deepcopy(frame.as_dict()))

    def frame(self):
        if self.kind!='signal': raise ValueError('not a signal message')
        p=deepcopy(self.payload)
        if p.get('sequence')!=self.sequence or p.get('source_time_s')!=self.source_time_s or p.get('clock_domain')!=self.clock_domain:
            raise ValueError('signal header/body mismatch')
        p['received_time_s']=self.received_time_s
        return SignalFrame(**p)

    def as_dict(self): return asdict(self)

class MessageGuard:
    def __init__(self,session_id,generation=0,clock_domain='simulation'):
        self.session_id=session_id; self.generation=generation; self.clock_domain=clock_domain
        self.last={}; self.accepted=0; self.rejected=0

    def accept(self,message,now,kind):
        number(now,'receive time',0)
        reason='accepted'
        if message.session_id!=self.session_id: reason='wrong_session'
        elif message.generation!=self.generation: reason='wrong_generation'
        elif message.clock_domain!=self.clock_domain: reason='wrong_clock_domain'
        elif message.kind!=kind: reason='wrong_kind'
        elif message.received_time_s>now or message.source_time_s>now: reason='future_message'
        elif kind in self.last and (message.sequence<=self.last[kind][0] or message.source_time_s<self.last[kind][1]): reason='old_or_repeated_message'
        if reason=='accepted' and kind=='signal':
            try: message.frame()
            except (ValueError,TypeError): reason='invalid_signal_body'
        if reason=='accepted':
            self.last[kind]=(message.sequence,message.source_time_s); self.accepted+=1
        else: self.rejected+=1
        return {'accepted':reason=='accepted','reason':reason,'session_id':self.session_id,'generation':self.generation,
                'sequence':message.sequence,'kind':kind,'time_s':now}

class CommandGate:
    """Validates only local commands. No device/network write implementation."""
    def __init__(self,config):
        self.config=config
        self.last={'front':0.0,'long':0.0,'targets':{},'vacuum':False,'hold':True}

    def validate(self,command):
        exact_keys(command,('front','long','targets','vacuum','hold'),'command')
        for k,limit in (('front',self.config['motion']['front_speed_m_s']),('long',self.config['motion']['test_speed_range_m_s'][1])):
            number(command[k],k,0)
            if command[k]>limit+1e-12: raise ValueError('command speed outside configured range')
        if type(command['vacuum']) is not bool or type(command['hold']) is not bool: raise ValueError('command flags must be boolean')
        if command['hold'] and (command['front']!=0 or command['long']!=0): raise ValueError('HOLD requires zero belt commands')
        if not isinstance(command['targets'],dict) or not command['targets'].keys()<=self.config['geometry']['joint_limits_m'].keys(): raise ValueError('unknown motion axis')
        for k,v in command['targets'].items():
            number(v,k)
            lo,hi=self.config['geometry']['joint_limits_m'][k]
            if not lo<=v<=hi: raise ValueError('axis command outside limits')
        self.last=deepcopy(command)
        return deepcopy(command)

    def stop(self):
        result=deepcopy(self.last); result.update(front=0.0,long=0.0,hold=True)
        return result
