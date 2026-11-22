import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/"references/ai-video-sample-index.jsonl"
class SampleGovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(x) for x in INDEX.read_text(encoding="utf-8").splitlines() if x.strip()]
        cls.by={x["asset_id"]:x for x in cls.rows}
    def test_ids_unique(self):
        self.assertEqual(len(self.rows),len(self.by))
    def test_all_indexed_paths_exist(self):
        for x in self.rows:
            self.assertTrue((ROOT/x["path"]).is_file(),x["asset_id"])
    def test_a01_is_benchmark_only(self):
        x=self.by["A01-V5.0"]
        self.assertEqual(x["status"],"benchmark_reference_only_not_performance_verified")
        self.assertFalse(x.get("few_shot_policy","").startswith("ACCEPTED"))
    def test_six_cases_are_candidates(self):
        x=self.by["SIX-CASES-V1.0"]
        self.assertEqual(x["status"],"candidate_not_performance_verified")
    def test_a01_s01_exclusion(self):
        x=self.by["S01-LIVE-DEMO"]
        self.assertIn("do_not_co_retrieve",x["retrieval_exclusion"])
    def test_six_case_ids_present(self):
        self.assertEqual({self.by[f"S0{i}-"+suffix]["case_id"] for i,suffix in [(2,"FORUM-EXPERT"),(3,"SERVICE-EXPLAINER"),(4,"FAQ-DIGITAL"),(5,"PRODUCT-SELECTION"),(6,"EXPERT-TRAINING")]},{f"S0{i}" for i in range(2,7)})
if __name__=="__main__": unittest.main(verbosity=2)
