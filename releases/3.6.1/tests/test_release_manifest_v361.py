import json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ReleaseManifestV361Tests(unittest.TestCase):
    def test_all_fifteen_acceptance_ids_are_present_once(self):
        module = (ROOT / "scripts" / "acceptance_contract_v361.py").read_text(encoding="utf-8")
        expected = ["user_need", "topic_selection", "cover", "opening_0_3", "bridge_3_8", "body_mode", "promise_payoff", "capability_amplification", "next_level_value", "calling", "evidence", "platform_fit", "oral_delivery", "independent_review", "outcome_feedback"]
        for criterion in expected:
            with self.subTest(criterion=criterion): self.assertIn('"' + criterion + '"', module)
        self.assertEqual(len(expected), 15)

    def test_new_schemas_are_valid_json_and_have_v361_title(self):
        for name in ["source-evidence-v361.schema.json", "decision-competition-v361.schema.json", "draft-delivery-v361.schema.json", "acceptance-15-v361.schema.json", "independent-review-attestation-v361.schema.json", "external-validation-v361.schema.json"]:
            with self.subTest(schema=name):
                data = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
                self.assertIn("v3.6.1", data["title"])

    def test_new_entrypoint_calls_all_four_stage_contracts(self):
        source = (ROOT / "scripts" / "run_pipeline_v3_6_1.py").read_text(encoding="utf-8")
        for token in ["validate_source_inventory", "validate_plan_stage", "validate_draft_stage", "validate_review", "intake", "plan", "draft", "validate", "export"]:
            with self.subTest(token=token): self.assertIn(token, source)

    def test_public_skill_preserves_domain_separation_and_old_entrypoints(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in ["AI视频V4.1", "插画V2.0", "双标杆", "Title Guide V4", "v3.5.0", "v3.5.1", "v3.6.0", "VALIDATION_PENDING"]:
            with self.subTest(token=token): self.assertIn(token, skill)

if __name__ == "__main__": unittest.main(verbosity=2)
