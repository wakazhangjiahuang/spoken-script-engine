import unittest
from topic_gate_contract import validate_topic_gate
from video_execution_contract import validate_video_production
def candidate():
 dims={k:"PASS" for k in ["audience_specificity","viewer_relevance","benefit_clarity","evidence_sufficiency","story_progression","platform_fit","originality","claim_safety"]}
 return {"candidate_id":"T01","platform":"douyin","topic_title":"真实工作流演示","core_question":"如何把素材做成视频？","target_audience":"不会剪口播的小团队","audience_job":"把素材做成视频","audience_pain_or_desire":"不会剪且担心质量","why_care":"知道哪些工序能自动化","viewer_payoff":"获得步骤与验收边界","story_mechanism":"问题—演示—反证—结论","proof_basis":"原片与真实屏录","proof_status":"available","calling_reason":"邀请观众描述素材场景","platform_expression":"先前后对比再拆步骤","differentiation":"不同用户问题和证据路径","self_audit":{"creator_case":"可展示完整流程","audience_counterargument":"可能只是工具展示","evidence_check":"原片屏录可复核","revision_decision":"加入人工验收边界","public_summary":"受众明确且证据可用","verdict":"PASS","dimensions":dims}}
class TopicGateTests(unittest.TestCase):
 def setUp(self):self.brief={"topic_gate_required":True,"platforms":["douyin"],"count_per_platform":{"douyin":1}};self.d={"selected":[{"id":"D01","platform":"douyin","topic_candidate_id":"T01"}],"topic_gate":{"status":"USER_APPROVED","confirmation_source":"current_user_turn","confirmation_text":"确认T01","candidates":[candidate()],"approved_topic_ids":["T01"]}}
 def test_approved(self):self.assertEqual(validate_topic_gate(self.d,self.brief),[])
 def test_unconfirmed(self):self.d["topic_gate"]["status"]="DRAFT";self.assertTrue(validate_topic_gate(self.d,self.brief))
 def test_unapproved_selection(self):self.d["selected"][0]["topic_candidate_id"]="T99";self.assertTrue(validate_topic_gate(self.d,self.brief))
 def test_missing_proof(self):self.d["topic_gate"]["candidates"][0]["proof_status"]="missing";self.assertTrue(validate_topic_gate(self.d,self.brief))
class VideoTests(unittest.TestCase):
 def test_h3_requires_cards(self):self.assertTrue(validate_video_production({"brief":{"production_mode":"h3"},"scripts":[],"video_production":{"mode":"h3","h3_cards":[]}})["errors"])
if __name__=="__main__":unittest.main()
