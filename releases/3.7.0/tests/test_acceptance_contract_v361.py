import hashlib, json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from acceptance_contract_v361 import (
    CRITERIA, validate_source_inventory, validate_decision_competition, visible_review_copy,
    validate_draft_delivery, validate_review,
)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class FourLayerAcceptanceV361Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.run = Path(self.tmp.name)
        (self.run / "sources").mkdir()
        self.source = self.run / "sources" / "01.txt"
        self.source.write_text("原始客户需求：客户提出婴童围兜印花需求，要求图案适配产品尺寸。", encoding="utf-8")
        self.source_sha = sha(self.source)
        self.source_manifest = {"sources": [{"original_name": "brief.txt", "stored_path": "sources/01.txt", "sha256": self.source_sha}]}
        (self.run / "source-manifest.json").write_text(json.dumps(self.source_manifest, ensure_ascii=False), encoding="utf-8")
        self.brief = {
            "domain": "illustration", "case_policy": "prefer_real",
            "facts": [{"id": "F1", "text": "客户提出婴童围兜印花需求", "status": "provided", "evidence_class": "user_project"}],
            "source_inventory": {
                "status": "complete", "selection_reason": "本轮真实客户需求与插画商业案例直接相关，优先使用原始材料。",
                "checked_assets": [{"asset_id": "A1", "source_file": "sources/01.txt", "source_sha256": self.source_sha, "locator": "原始需求文档第1段", "source_quote": "原始客户需求：客户提出婴童围兜印花需求", "read": True}],
                "fact_evidence": [{"fact_id": "F1", "source_asset_id": "A1", "source_file": "sources/01.txt", "source_sha256": self.source_sha, "source_quote": "原始客户需求：客户提出婴童围兜印花需求", "source_locator": "原始需求文档第1段"}],
                "relevant_real_case_ids": ["F1"], "selected_real_case_ids": ["F1"], "excluded_relevant_source_ids": []
            }
        }
        self.decision = {
            "marketing_entry_competition": {
                "selected_candidate_id": "C1", "comparison_summary": "三种入口分别触达买方产品适配、插画师商业接单和设计交付效率，证据及正文兑现路径不同。",
                "decision_reason": "选择买方产品适配入口，因为原始Brief可以支撑，且正文能展示专业判断和产品交付。",
                "tradeoffs": ["放弃泛AI效率话题，优先产品买方的具体判断。"],
                "candidates": [
                    self.candidate("C1", "buyer_product_fit", "婴童品牌买方为什么需要产品适配", "从产品Brief展示设计判断和适配结果", True),
                    self.candidate("C2", "creator_commercial_order", "商业插画师怎样提高海外客户接单能力", "从作品集呈现海外买方能理解的商业价值", False),
                    self.candidate("C3", "workflow_efficiency", "怎样减少客户反复修改和沟通成本", "从需求确认和交付流程切入并降低返工", False),
                ]
            },
            "selected": [{"id": "P1", "selected_entry_candidate_id": "C1", "content_mode": "real_commercial_case", "source_selection": {"selected_fact_ids": ["F1"]}}]
        }
        self.script = self.make_script()
        self.batch = {"scripts": [self.script]}
        self.batch_path = self.run / "batch-v1.json"
        self.batch_path.write_text(json.dumps(self.batch, ensure_ascii=False), encoding="utf-8")
        self.decision_path = self.run / "decision.json"
        self.decision_path.write_text(json.dumps(self.decision, ensure_ascii=False), encoding="utf-8")

    def tearDown(self): self.tmp.cleanup()

    def candidate(self, cid, entry_type, need, payoff, selected):
        return {"candidate_id": cid, "entry_type": entry_type, "target_user": "服务婴童品牌的原创插画师", "user_need": need,
                "hook": "客户提出需求后，怎样判断图案能不能真正用于围兜？" if cid == "C1" else f"{need}？",
                "click_reason": f"用户希望获得{need}的具体判断依据", "promised_payoff": payoff,
                "evidence_refs": ["F1"], "delivery_plan": "展示真实需求、设计判断、产品适配和最终输出", "commercial_value": "提升商业项目沟通和交付价值",
                "risk": "如果没有产品尺寸和印花限制，不能声称已经完成适配", "counter_evidence": "当前资料只证明客户提出需求，不证明已经成交或量产",
                "selected": selected, "selection_reason": "与原始真实需求最匹配，证据和交付均可兑现。" if selected else "此入口与本轮真实材料的直接关联较弱，故不选。",
                "rejection_reason": "本轮目标不是泛化接单教育，现有材料不能支撑该入口。" if not selected else ""}

    def make_script(self):
        body = "客户提出婴童围兜印花需求。先判断产品Brief和尺寸约束，再选择适合的画法与配色，调整主体比例和图案密度，形成适配围兜的原创印花，最后按实际产品尺寸检查输出。这个判断方法可以迁移到其他婴童纺织品。"
        stages = {
            "buyer_need": "客户提出婴童围兜印花需求",
            "professional_judgment": "先判断产品Brief和尺寸约束",
            "tool_or_method": "再选择适合的画法与配色",
            "product_translation": "调整主体比例和图案密度",
            "result": "形成适配围兜的原创印花",
            "transferable_value": "这个判断方法可以迁移到其他婴童纺织品",
        }
        return {
            "id": "S1", "script_id": "S1", "plan_id": "P1", "selected_entry_candidate_id": "C1", "platform": "抖音",
            "content_mode": "real_commercial_case", "source_fact_ids": ["F1"], "source_asset_ids": ["A1"],
            "cover_main": "客户为什么需要产品适配？", "cover_sub": "从围兜Brief到原创印花交付",
            "segments": [
                {"id": "H", "role": "hook", "duration_seconds": 3, "text": "客户为什么需要产品适配？"},
                {"id": "B", "role": "bridge", "duration_seconds": 5, "text": "先看产品尺寸和印花限制，再决定图案怎么画。"},
                {"id": "BODY", "role": "judgment", "duration_seconds": 35, "text": body},
                {"id": "CTA", "role": "calling", "duration_seconds": 7, "text": "如果你也做婴童纺织印花，先拿一个真实产品Brief检查作品是否适配，为后续建立产品适配作品集打好基础。"},
            ],
            "narrative_map": {"content_mode": "real_commercial_case", "stages": [{"stage_id": k, "quote": v} for k, v in stages.items()]},
            "claim_evidence": [{"fact_id": "F1", "spoken_claim_quote": "客户提出婴童围兜印花需求", "source_asset_id": "A1", "source_file": "sources/01.txt", "source_sha256": self.source_sha, "source_locator": "原始需求文档第1段", "source_quote": "原始客户需求：客户提出婴童围兜印花需求"}],
            "calling": {"action": "检查一个真实产品Brief", "reason": "先确认设计是否适配具体产品", "user_payoff": "减少无效修改并提高买方判断效率", "quote": "先拿一个真实产品Brief检查作品是否适配，为后续建立产品适配作品集打好基础。"},
            "platform_fit": {"platform": "抖音", "user_task": "快速判断产品图案是否适配", "native_expression_reason": "开头直接给出产品问题，正文用真实需求和具体判断推进，适合短视频快速理解。", "quote": "先看产品尺寸和印花限制，再决定图案怎么画。"}
        }

    def make_attestation(self):
        batch_sha = sha(self.batch_path); decision_sha = sha(self.decision_path); manifest_sha = sha(self.run / "source-manifest.json")
        review_evidence = self.run / "review-evidence.json"
        review_evidence.write_text(json.dumps({"reviewer_id": "reviewer-B", "batch_sha256": batch_sha, "reviewed_script_ids": ["S1"], "verdict": "DRAFT_FOR_USER_REVIEW"}), encoding="utf-8")
        blind_packet = self.run / "blind-packet.json"
        blind_packet.write_text(json.dumps({"batch_sha256": batch_sha, "script_ids": ["S1"], "actual_copy": [visible_review_copy(self.script)]}, ensure_ascii=False), encoding="utf-8")
        return {"reviewer_id": "reviewer-B", "generator_id": "generator-A", "reviewer_session_id": "session-B", "generator_session_id": "session-A", "reviewed_at": "2026-11-23T12:00:00+08:00",
                "independence_level": "separate_model", "independent": True, "same_model_role": False, "reviewer_mode": "separate_model", "reviewer_model": "model-B", "generator_model": "model-A",
                "review_evidence_path": "review-evidence.json", "review_evidence_sha256": sha(review_evidence), "blind_packet_path": "blind-packet.json", "blind_packet_sha256": sha(blind_packet),
                "batch_sha256": batch_sha, "decision_sha256": decision_sha, "source_manifest_sha256": manifest_sha, "attestation_method": "separate_model_session_log", "contains_scores": False}

    def make_review(self):
        checks = []
        quote_map = {
            "user_need": ["客户为什么需要产品适配？"], "cover": [self.script["cover_main"], self.script["cover_sub"]],
            "opening_0_3": ["客户为什么需要产品适配？"], "bridge_3_8": ["先看产品尺寸和印花限制，再决定图案怎么画。"],
            "body_mode": ["客户提出婴童围兜印花需求", "先判断产品Brief和尺寸约束", "再选择适合的画法与配色", "调整主体比例和图案密度", "形成适配围兜的原创印花", "这个判断方法可以迁移到其他婴童纺织品"], "promise_payoff": [self.script["cover_main"], "形成适配围兜的原创印花"],
            "next_level_value": ["为后续建立产品适配作品集打好基础。"], "calling": ["先拿一个真实产品Brief检查作品是否适配，为后续建立产品适配作品集打好基础。"],
            "platform_fit": ["先看产品尺寸和印花限制，再决定图案怎么画。"]
        }
        for cid, _ in CRITERIA:
            status = "PENDING" if cid in {"oral_delivery", "independent_review", "outcome_feedback"} else "PASS"
            row = {"criterion_id": cid, "status": status, "reason": "逐项引用实际成品或记录待外部验证事项，不能用总分补偿单项短板。"}
            if cid in quote_map: row["quotes"] = quote_map[cid]
            if cid == "next_level_value": row["next_need"] = "为海外买方建立可复用的产品适配作品集"
            if cid == "topic_selection": row["evidence_refs"] = ["C1", "C2", "C3"]
            if cid == "evidence": row["evidence_refs"] = ["F1"]
            if cid == "capability_amplification": row.update(status="NOT_APPLICABLE", not_applicable_reason="本篇不提出AI能力、节省人力或替代团队的主张。")
            checks.append(row)
        return {"reviewer_attestation": self.make_attestation(), "delivery_acceptance": [{"script_id": "S1", "checks": checks}],
                "external_validation": {"human_voice_test": [], "target_user_blind_read": [], "rights_and_permissions": {"assets": []}, "platform_outcome": []}}

    def test_source_inventory_checks_original_file_hash_and_quote(self):
        self.assertEqual(validate_source_inventory(self.brief, self.run), [])
        self.source.write_text("内容已被替换", encoding="utf-8")
        errors = validate_source_inventory(self.brief, self.run)
        self.assertTrue(any("SOURCE_FILE_SHA256_MISMATCH" in x for x in errors))
        self.assertTrue(any("SOURCE_ASSET_QUOTE_NOT_FOUND" in x for x in errors))

    def test_three_distinct_entry_options_and_rejection_reasons_are_required(self):
        self.assertEqual(validate_decision_competition(self.decision, self.brief, "illustration", self.run), [])
        broken = json.loads(json.dumps(self.decision))
        broken["marketing_entry_competition"]["candidates"] = broken["marketing_entry_competition"]["candidates"][:2]
        self.assertTrue(validate_decision_competition(broken, self.brief, "illustration", self.run))

    def test_mode_specific_narrative_map_is_quote_bound(self):
        self.assertEqual(validate_draft_delivery(self.batch, self.decision, self.brief, "illustration", self.run), [])
        broken = json.loads(json.dumps(self.batch))
        broken["scripts"][0]["narrative_map"]["stages"] = broken["scripts"][0]["narrative_map"]["stages"][:-1]
        self.assertTrue(any("NARRATIVE_STAGE_NOT_ANCHORED" in x for x in validate_draft_delivery(broken, self.decision, self.brief, "illustration", self.run)))

    def test_spoken_claim_source_quote_must_exist_in_the_original_file(self):
        broken = json.loads(json.dumps(self.batch))
        broken["scripts"][0]["claim_evidence"][0]["source_quote"] = "一条并不存在的客户订单和收入记录"
        errors = validate_draft_delivery(broken, self.decision, self.brief, "illustration", self.run)
        self.assertTrue(any("SCRIPT_SOURCE_QUOTE_NOT_FOUND_IN_ORIGINAL" in x for x in errors))

    def test_real_case_cannot_be_silently_changed_to_hypothetical(self):
        broken = json.loads(json.dumps(self.batch))
        broken["scripts"][0]["content_mode"] = "hypothetical_scenario"
        self.assertTrue(validate_draft_delivery(broken, self.decision, self.brief, "illustration", self.run))

    def test_valid_15_point_review_remains_pending_without_external_evidence(self):
        review = self.make_review()
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "VALIDATION_PENDING")
        self.assertEqual(result["criteria_per_script"], 15)
        self.assertEqual(result["criteria_total"], 15)
        self.assertFalse(result["average_score_used_for_release"])

    def test_any_failed_criterion_blocks_even_when_other_fourteen_pass(self):
        review = self.make_review()
        review["delivery_acceptance"][0]["checks"][0]["status"] = "FAIL"
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("NON_COMPENSATORY_CRITERION_FAILED" in x for x in result["errors"]))

    def test_same_reviewer_identity_or_session_is_blocked(self):
        review = self.make_review()
        review["reviewer_attestation"]["reviewer_id"] = "generator-A"
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("REVIEWER_ID_EQUALS_GENERATOR" in x for x in result["errors"]))

    def test_oral_delivery_cannot_pass_without_human_voice_recording(self):
        review = self.make_review()
        item = next(x for x in review["delivery_acceptance"][0]["checks"] if x["criterion_id"] == "oral_delivery")
        item["status"] = "PASS"
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("ORAL_DELIVERY_PASS_WITHOUT_HUMAN_VOICE_EVIDENCE" in x for x in result["errors"]))

    def test_outcome_feedback_cannot_pass_without_real_platform_post_data(self):
        review = self.make_review()
        item = next(x for x in review["delivery_acceptance"][0]["checks"] if x["criterion_id"] == "outcome_feedback")
        item["status"] = "PASS"
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("OUTCOME_FEEDBACK_PASS_WITHOUT_REAL_PLATFORM_DATA" in x for x in result["errors"]))

    def test_missing_one_of_fifteen_criteria_is_blocked(self):
        review = self.make_review()
        review["delivery_acceptance"][0]["checks"].pop()
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("FIFTEEN_CRITERIA_NOT_EXACTLY_COVERED" in x for x in result["errors"]))

    def test_platform_outcome_requires_real_post_metrics_and_traceable_evidence(self):
        review = self.make_review()
        post = self.run / "post-export.json"
        post.write_text(json.dumps({"post_id": "p-1", "views": 1000}), encoding="utf-8")
        review["external_validation"]["platform_outcome"] = [{"script_id": "S1", "status": "PASSED", "post_id": "p-1", "post_url": "https://example.com/post/1", "published_at": "2026-11-20T12:00:00+08:00", "captured_at": "2026-11-21T12:00:00+08:00", "data_source": "platform_export", "metrics": {"views": 1000}, "evidence_path": "post-export.json", "evidence_sha256": sha(post), "analysis": {"baseline_or_comparator": "Compared with the previous five similar posts.", "diagnosis": "Views increased but save rate was lower than the account baseline.", "attribution_limit": "The sample is small and topic seasonality may affect the result.", "next_action": "Keep the buyer-fit hook and test a more specific product proof."}}]
        # The acceptance item must also remain pending unless the actual outcome is independently accepted.
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertNotEqual(result["status"], "PASS")

    def test_all_external_evidence_can_pass_only_when_each_script_is_verified(self):
        review = self.make_review()
        voice = self.run / "voice.wav"; voice.write_bytes(b"RIFF" + b"0" * 128)
        blind = self.run / "blind-read.json"; blind.write_text(json.dumps({"participants": 3, "correct_topic_count": 3, "correct_value_count": 2}), encoding="utf-8")
        rights = self.run / "rights.json"; rights.write_text(json.dumps({"asset_id": "A1", "rights_status": "USER_OWNED", "scope": "current project"}), encoding="utf-8")
        post = self.run / "platform.json"; post.write_text(json.dumps({"post_id": "p-1", "views": 1000, "saves": 45}), encoding="utf-8")
        att = review["reviewer_attestation"]
        review["external_validation"] = {
            "human_voice_test": [{"script_id": "S1", "status": "PASSED", "reader_id": "reader-01", "reader_is_author": False, "measured_seconds": 50, "target_seconds": 52, "evidence_path": "voice.wav", "evidence_sha256": sha(voice)}],
            "target_user_blind_read": [{"script_id": "S1", "status": "PASSED", "participants": [{"participant_id": "u1", "topic_understood": True, "value_understood": True}, {"participant_id": "u2", "topic_understood": True, "value_understood": True}, {"participant_id": "u3", "topic_understood": True, "value_understood": False}], "author_present": False, "blind_packet_sha256": att["blind_packet_sha256"], "correct_topic_count": 3, "correct_value_count": 2, "evidence_path": "blind-read.json", "evidence_sha256": sha(blind)}],
            "rights_and_permissions": {"assets": [{"asset_id": "A1", "rights_status": "USER_OWNED", "evidence_path": "rights.json", "evidence_sha256": sha(rights), "scope": "current project"}]},
            "platform_outcome": [{"script_id": "S1", "status": "PASSED", "post_id": "p-1", "post_url": "https://example.com/post/1", "published_at": "2026-11-20T12:00:00+08:00", "captured_at": "2026-11-21T12:00:00+08:00", "data_source": "platform_export", "metrics": {"views": 1000, "saves": 45}, "evidence_path": "platform.json", "evidence_sha256": sha(post), "analysis": {"baseline_or_comparator": "Compared with the previous five similar posts.", "diagnosis": "Views were above baseline but saves remained below the target.", "attribution_limit": "The sample is small and topic seasonality may affect the result.", "next_action": "Keep the buyer-fit hook and test a clearer product proof."}}]
        }
        for item in review["delivery_acceptance"][0]["checks"]:
            if item["criterion_id"] in {"oral_delivery", "independent_review", "outcome_feedback"}:
                item["status"] = "PASS"
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "PASS", result["errors"])

    def test_failed_external_voice_or_rights_evidence_blocks(self):
        review = self.make_review()
        review["external_validation"]["human_voice_test"] = [{"script_id": "S1", "status": "FAILED"}]
        result = validate_review(self.batch, self.decision, self.brief, review, self.run, self.batch_path)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("HUMAN_VOICE_TEST_FAILED" in x for x in result["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
