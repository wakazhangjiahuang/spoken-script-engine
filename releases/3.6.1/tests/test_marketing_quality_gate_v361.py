import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from marketing_quality_gate_v361 import (
    validate_benchmark_catalog, validate_source_inventory, validate_plan_marketing,
    validate_script_marketing, validate_marketing_review, release_validation_status
)
CATALOG = json.loads((ROOT / "references/benchmark-governance-v360.json").read_text(encoding="utf-8"))

def brief():
    return {
        "case_policy": "prefer_real",
        "facts": [{"id": "F-01", "status": "provided", "evidence_class": "user_project", "text": "Current real project brief"}],
        "source_inventory": {
            "status": "complete",
            "checked_assets": [{"asset_id": "PROJECT-BRIEF", "locator": "current project brief", "source_quote": "buyer product brief", "read": True}],
            "relevant_real_case_ids": ["F-01"], "selected_real_case_ids": ["F-01"],
            "excluded_relevant_source_ids": [],
            "selection_reason": "The real project is directly relevant to the user's current content task."
        },
        "production_resources": [{"id": "DEMO-01", "status": "available", "evidence_role": "demonstration"}]
    }

def illustration_plan():
    return {"selected": [{
        "id": "P-01", "content_mode": "real_commercial_case",
        "source_selection": {"selected_fact_ids": ["F-01"], "rejected_relevant_case_ids": [], "selection_reason": "The real client brief directly matches the topic.", "case_mode": "real"},
        "story_plan": {"buyer_need": "Buyer needs a seasonal original print.", "professional_judgment": "Translate the brief into design decisions.", "tool_or_method": "Select a brush and palette for the brief.", "product_translation": "Organize motifs for the target product.", "result": "A product-ready original print.", "transferable_value": "Show product fit rather than a standalone image."},
        "content_contract": {"promised_payoff": "Understand how a brief becomes a product-ready print."},
        "benchmark_reference": {"used": True, "benchmark_id": "illustration_commercial_case", "mechanisms_selected": ["buyer_context_and_product_specificity", "customer_brief_to_visual_decision", "original_artwork_to_product_translation"], "transfer_reason": "The same buyer-to-design logic applies.", "new_application": "Apply it to a different project and buyer.", "non_transferable_acknowledged": "Do not copy the original hook, client details or price."}
    }]}

def illustration_script():
    return {"id": "S-01", "plan_id": "P-01", "content_mode": "real_commercial_case", "source_fact_ids": ["F-01"], "cover_main": "客户为什么愿意为原创图案付费？", "cover_sub": "从产品Brief到可用的家纺印花", "professional_decision": {"case_mode": "real"}, "segments": [
        {"id": "H", "role": "hook", "text": "客户为什么愿意为原创图案付费？"},
        {"id": "B", "role": "suspense", "text": "真正影响买方判断的，不只是画得好看，而是能不能适配实际产品。"},
        {"id": "BODY", "role": "judgment", "text": "客户提出季节性家纺产品的复古水彩需求。我先按Brief判断笔刷和色彩，再把主体与辅助元素组织成适合产品的原创印花。"},
        {"id": "CTA", "role": "calling", "text": "如果你也准备服务海外买方，先检查作品集能不能让买方判断产品适配。"}
    ]}

def marketing_review(s):
    return {
        "marketing_reviewer": {"reviewer_id": "reviewer-B", "generator_id": "generator-A", "mode": "separate_model", "independent": True, "same_model_role": False},
        "marketing_checks": [{
            "script_id": s["id"],
            "user_relevance": {"passed": True, "quote": "客户为什么愿意为原创图案付费？", "reason": "The intended buyer-facing creator recognizes the commercial question."},
            "click_chain": {"passed": True, "hook_quote": "客户为什么愿意为原创图案付费？", "bridge_quote": "真正影响买方判断的，不只是画得好看，而是能不能适配实际产品。", "new_information_quote": "能不能适配实际产品", "reason": "The bridge adds a specific product-fit reason to keep watching."},
            "promise_payoff": {"passed": True, "promise_quote": "客户为什么愿意为原创图案付费？", "payoff_quote": "我先按Brief判断笔刷和色彩，再把主体与辅助元素组织成适合产品的原创印花。", "reason": "The body explains the brief, decision and product-ready output."},
            "content_mode_fit": {"passed": True, "mode": "real_commercial_case", "evidence_quote": "客户提出季节性家纺产品的复古水彩需求。", "reason": "This is a buyer-need-to-delivery commercial case, not a generic tutorial."},
            "capability_amplification": {"applicable": False, "reason": "This script makes no AI labor or capacity claim; its value is design judgment and product fit."},
            "next_level_value": {"passed": True, "quote": "先检查作品集能不能让买方判断产品适配。", "next_need": "Build a commercial portfolio for overseas buyers", "reason": "It moves from one print to the next-level need of a buyer-ready portfolio."},
            "source_fidelity": {"passed": True, "used_fact_ids": ["F-01"], "ignored_relevant_sources": [], "reason": "The actual user project fact remains in the script and was not replaced by a hypothetical."}
        }],
        "external_validation": {"human_voice_test": "NOT_RUN", "target_user_blind_read": "NOT_RUN", "rights_and_permissions": "NOT_RUN", "platform_outcome": "NOT_RUN"}
    }

class MarketingQualityGateV360Tests(unittest.TestCase):
    def test_benchmark_classes_are_separate_and_source_status_is_preserved(self):
        self.assertEqual(validate_benchmark_catalog(CATALOG), [])
        rows = {x["benchmark_key"]: x for x in CATALOG["benchmarks"]}
        self.assertNotEqual(rows["illustration_commercial_case"]["benchmark_type"], rows["ai_video_marketing_method"]["benchmark_type"])
        self.assertEqual(rows["illustration_commercial_case"]["source_status"], "USER_PROVIDED")
        self.assertEqual(rows["illustration_commercial_case"]["performance_status"], "NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(rows["ai_video_marketing_method"]["source_status"], "calibrated_reference_not_performance_verified")

    def test_real_user_case_is_selected_and_not_silently_simulated(self):
        b, p, s = brief(), illustration_plan(), illustration_script()
        self.assertEqual(validate_source_inventory(b), [])
        self.assertEqual(validate_plan_marketing(p, b, "illustration", CATALOG), [])
        s["professional_decision"]["case_mode"] = "simulated"
        self.assertTrue(any("REAL_CASE_SILENTLY_REPLACED_WITH_SIMULATION" in x for x in validate_script_marketing({"scripts": [s]}, p, b, "illustration", CATALOG)))

    def test_cross_domain_benchmark_is_blocked(self):
        p = illustration_plan()
        p["selected"][0]["benchmark_reference"]["benchmark_id"] = "AI-VIDEO-A01"
        self.assertTrue(any("CROSS_DOMAIN_BENCHMARK_USE_BLOCKED" in x for x in validate_plan_marketing(p, brief(), "illustration", CATALOG)))

    def test_missing_inventory_and_unapproved_simulation_are_blocked(self):
        b, p = brief(), illustration_plan()
        b.pop("source_inventory")
        self.assertTrue(any("SOURCE_INVENTORY_MISSING" in x for x in validate_plan_marketing(p, b, "illustration", CATALOG)))
        b = brief(); p = illustration_plan()
        p["selected"][0]["content_mode"] = "hypothetical_scenario"
        p["selected"][0]["source_selection"]["selected_fact_ids"] = []
        p["selected"][0]["source_selection"]["simulation_disclosure"] = "This is a hypothetical scenario."
        self.assertTrue(any("HYPOTHETICAL_MODE_NOT_AUTHORIZED" in x for x in validate_plan_marketing(p, b, "illustration", CATALOG)))

    def test_ai_video_capability_claim_requires_demonstration(self):
        b, p, s = brief(), illustration_plan(), illustration_script()
        s["segments"][2]["text"] += " 现在一个人也能完成过去需要多人协作的工作。"
        s["capability_claim_evidence_ids"] = []
        self.assertTrue(any("AI_CAPABILITY_AMPLIFICATION_WITHOUT_AVAILABLE_DEMONSTRATION" in x for x in validate_script_marketing({"scripts": [s]}, p, b, "ai_video", CATALOG)))

    def test_marketing_review_quotes_are_bound_and_reviewer_is_independent(self):
        b, p, s = brief(), illustration_plan(), illustration_script()
        r = marketing_review(s)
        self.assertEqual(validate_marketing_review({"scripts": [s]}, p, r, b, "illustration"), [])
        r["marketing_reviewer"]["same_model_role"] = True
        r["marketing_checks"][0]["promise_payoff"]["payoff_quote"] = "Hidden notes are not spoken script."
        errors = validate_marketing_review({"scripts": [s]}, p, r, b, "illustration")
        self.assertTrue(any("MARKETING_REVIEWER_NOT_INDEPENDENT" in x for x in errors))
        self.assertTrue(any("PROMISE_PAYOFF_QUOTES_NOT_BOUND_TO_SCRIPT" in x for x in errors))

    def test_bridge_cannot_substitute_for_body_payoff(self):
        b, p, s = brief(), illustration_plan(), illustration_script()
        r = marketing_review(s)
        r["marketing_checks"][0]["promise_payoff"]["payoff_quote"] = s["segments"][1]["text"]
        errors = validate_marketing_review({"scripts": [s]}, p, r, b, "illustration")
        self.assertTrue(any("PROMISE_PAYOFF_QUOTES_NOT_BOUND_TO_SCRIPT" in x for x in errors))

    def test_calling_must_create_a_distinct_next_level_value(self):
        b, p, s = brief(), illustration_plan(), illustration_script()
        r = marketing_review(s)
        r["marketing_checks"][0]["next_level_value"]["next_need"] = "Understand how a brief becomes a product-ready print."
        errors = validate_marketing_review({"scripts": [s]}, p, r, b, "illustration")
        self.assertTrue(any("NEXT_LEVEL_VALUE_REPEATS_CURRENT_PAYOFF" in x for x in errors))

    def test_six_negative_regression_patterns_are_blocked(self):
        mutations = [
            lambda p, b: p["selected"][0].update(content_mode="hypothetical_scenario"),
            lambda p, b: b.pop("source_inventory"),
            lambda p, b: p["selected"][0]["benchmark_reference"].update(benchmark_id="AI-VIDEO-A01"),
            lambda p, b: p["selected"][0]["source_selection"].update(case_mode="simulated"),
            lambda p, b: p["selected"][0]["benchmark_reference"].update(used_as_few_shot=True),
            lambda p, b: p["selected"][0].update(content_mode="unknown_mode")
        ]
        for i, mutate in enumerate(mutations, 1):
            with self.subTest(case=i):
                b, p = brief(), illustration_plan()
                mutate(p, b)
                self.assertTrue(validate_plan_marketing(p, b, "illustration", CATALOG))

    def test_external_validation_remains_pending_until_real_evidence(self):
        self.assertEqual(release_validation_status(marketing_review(illustration_script())), "VALIDATION_PENDING")

if __name__ == "__main__":
    unittest.main(verbosity=2)
