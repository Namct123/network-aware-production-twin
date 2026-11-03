"""Independent MuJoCo belt/block forecasts from estimates, never a live Cell state."""
from itertools import product
import math
import time

class ReferenceMuJoCoBeltPredictor:
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


class MuJoCoBeltPredictor(ReferenceMuJoCoBeltPredictor):
    """Same models and stop transitions; grouped native loops, bounded optional workers."""
    def __init__(self,config,clock=None):
        super().__init__(config,clock)
        import numpy as np
        from mujoco.rollout import Rollout
        self.np=np
        self.thread_count=config['prediction'].get('native_threads',1)
        if type(self.thread_count) is not int or not 1<=self.thread_count<=16: raise ValueError('native_threads must be an integer in 1..16')
        self.engine=Rollout(nthread=0 if self.thread_count==1 else self.thread_count)
        self.scratch=self.mj.MjData(self.stopped) if self.thread_count==1 else [self.mj.MjData(self.stopped) for _ in range(self.thread_count)]

    def _batch(self,models,initial,nstep):
        states,_=self.engine.rollout(models,self.scratch,initial,nstep=nstep)
        # rollout repeats states on divergence. Finite coordinates alone cannot detect it.
        times=self.np.concatenate((initial[:,None,0],states[:,:,0]),axis=1)
        if not self.np.isfinite(states).all() or not (self.np.diff(times,axis=1)>0).all():
            raise ValueError('non-finite or diverged native forecast')
        return states

    def _margins(self,states):
        np=self.np; g=self.config['geometry']; zlo,zhi=g['hold_z_m']
        width=self.config.get('mechanics',{}).get('long_belt_width_m',.078)
        # FULLPHYSICS is time, qpos, qvel (no activation state in this model).
        x,y,z=states[...,1],states[...,2],states[...,3]
        return np.minimum.reduce((self.limit-y,width/2-g['product_size_m'][0]/2-np.abs(x),z-zlo,zhi-z))

    def rollout(self,estimate,source_time_s,now_s):
        vals=(estimate.y_m,estimate.velocity_m_s,estimate.uncertainty_m,source_time_s,now_s)
        if any(v is None or type(v) not in (float,int) or not math.isfinite(v) for v in vals): raise ValueError('finite estimated state required')
        if now_s<source_time_s or estimate.velocity_m_s<0 or estimate.uncertainty_m<0: raise ValueError('invalid estimated state/time')
        start=self.clock(); p=self.parameters; age=now_s-source_time_s; np=self.np
        axes=list(product(p['position_offsets'],p['speed_offsets_m_s'],p['reaction_delays_s']))
        expected=2*len(axes); completed=steps=0
        worst={'HOLD':math.inf,'CONTINUE':math.inf}; counts={'HOLD':0,'CONTINUE':0}
        def expired():return self.clock()-start>p['wall_budget_s']
        def result(status,action,reason):
            elapsed=self.clock()-start
            if elapsed>p['wall_budget_s']:
                status,action,reason='deadline_exceeded','HOLD','prediction_deadline_exceeded'
            return {'status':status,'action':action,'reason':reason,'completed_scenarios':completed,
                'expected_scenarios':expected,'rollout_steps':steps,'compute_ms':elapsed*1000,
                'margins_m':{k:v for k,v in worst.items() if counts[k]==len(axes)},
                'estimate_age_s':age,'horizon_s':p['horizon_s'],
                'native_threads':self.thread_count,
                'model':'independent MuJoCo belt/block contact forecast; native grouped rollout; not full-cell or calibrated suction physics'}
        if expired():return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
        uncertainty=estimate.uncertainty_m+self.config['estimator']['drift_m_s']*age
        nstep=math.ceil(p['horizon_s']/self.dt); groups={}
        for policy,advance in (('HOLD',0.0),('CONTINUE',self.period)):
            for offset,dv,reaction in axes:
                speed=max(0.0,estimate.velocity_m_s+dv)
                model=self._model(speed)
                initial=np.concatenate(([0.0],model.qpos0,np.zeros(model.nv)))
                initial[2]=estimate.y_m+offset*uncertainty+speed*age
                initial[9]=speed  # time + 7 qpos + y velocity.
                # Match the reference multiplication/comparison, including floating-point cutoffs.
                stop=next((i for i in range(nstep) if i*self.dt>=advance+reaction),nstep)
                groups.setdefault(stop,[]).append((policy,model,initial))
                if expired():return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
        for stop,tasks in sorted(groups.items()):
            if expired():return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
            initial=np.stack([t[2] for t in tasks]); minimum=self._margins(initial)
            if stop:
                prefix=self._batch([t[1] for t in tasks],initial,stop); steps+=len(tasks)*stop
                minimum=np.minimum(minimum,self._margins(prefix).min(axis=1)); initial=prefix[:,-1,:].copy()
                if expired():return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
            if stop<nstep:
                # Native rollout resets warmstart by default, just as the reference creates a
                # new stopped MjData and copies only time/qpos/qvel at this transition.
                tail=self._batch(self.stopped,initial,nstep-stop);steps+=len(tasks)*(nstep-stop)
                minimum=np.minimum(minimum,self._margins(tail).min(axis=1))
            for task,margin in zip(tasks,minimum):
                policy=task[0];worst[policy]=min(worst[policy],float(margin));counts[policy]+=1
            completed+=len(tasks)
            # A native call cannot be preempted here; an observed overrun always returns HOLD.
            if expired():return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
        action='CONTINUE' if worst['CONTINUE']>=0 else 'HOLD'
        reason='predictive_continue' if action=='CONTINUE' else 'predictive_stop_margin' if worst['HOLD']>=0 else 'predictive_no_admissible_continue'
        if expired():return result('deadline_exceeded','HOLD','prediction_deadline_exceeded')
        return result('complete',action,reason)
