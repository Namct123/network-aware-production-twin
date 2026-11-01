"""Integrate locally issued commands; never infer physical speed from plant truth."""
import math

class CommandHistory:
    def __init__(self):
        self.records=[{'time_s':0.0,'speed_m_s':0.0}]

    def record(self,time_s,speed_m_s):
        if not all(type(v) in (float,int) and math.isfinite(v) and v>=0 for v in (time_s,speed_m_s)):
            raise ValueError('finite nonnegative command time/speed required')
        last=self.records[-1]
        if time_s<last['time_s']: raise ValueError('command times must be monotonic')
        if time_s==last['time_s']:
            last['speed_m_s']=float(speed_m_s)
        elif speed_m_s!=last['speed_m_s']:
            self.records.append({'time_s':float(time_s),'speed_m_s':float(speed_m_s)})

    def interval(self,start_s,end_s):
        if not all(math.isfinite(v) for v in (start_s,end_s)) or not 0<=start_s<=end_s:
            raise ValueError('ordered finite command interval required')
        speed=0.0
        for item in self.records:
            if item['time_s']<start_s: speed=item['speed_m_s']
            else: break
        distance=variation=0.0; stops=0; cursor=start_s; peak=speed
        for item in self.records:
            t,v=item['time_s'],item['speed_m_s']
            if t<start_s: continue
            if t>=end_s: break  # sample at end precedes the command issued at end.
            distance+=speed*(t-cursor)
            variation+=abs(v-speed); stops+=int(speed>0 and v==0)
            peak=max(peak,v); speed=v; cursor=t
        distance+=speed*(end_s-cursor)
        return {'start_s':start_s,'end_s':end_s,'distance_m':distance,
                'speed_variation_m_s':variation,'stops':stops,'end_speed_m_s':speed,'max_speed_m_s':peak}
