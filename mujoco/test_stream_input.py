"""The streaming boundary cannot trust sender reception times or clear HOLD."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from config import load_config
from io_adapter import load_adapter
from stream_input import StreamCore,MAX_DATAGRAM

HERE=Path(__file__).resolve().parent


class StreamInputTest(unittest.TestCase):
    def setUp(self):
        config=load_config(HERE/'configs/reconfigurable_cell_20261030.json')
        self.core=StreamCore(config,load_adapter(HERE/'configs/recording_map_example.json').settings,'test')
        self.addCleanup(self.core.close)
        self.values={'PS1_pusher':False,'PS2_upstream':False,'PS3_pickup':False,'A1_back':True,'A1_front':False,'A2_up':True,'A2_down':False}

    def row(self,seq=0,source=0):
        return {'session_id':'test','generation':0,'sequence':seq,'source_time':source*1000,
            'values':self.values,'quality':{k:'good' for k in self.values}}

    def send(self,row,now):return self.core.tick(json.dumps(row).encode(),now)

    def test_reception_time_is_local_and_sender_cannot_override(self):
        result=self.send(self.row(),.02)
        self.assertTrue(result['input_guard']['accepted']);self.assertEqual(self.core.core.controller.last_received,.02)
        row=self.row(1,.02);row['received_time_s']=.021
        self.assertIsNotNone(self.send(row,.04)['input_error'])
        self.assertEqual(self.core.invalid,1)

    def test_silence_and_return_do_not_restart(self):
        self.send(self.row(),0)
        result=self.core.tick(None,.4)
        self.assertEqual(result['hold_reason'],'telemetry_timeout')
        result=self.send(self.row(1,.42),.42)
        self.assertEqual(result['phase'],'HOLD');self.assertEqual(result['hold_reason'],'telemetry_timeout')

    def test_session_ordering_and_bad_packets_remain_separate(self):
        self.send(self.row(),0)
        repeated=self.send(self.row(),.01)
        self.assertEqual(repeated['input_guard']['reason'],'old_or_repeated_message')
        wrong=self.row(1,.02);wrong['session_id']='old'
        self.assertEqual(self.send(wrong,.02)['input_guard']['reason'],'wrong_session')
        for index,packet in enumerate([b'not-json',b'\xff',b'{}'+b' '*(MAX_DATAGRAM+1),b'{"source_time":NaN}']):
            self.assertIsNotNone(self.core.tick(packet,.03+index*.01)['input_error'])
        self.assertEqual(self.core.invalid,4)

    def test_unconfirmed_mapping_is_unavailable_not_false(self):
        other=StreamCore(self.core.core.config,load_adapter(HERE/'configs/recording_map_unverified.json').settings,'test')
        try:
            result=other.tick(json.dumps(self.row()).encode(),0)
            self.assertEqual(result['phase'],'HOLD');self.assertTrue(result['hold_reason'].startswith('invalid_or_stale:'))
        finally:other.close()

    def test_finish_stops_locally_and_preserves_vacuum(self):
        self.send(self.row(),0)
        self.core.core.controller.command['vacuum']=True
        self.core.core.gate.last['vacuum']=True
        final=self.core.finish(.01)
        command=final['command_message']['payload']
        self.assertTrue(command['hold']);self.assertTrue(command['vacuum'])
        self.assertEqual(command['front'],0);self.assertFalse(final['physical_output'])
        self.assertIsNone(self.core.finish(.02))
        with self.assertRaises(RuntimeError):self.core.tick(None,.02)


if __name__=='__main__':unittest.main()
