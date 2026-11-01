"""Boundary checks for the shared core, without requiring a physical machine."""
from dataclasses import replace
import json
from pathlib import Path
import unittest
import importlib.util
import tempfile
from config import load_config
from signals import SignalFrame
from session import Envelope,MessageGuard,CommandGate
from io_adapter import load_adapter
from runtime import RuntimeCore

HERE=Path(__file__).resolve().parent

class IntegratedCoreTest(unittest.TestCase):
    def config(self): return load_config(HERE/'configs/reconfigurable_cell_20261030.json')
    def frame(self): return SignalFrame(0,0,0,{'ps1':False},{'ps1':'good'})

    def test_session_generation_order_and_body(self):
        packet=Envelope.signal(self.frame(),'current',1)
        gate=MessageGuard('current',1)
        for bad in (replace(packet,session_id='old'),replace(packet,generation=0),
                    replace(packet,payload={**packet.payload,'sequence':4})):
            self.assertFalse(gate.accept(bad,0,'signal')['accepted'])
        self.assertTrue(gate.accept(packet,0,'signal')['accepted'])
        self.assertFalse(gate.accept(packet,0,'signal')['accepted'])
        self.assertEqual(gate.accepted,1)

    def test_unconfirmed_mapping_never_invents_false(self):
        adapter=load_adapter(HERE/'configs/recording_map_unverified.json')
        row={'session_id':'recording','generation':0,'sequence':0,'source_time':0,
             'received_time_s':0,'values':{'PS2_upstream':True},'quality':{'PS2_upstream':'good'}}
        message,notes=adapter.convert(row)
        self.assertTrue(notes)
        self.assertTrue(all(v is None for v in message.frame().values.values()))

    def test_invalid_command_stops_and_keeps_last_vacuum(self):
        core=RuntimeCore(self.config())
        core.gate.validate({'front':0,'long':0,'targets':{},'vacuum':True,'hold':False})
        core.controller.command['long']=float('nan')
        core.stop('invalid_command',0)
        command=core.gate.validate(core.controller.command)
        self.assertTrue(command['hold']); self.assertTrue(command['vacuum'])
        self.assertEqual(command['long'],0)
        with self.assertRaises(ValueError): core.step(None,float('nan'))

    def test_old_generation_cannot_drive_new_core(self):
        core=RuntimeCore(self.config(),session_context={'session_id':'same','generation':1})
        result=core.step(Envelope.signal(self.frame(),'same',0),0)
        self.assertFalse(result['input_guard']['accepted'])
        self.assertIsNone(result['frame'])
        self.assertEqual(result['command_message']['generation'],1)

    def test_dashboard_reads_saved_results_without_physical_connection(self):
        spec=importlib.util.spec_from_file_location('project_status',HERE.parent/'web/project_status.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'output/docker/example').mkdir(parents=True)
            (root/'output/docker/example/summary.json').write_text(json.dumps({'controller_state':'HOLD'}))
            result=module.ProjectStatus(root).read()
            self.assertFalse(result['physical_connection'])
            self.assertEqual(result['runs'][0]['state'],'HOLD')

if __name__=='__main__': unittest.main()
