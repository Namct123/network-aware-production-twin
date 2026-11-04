from copy import deepcopy
import unittest
from audit_response import timeline, compare_pair


def rows(session='A'):
    result=[]
    for i in range(5):
        result.append({'time_s':i*.02,'physical_output':False,'phase':'HOLD' if i>=3 else 'TRACK',
            'hold_reason':'telemetry_timeout' if i>=3 else '',
            'prediction':{'action':'CONTINUE','compute_ms':2.} if i==0 else None,
            'input_guard':{'accepted':True,'session_id':session} if i==0 else None,
            'command_message':{'session_id':session,'payload':{'long':.16 if i<2 else .12 if i==2 else 0.}}})
    result.append({'time_s':.1,'physical_output':False,'final':True,'command_message':{'payload':{'long':0.}}})
    return result


class ResponseAuditTest(unittest.TestCase):
    def test_times_are_from_fixture_epoch_not_program_start(self):
        r=timeline(rows(),1)
        self.assertAlmostEqual(r['speed_reduction_after_epoch_ms'],20.)
        self.assertAlmostEqual(r['hold_after_epoch_ms'],40.)
        self.assertIsNone(r['packet_rejection_after_epoch_ms'])
        x=rows(); x[1]['input_guard']={'accepted':False,'reason':'wrong_session'}
        self.assertEqual(timeline(x,1)['packet_rejection_after_epoch_ms'],0.)

    def test_invalid_clock_final_and_epoch_are_rejected(self):
        with self.assertRaises(ValueError):timeline(rows()[:-1],1)
        with self.assertRaises(ValueError):timeline(rows(),0)
        x=rows();x[2]['time_s']=x[1]['time_s']
        with self.assertRaises(ValueError):timeline(x,1)

    def test_pair_normalizes_session_and_duration_but_not_data(self):
        def record(name):
            x=rows(name);return {'name':name,'rows':x,'timing':timeline(x,1),'packets':{0.:{'sequence':0,'values':{'PS2':False}}}}
        a,b=record('A'),record('B');b['rows'][0]['prediction']['compute_ms']=99.
        r=compare_pair(a,b);self.assertTrue(r['input_trace_equal_through_hold']);self.assertTrue(r['logical_trace_equal_through_hold'])
        b['packets'][0.]['values']['PS2']=True
        self.assertFalse(compare_pair(a,b)['input_trace_equal_through_hold'])
        b['rows'][2]['command_message']['payload']['long']=.1
        self.assertFalse(compare_pair(a,b)['logical_trace_equal_through_hold'])


if __name__=='__main__':unittest.main()
