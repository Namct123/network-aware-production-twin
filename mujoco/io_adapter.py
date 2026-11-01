"""Normalize recorded tag data; no PLC transport or actuator writes."""
from copy import deepcopy
import json
from pathlib import Path
from config import exact_keys,number
from signals import SignalFrame
from session import Envelope

class RecordingAdapter:
    def __init__(self,settings):
        exact_keys(settings,('purpose','clock','signals'),'recording adapter')
        if settings['purpose'] not in {'unverified_physical_mapping','synthetic_recording_only'}: raise ValueError('unknown mapping purpose')
        clock=settings['clock']
        exact_keys(clock,('source_scale_s','source_to_local_offset_s','uncertainty_s','max_uncertainty_s','verified'),'clock mapping')
        number(clock['source_scale_s'],'source_scale_s',0,True); number(clock['source_to_local_offset_s'],'clock offset')
        number(clock['max_uncertainty_s'],'max clock uncertainty',0)
        if clock['uncertainty_s'] is not None: number(clock['uncertainty_s'],'clock uncertainty',0)
        if type(clock['verified']) is not bool: raise ValueError('clock verified must be boolean')
        if not isinstance(settings['signals'],dict) or not settings['signals']: raise ValueError('signal map required')
        keys=[]
        for name,item in settings['signals'].items():
            exact_keys(item,('input_key','active_high','verified','plc_address'),'signal mapping')
            if not isinstance(name,str) or not name or not isinstance(item['input_key'],str) or not item['input_key']: raise ValueError('signal names required')
            if type(item['active_high']) is not bool or type(item['verified']) is not bool: raise ValueError('signal flags must be boolean')
            if item['plc_address'] is not None and not isinstance(item['plc_address'],str): raise ValueError('PLC address must be text or null')
            keys.append(item['input_key'])
        if len(set(keys))!=len(keys): raise ValueError('one input cannot silently stand for several independent sensors')
        self.settings=deepcopy(settings)

    def convert(self,row):
        exact_keys(row,('session_id','generation','sequence','source_time','received_time_s','values','quality'),'recorded row')
        if not isinstance(row['values'],dict) or not isinstance(row['quality'],dict): raise ValueError('recorded values/quality must be objects')
        number(row['source_time'],'raw source time',0); number(row['received_time_s'],'receive time',0)
        c=self.settings['clock']; source=row['source_time']*c['source_scale_s']+c['source_to_local_offset_s']
        clock_ok=c['verified'] and c['uncertainty_s'] is not None and c['uncertainty_s']<=c['max_uncertainty_s']
        values={}; quality={}; notes=[]
        for name,item in self.settings['signals'].items():
            key=item['input_key']; raw=row['values'].get(key); q=row['quality'].get(key,'unavailable')
            if q not in {'good','stale','unavailable'}: raise ValueError('unsupported input quality')
            if raw is not None and type(raw) is not bool: raise ValueError('recorded digital input must be boolean or null')
            usable=clock_ok and item['verified'] and raw is not None and q!='unavailable'
            values[name]=(raw if item['active_high'] else not raw) if usable else None
            quality[name]=q if usable else 'unavailable'
            if not usable: notes.append(name+': chưa đủ xác nhận nguồn/tín hiệu/thời gian')
        f=SignalFrame(row['sequence'],source,row['received_time_s'],values,quality,'recorded_io','mapped_recording')
        return Envelope.signal(f,row['session_id'],row['generation']),notes

def load_adapter(path):
    return RecordingAdapter(json.loads(Path(path).read_text(encoding='utf-8-sig')))

def readiness(settings):
    adapter=RecordingAdapter(settings)
    c=adapter.settings['clock']
    return {'purpose':settings['purpose'],'physical_output_supported':False,
        'clock_declared_usable':c['verified'] and c['uncertainty_s'] is not None and c['uncertainty_s']<=c['max_uncertainty_s'],
        'unconfirmed_signals':[n for n,v in settings['signals'].items() if not v['verified']],
        'unassigned_plc_addresses':[n for n,v in settings['signals'].items() if v['plc_address'] is None],
        'scope':'mapping declarations and recorded data only; not physical verification or permission to write PLC outputs'}
