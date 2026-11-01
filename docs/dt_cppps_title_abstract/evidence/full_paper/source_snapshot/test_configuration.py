"""Configuration/calibration/transport checks; standard library only."""

import csv
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from calibrate import FIELDS, import_measurements
from config import load_config, resolved_config, validate_config
from estimator import Estimate
from evaluation import Evaluator
from model_profile import model_xml
from network import Network
from sensor_model import SensorModel
from sequence import Sequence
from signals import SignalFrame


def frame(i):
    return SignalFrame(i,i*.02,i*.02,{"ps1":i%2==0},{"ps1":"good"})


class ConfigurationTest(unittest.TestCase):
    def test_unknown_missing_nonfinite_and_bool_are_rejected(self):
        for action in (lambda c:c["motion"].update(typo=1),
                       lambda c:c["timing"].update(physics_step_s=float("nan")),
                       lambda c:c["plant"].update(product_mass_kg=True),
                       lambda c:c["timing"].update(sample_steps=2.5),
                       lambda c:c["network"].update(drop_probability=1.01)):
            c=load_config(); action(c)
            with self.assertRaises(ValueError): validate_config(c)

    def test_infeasible_geometry_and_inertia_are_rejected(self):
        for action in (lambda c:c["geometry"]["ps_y_m"].update(ps1=.20),
                       lambda c:c["geometry"]["bin_centers_xy_m"].__setitem__(0,[10,.075]),
                       lambda c:c["sensors"].update(end_switch_tolerance_m=.08),
                       lambda c:c["motion"].update(a2_pick_m=.1),
                       lambda c:c["plant"]["link_inertials"]["cup_link"].update(diagonal_kg_m2=[1,1,9])):
            c=load_config(); action(c)
            with self.assertRaises(ValueError): validate_config(c)

    def test_profile_reaches_geometry_controller_and_sensors(self):
        c=load_config()
        c["geometry"]["ps_y_m"]["ps2"] = .165
        c["geometry"]["bin_centers_xy_m"][0][0] = .085
        c["sensors"]["end_switch_tolerance_m"] = .001
        c["plant"]["product_mass_kg"] = .023
        tree=ET.fromstring(model_xml(c))
        self.assertAlmostEqual(float(tree.find(".//site[@name='ps2_beam']").get("pos").split()[1]),.165)
        self.assertAlmostEqual(float(tree.find(".//geom[@name='bin_r1c1_floor']").get("pos").split()[0]),.085)
        self.assertAlmostEqual(float(tree.find(".//geom[@name='product_box']").get("mass")),.023)
        seq=Sequence(config=c)
        self.assertAlmostEqual(seq.bin_target[0],.265)
        self.assertEqual(seq.estimator.positions["ps2"],.165)
        f,_=SensorModel(config=c).sample(dict(time_s=0,ps1=False,ps2=False,a1_m=.1085,a2_m=0))
        self.assertFalse(f.values["a1_extended"])

    def test_resolved_speed_override_does_not_mutate_base(self):
        c=load_config(); resolved=resolved_config(c,.10)
        self.assertEqual(c["motion"]["long_speed_m_s"],.16)
        self.assertEqual(resolved["motion"]["long_speed_m_s"],.10)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"; p.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaisesRegex(ValueError,"duplicate"): load_config(p)

    def test_calibration_imports_si_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path,out=Path(d)/"measure.csv",Path(d)/"partial.json"
            row=dict(zip(FIELDS,["geometry.ps_y_m.ps2","0.165","m","0.001","2026-10-27",
                                 "unit-test synthetic ruler","unit-test","not a real measurement"]))
            with csv_path.open("w",newline="",encoding="utf-8") as stream:
                writer=csv.DictWriter(stream,fieldnames=FIELDS); writer.writeheader(); writer.writerow(row)
            result=import_measurements(load_config(),csv_path,out,"test_only_partial")
            self.assertEqual(result["geometry"]["ps_y_m"]["ps2"],.165)
            self.assertEqual(result["profile"]["status"],"partial")
            self.assertEqual(result["profile"]["measurements"][0]["uncertainty"],.001)
            self.assertEqual(load_config()["geometry"]["ps_y_m"]["ps2"],.170)
            with self.assertRaises(FileExistsError): import_measurements(load_config(),csv_path,out)

    def test_wrong_units_and_empty_csv_cannot_certify_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path,out=Path(d)/"measure.csv",Path(d)/"partial.json"
            for value,unit in (("165","mm"),("","m"),("NaN","m")):
                with csv_path.open("w",newline="",encoding="utf-8") as stream:
                    writer=csv.writer(stream); writer.writerow(FIELDS)
                    writer.writerow(["geometry.ps_y_m.ps2",value,unit,"","2026-10-27","test","test",""])
                with self.assertRaises(ValueError): import_measurements(load_config(),csv_path,out)
                self.assertFalse(out.exists())

    def test_zero_delay_and_total_loss(self):
        c=load_config()["network"]
        net=Network(c); f=frame(0); net.send(f,0)
        self.assertEqual(net.receive(0),f)
        self.assertIsNone(net.receive(0))
        c["drop_probability"]=1
        net=Network(c); net.send(f,0)
        self.assertIsNone(net.receive(1))
        self.assertEqual(net.stats["dropped"],1)

    def test_delay_age_jitter_seed_and_reordering(self):
        c=load_config()["network"]; c["delay_s"]=.04
        net=Network(c); net.send(frame(0),0)
        self.assertIsNone(net.receive(.02))
        received=net.receive(.04)
        self.assertEqual(received.source_time_s,0)
        self.assertEqual(received.received_time_s,.04)
        self.assertEqual(received.aged(.04,.02).quality["ps1"],"stale")
        c.update(delay_s=.06,jitter_s=.06,seed=42)
        histories=[]
        for _ in range(2):
            n=Network(c); seen=[]
            for i in range(40):
                n.send(frame(i),i*.02)
                f=n.receive(i*.02)
                if f is not None: seen.append(f.sequence)
            self.assertEqual(seen,sorted(set(seen)))
            histories.append((seen,n.stats))
        self.assertEqual(histories[0],histories[1])
        self.assertGreater(histories[0][1]["out_of_order_ignored"],0)

    def test_watchdog_and_evaluator_support_front_belt(self):
        c=load_config(); controller=Sequence(config=c)
        controller.watchdog(.10)
        self.assertEqual(controller.reason,"telemetry_timeout")
        score=Evaluator(c["geometry"]).finish({"product_xyz_m":[.20,-.325,.060]},"HOLD",1)
        self.assertTrue(score["hold_product_supported_evaluator_only"])

    def test_evaluator_tracks_configured_bins_and_error(self):
        c=load_config(); c["geometry"]["bin_centers_xy_m"][0][0]=.085
        ev=Evaluator(c["geometry"])
        ev.observe(Estimate(y_m=.162,reason="tracking"),{"product_xyz_m":[0,.160,0]},"TRACK")
        score=ev.finish({"product_xyz_m":[.085,.075,.027]},"DONE",1)
        self.assertTrue(score["placement_pass_evaluator_only"])
        self.assertAlmostEqual(score["y_error_rmse_m"],.002)


if __name__ == "__main__":
    unittest.main()
