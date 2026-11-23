import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_content_decision import validate_script, validate_batch, validate_review

def sample():
    return {
      "id": "T-01",
      "segments": [
        {"id": "H", "role": "hook", "text": "客户说要复古水彩，你最先该问的不是颜色。"},
        {"id": "J", "role": "judgment", "text": "这是模拟示意：假设Brief只有浴巾和风格，没有版位、尺寸与工艺；先补齐三项，再定细节密度。"},
        {"id": "C", "role": "calling", "text": "先向客户确认版位、成品尺寸和印花工艺。"}
      ],
      "professional_decision": {
        "audience_need_ref": {"source_asset_id": "ILLUSTRATION-GUIDANCE-V2.0", "source_locator": "内容主线/L05", "source_quote": "客户只讲复古水彩，难确认最终使用要求"},
        "viewer_task": "把模糊Brief转成可执行设计要求",
        "case_mode": "simulated",
        "concrete_input": "模拟Brief只有产品类别和风格，没有版位、尺寸与工艺",
        "constraints": ["产品版位和工艺未确定，不能预设细节密度"],
        "options_considered": [{"option": "先画满版场景", "tradeoff": "视觉完整但可能返工"}, {"option": "先补齐规格", "tradeoff": "前期多一步沟通但减少方向性返工"}],
        "chosen_option": "先补齐规格",
        "rejected_option": "先画满版场景",
        "decision_reason": "当前Brief缺少决定构图和细节密度的关键约束，先补齐更合理。",
        "source_status": "SIMULATED",
        "evidence_refs": ["SIM-BRIEF-01"],
        "applicability_boundary": "适用于产品用途和工艺未明确的前期Brief。",
        "viewer_action": "先确认版位、成品尺寸和印花工艺，再开始画稿。",
        "spoken_anchor": {"segment_id": "J", "quote": "先补齐三项，再定细节密度。"},
        "simulation_disclosure": {"segment_id": "J", "quote": "这是模拟示意：假设Brief只有浴巾和风格"}
      }
    }

class ContentDecisionTests(unittest.TestCase):
    def test_valid_decision(self):
        self.assertEqual(validate_script(sample()), [])
    def test_missing_decision_rejected(self):
        s = sample(); del s["professional_decision"]
        self.assertIn("T-01:PROFESSIONAL_DECISION_MISSING", validate_script(s))
    def test_unanchored_decision_rejected(self):
        s = sample(); s["professional_decision"]["spoken_anchor"]["quote"] = "not in body"
        self.assertIn("T-01:DECISION_NOT_ANCHORED_IN_SPOKEN_BODY", validate_script(s))
    def test_old_six_script_batch_rejected(self):
        b = {"scripts": [{"id": f"OLD-{i}", "segments": []} for i in range(6)]}
        errors = validate_batch(b)
        self.assertEqual(sum(x.endswith("PROFESSIONAL_DECISION_MISSING") for x in errors), 6)
    def test_review_requires_anchored_quotes_and_three_of_five_floor(self):
        dims = {"audience_need", "cover_click_reason", "opening_bridge", "body_payoff", "evidence_credibility", "platform_native", "cta_comment", "human_voice_originality"}
        quote = "先补齐三项，再定细节密度。"
        item = {"script_id":"T-01","scorecard":{d:{"score":4,"quote":quote,"reason":"该判断具体影响Brief处理顺序。"} for d in dims},"professional_decision_review":{"passed":True,"quote":quote,"reason":"决策与正文完全一致并说明了选择依据。"}}
        batch={"scripts":[sample()]}; review={"items":[item]}
        self.assertEqual(validate_review(batch,review,dims),[])
        item["scorecard"]["body_payoff"]["score"]=2
        self.assertIn("T-01:DIMENSION_BELOW_3:body_payoff",validate_review(batch,review,dims))

if __name__ == "__main__":
    unittest.main()
