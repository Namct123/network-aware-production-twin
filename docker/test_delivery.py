"""Delivery boundaries: no private build inputs and no GUI in headless image."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from build_image import ROOT, context_files

class DeliveryTest(unittest.TestCase):
    def test_context_has_core_without_private_or_generated_files(self):
        names = {p.relative_to(ROOT).as_posix() for p in context_files()}
        self.assertIn('cad_reference/production_twin_v0_parts.csv',names)
        self.assertFalse(any('unity' in Path(n).parts for n in names))
        self.assertTrue({'mujoco/experiment.py','mujoco/predictor.py',
                         'mujoco/production_cell.xml','scripts/portable_bundle/launch.py'} <= names)
        forbidden = {'.git','.venv','__pycache__','output','tmp','paper','rendered'}
        self.assertFalse(any(forbidden.intersection(Path(n).parts) for n in names))
        self.assertFalse(any(Path(n).suffix in {'.pdf','.docx','.env','.pyc'} for n in names))

    def test_focused_context_keeps_method_and_testbed_without_full_controller(self):
        names={p.relative_to(ROOT).as_posix() for p in context_files('monitoring')}
        self.assertTrue({'mujoco/event_window.py','mujoco/study_eta_monitor.py','mujoco/parametric_cell.py'}<=names)
        self.assertFalse(any(n.startswith(('web/','fusion/','scenes/')) for n in names))
        self.assertNotIn('mujoco/runtime.py',names);self.assertNotIn('mujoco/reconfiguration.py',names)
        self.assertLess(len(names),len(context_files()))

    def test_headless_rejects_view_before_starting_a_simulation(self):
        result = subprocess.run([sys.executable,str(ROOT/'scripts/portable_bundle/launch.py'),'demo','--view'],
                                env={**os.environ,'DT_CONTAINER_HEADLESS':'1'},capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('headless',result.stderr)

if __name__ == '__main__':
    unittest.main()
