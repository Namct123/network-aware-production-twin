"""Native-loop integrity tests; run with installed MuJoCo in WSL/container."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from config import load_config
from estimator import Estimate
from physics_predictor import MuJoCoBeltPredictor,ReferenceMuJoCoBeltPredictor

try:
    import mujoco
    HAS_ENGINE=hasattr(mujoco,'MjModel')
except ImportError:HAS_ENGINE=False

@unittest.skipUnless(HAS_ENGINE,'MuJoCo required; exercised in container')
class NativePhysicsTest(unittest.TestCase):
    def config(self):
        c=load_config(Path(__file__).parent/'configs/reconfigurable_cell_20261030.json')
        c['prediction']['wall_budget_s']=5.0
        return c

    def test_full_forecast_matches_reference_without_mutating_estimate(self):
        c=self.config();state=Estimate(0,.16,.003,2,'tracking');before=state.as_dict()
        a=ReferenceMuJoCoBeltPredictor(c).rollout(state,0,.02)
        b=MuJoCoBeltPredictor(c).rollout(state,0,.02)
        self.assertEqual(a['action'],b['action']);self.assertEqual(b['completed_scenarios'],54)
        self.assertEqual(a['rollout_steps'],b['rollout_steps']);self.assertEqual(state.as_dict(),before)
        for k in ('HOLD','CONTINUE'):self.assertAlmostEqual(a['margins_m'][k],b['margins_m'][k],places=9)

    def test_deadline_before_work_returns_hold(self):
        predictor=MuJoCoBeltPredictor(self.config())
        ticks=iter([0,6,6]);predictor.clock=lambda:next(ticks)
        result=predictor.rollout(Estimate(0,.1,.002),0,0)
        self.assertEqual(result['status'],'deadline_exceeded');self.assertEqual(result['action'],'HOLD')
        self.assertEqual(result['completed_scenarios'],0)

    def test_invalid_state_rejected(self):
        predictor=MuJoCoBeltPredictor(self.config())
        with self.assertRaises(ValueError):predictor.rollout(Estimate(0,float('nan'),.002),0,0)

    def test_nonincreasing_native_time_rejected(self):
        predictor=MuJoCoBeltPredictor(self.config())
        class Diverged:
            def rollout(self,*args,**kwargs):
                np=predictor.np
                return np.zeros((1,2,14)),None
        predictor.engine=Diverged()
        with self.assertRaises(ValueError):predictor._batch(predictor.stopped,predictor.np.zeros((1,14)),2)

    def test_native_trajectory_matches_individual_steps(self):
        predictor=MuJoCoBeltPredictor(self.config());mj=predictor.mj;np=predictor.np
        model=predictor._model(.16);data=mj.MjData(model);data.qpos[1]=0;data.qvel[1]=.16
        mj.mj_forward(model,data)
        initial=np.empty(14);mj.mj_getState(model,data,initial,mj.mjtState.mjSTATE_FULLPHYSICS)
        reference=[]
        for _ in range(30):
            mj.mj_step(model,data);state=np.empty(14);mj.mj_getState(model,data,state,mj.mjtState.mjSTATE_FULLPHYSICS);reference.append(state)
        native=predictor._batch(model,initial[None,:],30)[0]
        np.testing.assert_allclose(native,np.stack(reference),rtol=1e-12,atol=1e-12)

    def test_configured_workers_preserve_forecast_and_reject_bad_count(self):
        c=self.config();c['prediction']['native_threads']=4
        state=Estimate(.1,.16,.005,2,'tracking')
        a=ReferenceMuJoCoBeltPredictor(c).rollout(state,0,.02)
        b=MuJoCoBeltPredictor(c).rollout(state,0,.02)
        self.assertEqual(a['action'],b['action']);self.assertEqual(b['native_threads'],4)
        for k in ('HOLD','CONTINUE'):self.assertAlmostEqual(a['margins_m'][k],b['margins_m'][k],places=9)
        from calibrate import parameter_report
        record=next(r for r in parameter_report(c) if r['path']=='prediction.native_threads')
        self.assertEqual(record['unit'],'1');self.assertEqual(record['status'],'provisional_or_design')
        from config import validate_config
        for bad in (True,0,17):
            c['prediction']['native_threads']=bad
            with self.assertRaises(ValueError):validate_config(c)

if __name__=='__main__':unittest.main()
