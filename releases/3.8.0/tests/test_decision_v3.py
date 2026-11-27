import copy
import unittest

from decision_v3 import GATES, actual_fields, validate_draft, validate_review, validate_topic
from v3_fixtures import populate, script_for


class DecisionV3Tests(unittest.TestCase):
    def setUp(self):
        self.source = {"asset_id": "SRC", "source_sha256": "1" * 64, "locator": "line 1", "read": True}
        self.brief = {"source_inventory": {"checked_assets": [self.source]}}
        self.topic = populate({"id": "01", "platform": "xiaohongshu", "audience": "Sample buyer",
                               "buyer_decision": "Can I approve the print sample?",
                               "payoff": "A way to check whether the print fits",
                               "next_step": "Compare at full scale",
                               "copy": {"cover_main": "Can you approve this nursery print?",
                                        "cover_sub": "Check scale against a cut line",
                                        "hook": "The proof on a phone hides the cut line.",
                                        "suspense": "Put the full-scale sample over the pattern template.",
                                        "body": "Check where the motif meets the cut line on two samples.",
                                        "calling": "Compare at full scale before you approve.",
                                        "comment": "Which edge of your pattern needs a check?"}}, self.source)
        self.d = self.topic["decision_v3"]
        self.script = script_for(self.topic)
        self.batch = {"scripts": [self.script]}
        self.selected = {"01": self.topic}
        fields = actual_fields(self.script, self.topic)
        self.review = {"batch_sha256": "sha", "reviewer_id": "reader",
                       "scripts": [{"plan_id": "01",
                                    "fields": [{"id": f, "quote": t, "status": "PASS", "reason": "Fixture"}
                                               for f, t in fields.items()],
                                    "gates": [{"id": g, "fields": list(f), "status": "PASS", "reason": "Fixture"}
                                              for g, f in GATES.items()]}]}

    def test_t01_duplicate_angles_are_rejected(self):
        alt = self.d["entries"][1]
        alt.update({k: v for k, v in self.d["entries"][0].items() if k != "id"})
        with self.assertRaisesRegex(ValueError, "ENTRIES_NOT_DISTINCT"):
            validate_topic(self.topic, self.brief)

    def test_t02_information_cannot_claim_comparison(self):
        self.d["claims"][0]["type"] = "comparison"
        with self.assertRaisesRegex(ValueError, "CLAIM_OVERREACH"):
            validate_topic(self.topic, self.brief)

    def test_t03_draft_body_without_the_promised_proof_fails(self):
        self.script["segments"][2]["text"] = "The service looks wonderful."
        with self.assertRaisesRegex(ValueError, "CLAIM_QUOTE_MISMATCH"):
            validate_draft(self.batch, self.selected)

    def test_t04_benefit_cannot_repeat_feature(self):
        self.d["value_map"]["feature"] = self.topic["payoff"]
        with self.assertRaisesRegex(ValueError, "BENEFIT_MAP_INVALID"):
            validate_topic(self.topic, self.brief)

    def test_t05_calling_or_comment_failure_is_noncompensable(self):
        self.review["scripts"][0]["fields"][-1]["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "NINE_FIELD_BLOCKED"):
            validate_review(self.batch, self.selected, self.review, "sha", "reader")

    def test_t06_stale_offer_and_noncomparable_benchmark_fail(self):
        evidence = self.d["evidence"][0]
        evidence["valid_until"] = "2026-11-26"
        with self.assertRaisesRegex(ValueError, "EVIDENCE_STALE"):
            validate_topic(self.topic, self.brief)
        evidence.pop("valid_until")
        evidence.update(status="VERIFIED", kind="comparison")
        self.d["purchase"].update(status="ADVANTAGE_VERIFIED",
                                  comparison={k: "mismatched" for k in (
                                      "option", "alternative", "dimension", "scenario", "period",
                                      "specification", "denominator")})
        with self.assertRaisesRegex(ValueError, "COMPARISON_NOT_COMPARABLE"):
            validate_topic(self.topic, self.brief)

    def test_t07_handoff_drift_is_rejected(self):
        self.script["v3_content_entry"] = "Spot clipping after cutting"
        with self.assertRaisesRegex(ValueError, "HANDOFF_DRIFT"):
            validate_draft(self.batch, self.selected)

    def test_t08_basic_fact_information_path_and_review(self):
        self.assertEqual(validate_topic(self.topic, self.brief)["purchase"]["status"], "INFO_ONLY")
        validate_draft(self.batch, self.selected)
        validate_review(self.batch, self.selected, self.review, "sha", "reader")

    def test_t09_customer_testimonial_stays_within_sample(self):
        self.d["evidence"][0]["kind"] = "experience"
        self.d["claims"][0]["population"] = "all_buyers"
        with self.assertRaisesRegex(ValueError, "TESTIMONIAL_OVERREACH"):
            validate_topic(self.topic, self.brief)

    def test_t10_proven_service_is_not_a_guaranteed_business_outcome(self):
        self.d["evidence"][0]["kind"] = "service"
        self.d["claims"][0]["guaranteed_outcome"] = True
        with self.assertRaisesRegex(ValueError, "CLAIM_OVERREACH"):
            validate_topic(self.topic, self.brief)

    def test_editorial_gate_is_separate_from_nine_field_passes(self):
        candidate = copy.deepcopy(self.review)
        candidate["scripts"][0]["gates"][-1]["status"] = "NOT_RUN"
        with self.assertRaisesRegex(ValueError, "THREE_GATE_BLOCKED"):
            validate_review(self.batch, self.selected, candidate, "sha", "reader")

    def test_visible_cover_rejects_unfounded_advantage_even_when_ledger_is_safe(self):
        self.topic["copy"]["cover_main"] = "全城最值的温泉，周六夜场每人79元"
        with self.assertRaisesRegex(ValueError, "VISIBLE_COPY_OVERREACH"):
            validate_topic(self.topic, self.brief)

    def test_visible_copy_and_false_claim_cannot_relabel_unsupported_price_as_fact(self):
        self.d["claims"][0]["text"] = "周六夜场每人79元"
        with self.assertRaisesRegex(ValueError, "VISIBLE_COPY_UNSUPPORTED_METRIC"):
            validate_topic(self.topic, self.brief)
        self.d["claims"][0]["text"] = self.topic["copy"]["body"]
        self.script["segments"][2]["text"] = "汤池夜场开到凌晨"
        with self.assertRaisesRegex(ValueError, "VISIBLE_COPY_UNSUPPORTED_AVAILABILITY"):
            validate_draft(self.batch, self.selected, self.brief)
