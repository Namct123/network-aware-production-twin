import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from check_software import inventory

ROOT=Path(__file__).resolve().parents[1]


class SoftwareReleaseTest(unittest.TestCase):
    def test_all_six_items_exist_before_checks(self):
        result=inventory()
        self.assertEqual(len(result['items']),6);self.assertTrue(result['files_sha256'])
        self.assertEqual(result['user_acceptance'],'pending')

    def test_dashboard_reads_diagnostics_and_prefers_new_manifest(self):
        spec=importlib.util.spec_from_file_location('project_status_v2',ROOT/'web/project_status.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'mujoco').mkdir();folder=root/'output/docker/stream_run';folder.mkdir(parents=True)
            (root/'mujoco/software_release_v2.json').write_text(json.dumps({'items':[{'id':'S01'}]}))
            (folder/'summary.json').write_text(json.dumps({'kind':'stream_input_v1','controller_state':'HOLD','datagrams':4,'invalid_datagrams':1,'hold_reason':'telemetry_timeout'}))
            state=module.ProjectStatus(root).read()
            self.assertEqual(state['implementation']['items'][0]['id'],'S01')
            self.assertEqual(state['diagnostics'][0]['kind'],'stream_input_v1')
            self.assertFalse(state['physical_connection'])
        d=module.diagnostic({'kind':'model_boundary_v1','complete':144,'planned':144,'forward_decision_pairs':{'agree':138}},'boundary')
        self.assertIsNone(d['passed']);self.assertIn('144',d['summary_vi'])


if __name__=='__main__':unittest.main()
