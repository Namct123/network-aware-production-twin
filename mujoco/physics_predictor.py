"""Independent MuJoCo belt/block forecasts from estimates, never a live Cell state."""
from itertools import product
import math
import time

class MuJoCoBeltPredictor:
    def __init__(self,config,clock=None):
        import mujoco
        self.mj=mujoco; self.config=config; self.clock=clock or time.perf_counter
        self.parameters=config['prediction']; self.dt=config['timing']['physics_step_s']
        self.period=self.dt*config['timing']['sample_steps']
        self.limit=config['geometry']['long_belt_y_m'][1]-config['geometry']['product_size_m'][1]/2-self.parameters['stop_margin_m']
        self.models={}; self.stopped=self._model(0.0)

    def _model(self,speed):
        key=round(speed,9)
        if key in self.models: return self.models[key]
        c=self.config; g=c['geometry']; p=c['plant']; m=c.get('mechanics',{})
        a,b=g['long_belt_y_m']; half=[v/2 for v in g['product_size_m']]
        z=m.get('belt_surface_z_m',g['product_initial_xyz_m'][2]-half[2]-.001)
        width=m.get('long_belt_width_m',.078)
        vec=lambda xs:' '.join(str(v) for v in xs)
        xml=f'''<mujoco model="estimated_belt_forecast"><option timestep="{self.dt}" gravity="{vec(m.get('gravity_m_s2',[0,0,-9.81]))}"/>
        <worldbody><geom name="belt" type="box" pos="0 {(a+b)/2} {z-.002}"
        size="{width/2} {(b-a)/2} .002" friction="{vec(p['belt_friction'])}" surfacevel="0 {speed} 0 0 0 0"/>
        <body name="part" pos="0 0 {z+half[2]+.0005}"><freejoint/>
        <geom type="box" size="{vec(half)}" mass="{p['product_mass_kg']}" friction="{vec(p['product_friction'])}"/></body>
        </worldbody></mujoco>'''
        model=self.mj.MjModel.from_xml_string(xml)
        if len(self.models)>=16: self.models.pop(next(iter(self.models)))
        self.models[key]=model
        return model

    def rollout(self,estimate,source_time_s,now_s):
        vals=(estimate.y_m,estimate.velocity_m_s,estimate.uncertainty_m,source_time_s,now_s)
        if any(v is None or type(v) not in (float,int) or not math.isfinite(v) for v in vals): raise ValueError('finite estimated state required')
        if now_s<source_time_s or estimate.velocity_m_s<0 or estimate.uncertainty_m<0: raise ValueError('invalid estimated state/time')
        start=self.clock(); p=self.parameters; age=now_s-source_time_s
        axes=list(product(p['position_offsets'],p['speed_offsets_m_s'],p['reaction_delays_s']))
        expected=2*len(axes); completed=steps=0; margins={}
        uncertainty=estimate.uncertainty_m+self.config['estimator']['drift_m_s']*age
        def result(status,action,reason):
            return {'status':status,'action':action,'reason':reason,'completed_scenarios':completed,
                'expected_scenarios':expected,'rollout_steps':steps,'compute_ms':(self.clock()-start)*1000,
                'margins_m':margins,'estimate_age_s':age,'horizon_s':p['horizon_s'],
                'model':'independent MuJoCo belt/block contact forecast; not full-cell or calibrated suction physics'}
        for policy,advance in (('HOLD',0.0),('CONTINUE',self.period)):
            worst=math.inf
            for offset,dv,reaction in axes:
                if self.clock()-start>p['wall_budget_s']: return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
                speed=max(0.0,estimate.velocity_m_s+dv); running=self._model(speed)
                data=self.mj.MjData(running)
                data.qpos[1]=estimate.y_m+offset*uncertainty+speed*age
                data.qvel[1]=speed
                self.mj.mj_forward(running,data)
                def margin():
                    zlo,zhi=self.config['geometry']['hold_z_m']
                    width=self.config.get('mechanics',{}).get('long_belt_width_m',.078)
                    lateral=width/2-self.config['geometry']['product_size_m'][0]/2-abs(float(data.qpos[0]))
                    return min(self.limit-float(data.qpos[1]),lateral,float(data.qpos[2])-zlo,zhi-float(data.qpos[2]))
                cutoff=advance+reaction; minimum=margin(); stopped=False
                for i in range(math.ceil(p['horizon_s']/self.dt)):
                    if self.clock()-start>p['wall_budget_s']: return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
                    model=running
                    if i*self.dt>=cutoff:
                        if not stopped:
                            other=self.mj.MjData(self.stopped)
                            other.qpos[:]=data.qpos; other.qvel[:]=data.qvel; other.time=data.time
                            self.mj.mj_forward(self.stopped,other); data=other; stopped=True
                        model=self.stopped
                    self.mj.mj_step(model,data); steps+=1
                    if not all(math.isfinite(float(v)) for v in data.qpos): raise ValueError('non-finite forecast state')
                    minimum=min(minimum,margin())
                worst=min(worst,minimum); completed+=1
            margins[policy]=worst
        action='CONTINUE' if margins['CONTINUE']>=0 else 'HOLD'
        reason='predictive_continue' if action=='CONTINUE' else 'predictive_stop_margin' if margins['HOLD']>=0 else 'predictive_no_admissible_continue'
        if self.clock()-start>p['wall_budget_s']: return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
        return result('complete',action,reason)
