import unittest
from pathlib import Path
from config import load_config
from sequence import Sequence
from health import SignalHealth
from clock_checks import elapsed_at_least


class ClockBoundaryTest(unittest.TestCase):
    def test_inclusive_threshold_is_consistent_at_different_clock_origins(self):
        config=load_config(Path(__file__).parent/'configs/reconfigurable_cell_20261030.json')
        timeout=config['timing']['silence_timeout_s']
        for start in (0.,.5,1.,5.,10.,20.):
            with self.subTest(start=start):
                ctl=Sequence(config=config);ctl.phase='TRACK';ctl.last_received=start;ctl.command['long']=.16;ctl.command['vacuum']=True
                health=SignalHealth(config);health.last_received=start
                now=start+timeout;ctl.watchdog(now)
                finding=health.update(None,now,{},ctl.estimator.estimate)
                self.assertEqual(ctl.phase,'HOLD');self.assertEqual(ctl.reason,'telemetry_timeout')
                self.assertTrue(ctl.command['vacuum']);self.assertEqual(ctl.command['long'],0.)
                self.assertIn('telemetry_silence',{f['code'] for f in finding['findings']})

    def test_a_microsecond_before_threshold_is_not_expired(self):
        for start in (0.,.5,1.,5.,10.,20.):
            self.assertFalse(elapsed_at_least(start+.1-1e-6,start,.1))

    def test_roundoff_tolerance_is_absolute_not_relative_to_large_times(self):
        self.assertTrue(elapsed_at_least(5.1,5.,.1))
        self.assertFalse(elapsed_at_least(1000.099999,1000.,.1))


if __name__=='__main__':unittest.main()
