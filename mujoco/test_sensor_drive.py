from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from study_sensor_drive import should_start,inject_signal,applied_command,load_plan


class SensorDriveTest(unittest.TestCase):
    def test_trigger_uses_phase_and_optical_edge_not_pose(self):
        self.assertTrue(should_start('feed_drive_stall','FEED',None,False,0))
        self.assertTrue(should_start('pickup_sensor_missing','TRACK',True,False,1))
        self.assertFalse(should_start('pickup_sensor_missing','TRACK',True,False,0))
        self.assertFalse(should_start('nominal','TRACK',True,False,1))
        plan=load_plan(Path(__file__).parent/'experiments/sensor_drive_20261104.json')
        self.assertEqual(len(plan['cases']),7)

    def test_plant_override_does_not_mutate_issued_command(self):
        command={'front':.16,'long':.16,'targets':{'x_joint':.1},'hold':False,'vacuum':True}
        saved=deepcopy(command)
        result=applied_command(command,'long_drive_stall',True)
        self.assertEqual(result['long'],0.);self.assertEqual(command,saved)
        result['targets']['x_joint']=0.
        self.assertEqual(command,saved)
        self.assertEqual(applied_command(command,'long_drive_stall',False),saved)


if __name__=='__main__':unittest.main()
