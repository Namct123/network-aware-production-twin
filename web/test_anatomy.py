"""Provenance and observation-boundary checks for the offline Anatomy view."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class AnatomyTests(unittest.TestCase):
    def test_embedded_data_and_clock_alignment(self):
        data=json.loads((ROOT/"anatomy_data.json").read_text(encoding="utf-8"))
        html=(ROOT/"anatomy.html").read_text(encoding="utf-8")
        embedded=html.split('<script id="anatomy-data" type="application/json">',1)[1].split('</script>',1)[0]
        self.assertEqual(data,json.loads(embedded))
        self.assertEqual(len(data["trials"]),7)
        self.assertEqual(sum(len(t["frames"]) for t in data["trials"]),1973)
        self.assertEqual(len(data["source_hashes"]),30)
        for trial in data["trials"]:
            times=[f["t"] for f in trial["frames"]]
            self.assertTrue(all(b>a for a,b in zip(times,times[1:])))
            self.assertEqual(trial["frames"][-1]["phase"],"HOLD")
            for f in trial["frames"]:
                self.assertIsNone(f["o"]["belt_speed_front_m_s"])
                self.assertIsNone(f["o"]["belt_speed_long_m_s"])
                self.assertNotIn("product_xyz_m",f["o"])
                self.assertEqual(f["policy"]["observation_age_s"],0)

    def test_two_ambiguous_pairs_really_share_observations(self):
        data=json.loads((ROOT/"anatomy_data.json").read_text(encoding="utf-8"))
        trials={t["id"]:t for t in data["trials"]}
        for a,b in [("feed_sensor_missing","feed_drive_stall"),("pickup_sensor_missing","long_drive_stall")]:
            left,right=trials[a],trials[b]
            hold=next(i for i,f in enumerate(left["frames"]) if f["phase"]=="HOLD")
            for x,y in zip(left["frames"][:hold+1],right["frames"][:hold+1]):
                self.assertEqual(x["t"],y["t"])
                self.assertEqual(x["o"],y["o"])
                self.assertEqual(x["command"],y["command"])
                self.assertEqual(x["phase"],y["phase"])
            self.assertNotEqual(left["frames"][hold]["p"],right["frames"][hold]["p"])

if __name__=="__main__": unittest.main()
