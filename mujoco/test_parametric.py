"""Measured-envelope configuration, propagation, admission guard and editable measurements."""
import csv
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from calibrate import FIELDS, export_template, import_measurements, parameter_report, parameter_units
from config import load_config, validate_config
from model_profile import model_xml
from sensor_model import SensorModel
from sequence import Sequence

PROFILE=Path(__file__).parent/'configs/measured_cell_20261030.json'

def sample(sensor,t,transfer=False):
    return sensor.sample(dict(time_s=t,ps1=False,ps2=False,transfer_present=transfer,a1_m=0,a2_m=0))[0]

class ParametricTest(unittest.TestCase):
    def test_dimensions_reach_mjcf_and_preserve_three_roles(self):
        c=load_config(PROFILE); xml=ET.fromstring(model_xml(c))
        self.assertEqual(xml.find(".//geom[@name='product_box']").get('size'),'0.03 0.03 0.03')
        belt=xml.find(".//geom[@name='long_green_belt']")
        self.assertEqual(belt.get('size'),'0.04 0.265 0.002')
        self.assertAlmostEqual(float(belt.get('pos').split()[2])+.002,.1)
        self.assertEqual(len(xml.findall('sensor/rangefinder')),3)
        pusher=xml.find(".//body[@name='pusher_link']")
        self.assertIsNotNone(pusher.find("site[@name='transfer_present_beam']"))
        self.assertEqual(c['mechanics']['sensor_roles']['ps1'],'PS2_upstream')
        self.assertEqual(len(xml.findall(".//geom[@type='sphere']")),4)
        self.assertIsNone(xml.find('equality'))  # No perfect grasp weld.

    def test_height_change_propagates_without_source_constants(self):
        c=load_config(PROFILE); c['mechanics']['belt_surface_z_m']+=.01
        c['mechanics']['cup_retracted_z_m']+=.01
        c['geometry']['product_initial_xyz_m'][2]+=.01
        c['geometry']['optical_xz_m'][1]+=.01
        c['mechanics']['pusher_rest_xyz_m'][2]+=.01
        xml=ET.fromstring(model_xml(c))
        self.assertAlmostEqual(float(xml.find(".//geom[@name='long_green_belt']").get('pos').split()[2]),.108)
        self.assertAlmostEqual(float(xml.find(".//site[@name='ps1_beam']").get('pos').split()[2]),.14)

    def test_inconsistent_coupled_dimensions_are_rejected(self):
        base=load_config(PROFILE)
        for mutate in (lambda c:c['mechanics'].update(cup_retracted_z_m=.25),
                       lambda c:c['mechanics'].update(cup_patch_radius_m=.03),
                       lambda c:c['mechanics']['sensor_roles'].update(ps2='PS2_upstream'),
                       lambda c:c['geometry'].update(product_size_m=[.1,.06,.06])):
            c=deepcopy(base); mutate(c)
            with self.assertRaises(ValueError): validate_config(c)

    def test_missing_admission_stops_before_configured_front_limit(self):
        c=load_config(PROFILE); sensor=SensorModel(config=c); seq=Sequence(config=c,assume_open_loop=True)
        for i in range(120):
            seq.tick(sample(sensor,i*.02),i*.02)
            if seq.phase=='HOLD': break
        self.assertEqual(seq.reason,'timeout:FEED:transfer_present')
        self.assertLess(seq.entered,c['mechanics']['admission_timeout_s'])
        self.assertEqual(seq.command['front'],0)

    def test_admission_sensor_is_observation_not_ground_truth(self):
        c=load_config(PROFILE); sensor=SensorModel(config=c); seq=Sequence(config=c)
        f=sample(sensor,0,True); seq.tick(f,0)
        self.assertEqual(seq.phase,'HOLD')
        self.assertNotIn('product_xyz_m',f.values)

    def test_template_import_supports_new_fields_and_integer_settings(self):
        c=load_config(PROFILE)
        with tempfile.TemporaryDirectory() as folder:
            csv_path=Path(folder)/'measure.csv'; out=Path(folder)/'new.json'
            rows=export_template(c,csv_path)
            self.assertEqual(len(rows),len(parameter_units(c)))
            with csv_path.open(newline='',encoding='utf-8') as stream: values=list(csv.DictReader(stream))
            self.assertTrue(all(row['value']=='' for row in values))
            for row in values:
                if row['path'] in {'plant.product_mass_kg','mechanics.front_stop_coast_m','network.seed'}:
                    row.update(value={'plant.product_mass_kg':'.03','mechanics.front_stop_coast_m':'.003','network.seed':'9'}[row['path']],
                               measured_on='2026-10-30',method='synthetic unit test, not physical measurement')
            with csv_path.open('w',newline='',encoding='utf-8') as stream:
                w=csv.DictWriter(stream,fieldnames=FIELDS); w.writeheader(); w.writerows(values)
            changed=import_measurements(c,csv_path,out)
            self.assertEqual(changed['mechanics']['front_stop_coast_m'],.003)
            self.assertIs(type(changed['network']['seed']),int)
            self.assertEqual(c['plant']['product_mass_kg'],.02)

    def test_changed_record_is_not_silently_called_measured(self):
        c=load_config(PROFILE); c['mechanics']['long_belt_width_m']=.09
        rows={r['path']:r for r in parameter_report(c)}
        self.assertEqual(rows['mechanics.long_belt_width_m']['status'],'changed_since_measurement')
        self.assertFalse(rows['motion.feed_distance_m']['active_in_this_model'])

if __name__=='__main__':
    unittest.main()
