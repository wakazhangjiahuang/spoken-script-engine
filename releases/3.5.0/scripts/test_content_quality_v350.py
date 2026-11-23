import unittest
from scripts.content_quality_gate_v350 import (
    validate_plan_quality, validate_script_quality, validate_review_quality,
)

REGISTRY = {"AI-VIDEO-BUSINESS-GUIDE-V4.1": {"text": "企业有文档和流程资料，需要员工真正理解并执行。"}}
NEED = {"source_asset_id": "AI-VIDEO-BUSINESS-GUIDE-V4.1", "source_locator": "企业/培训", "source_quote": "需要员工真正理解并执行"}


def plan():
    return {"selected": [{"id": "P1", "audience_need_ref": NEED, "viewer_task": "把一份岗位操作文档转成可执行的培训视频", "proof_plan": ["脱敏文档、真实屏录和员工试做记录"], "content_contract": {
        "audience_need_ref": NEED, "target_audience": "负责员工培训与流程落地的企业培训负责人", "shared_task": "把一份岗位操作文档转成可执行的培训视频", "why_now": "员工看完文件仍无法按步骤完成操作", "click_reason": "看一份文档怎样变成有画面、有异常处理和验收点的操作视频", "promised_payoff": "获得按岗位任务拆解输入、操作、异常和验收的可执行方法", "proof_plan": ["脱敏文档、真实屏录和员工试做记录"], "decision_criteria": "员工能否在没有讲师提示时独立完成任务", "transferable_value": "按岗位任务而不是按文档页数组织培训内容", "next_value": "再把高频异常和复训记录纳入培训资产", "entry_competition": [
          {"id":"A","entry_type":"培训失败","click_reason":"员工看完文件仍不会操作","payoff":"找出培训内容中缺失的操作和异常处理环节","proof_plan":["员工独立试做记录与失败点清单"]},
          {"id":"B","entry_type":"文档转视频","click_reason":"一份岗位文档怎样变成可执行视频","payoff":"得到岗位任务拆解和分镜映射流程","proof_plan":["原始文档到分镜的逐段对应表"]},
          {"id":"C","entry_type":"数字人选择","click_reason":"哪些培训段落适合数字人讲解","payoff":"得到数字人适用范围与真人接手边界","proof_plan":["真人与数字人样片对照和授权记录"]}], "selected_entry_id":"B", "selection_reason":"现有资料最能证明从文档到执行任务的转化", "counterargument":"直接把文档配图并逐页念完可能更快", "counterevidence":"没有异常处理与员工试做，配图不能证明会操作"}}]}


def script():
    body = "模拟示意：这份岗位文档只有正常操作步骤，没有异常处理。先比较逐页念稿和按任务重组。逐页念稿保留信息顺序，却不能告诉员工出错时怎么办；按任务重组会先列输入、操作、异常和验收。处理前员工只看到步骤文字，处理后视频增加了异常分支和完成标准。可观察的变化是员工能按验收点独立完成一次操作。如果异常风险高，必须由岗位专家确认处理边界。"
    cta = "先选一个高频岗位任务，整理输入、操作、异常和验收四项，再让一名实际使用者试做；这样你能确认视频是否真的教会操作。"
    return {"script_id":"AI-WX-TEST-01","plan_id":"P1","cover_main":"员工看完培训文档，为什么还是不会做？","cover_sub":"用一个岗位任务拆出操作、异常和验收","content_contract":{"audience_need_ref":NEED,"target_audience":"负责员工培训与流程落地的企业培训负责人","shared_task":"把一份岗位操作文档转成可执行的培训视频","click_reason":"看一份文档怎样变成有画面、有异常处理和验收点的操作视频","promised_payoff":"获得按岗位任务拆解输入、操作、异常和验收的可执行方法","proof_plan":["脱敏文档、真实屏录和员工试做记录"],"body_payoff_anchor":{"segment_id":"BODY","quote":"按任务重组会先列输入、操作、异常和验收"}},"first_8_progression":{"hook_segment_id":"H","bridge_segment_id":"B","bridge_new_information":"员工看完文件仍不会操作，缺的是异常处理和验收点","reason_to_continue":"看任务拆解怎样改变培训视频结构"},"segments":[{"id":"H","role":"hook","text":"员工看完培训文档，为什么还是不会做？"},{"id":"B","role":"suspense","text":"员工看完文件仍不会操作，缺的是异常处理和验收点。"},{"id":"BODY","role":"judgment","text":body},{"id":"CTA","role":"calling","text":cta}],"professional_decision":{"audience_need_ref":NEED,"viewer_task":"把一份岗位操作文档转成可执行的培训视频","case_mode":"simulated","concrete_input":"模拟岗位文档只有正常操作步骤，没有异常处理和验收标准","constraints":["岗位任务必须准确","异常边界必须由岗位专家确认"],"options_considered":[{"option":"逐页念稿","tradeoff":"保留原文顺序但难以指导异常处理"},{"option":"按任务重组","tradeoff":"需要拆解输入、操作、异常和验收"}],"chosen_option":"按任务重组","rejected_option":"逐页念稿","decision_reason":"用户要完成任务而非听完文档，因此应按操作过程组织内容","source_status":"SIMULATED","evidence_refs":["AI-VIDEO-BUSINESS-GUIDE-V4.1","SIMULATED:TRAINING-01"],"applicability_boundary":"适用于有明确岗位任务和可复核操作标准的培训内容","viewer_action":"选一个高频岗位任务让实际使用者试做","spoken_anchors":{"chosen_option":{"segment_id":"BODY","quote":"按任务重组会先列输入、操作、异常和验收"},"rejected_option":{"segment_id":"BODY","quote":"逐页念稿保留信息顺序，却不能告诉员工出错时怎么办"},"decision_reason":{"segment_id":"BODY","quote":"没有异常处理与员工试做，配图不能证明会操作"},"applicability_boundary":{"segment_id":"BODY","quote":"如果异常风险高，必须由岗位专家确认处理边界"},"viewer_action":{"segment_id":"CTA","quote":"先选一个高频岗位任务"}},"simulation_disclosure":{"segment_id":"BODY","quote":"模拟示意：这份岗位文档只有正常操作步骤，没有异常处理"},"worked_example":{"input_snapshot":"这份岗位文档只有正常操作步骤，没有异常处理","decision_criterion":"员工能否在没有讲师提示时独立完成任务","before_state":"员工只看到步骤文字，不知道异常时如何处理","after_state":"视频增加异常分支和完成标准","observable_delta":"员工能按验收点独立完成一次操作","transfer_rule":"如果任务包含高风险异常，先由岗位专家确认边界再制作视频","spoken_anchor":{"segment_id":"BODY","quote":"按任务重组会先列输入、操作、异常和验收"},"result_anchor":{"segment_id":"BODY","quote":"可观察的变化是员工能按验收点独立完成一次操作"},"transfer_anchor":{"segment_id":"BODY","quote":"如果异常风险高，必须由岗位专家确认处理边界"}}},"calling_value_exchange":{"action":"选一个高频岗位任务让实际使用者试做","reason":"试做能暴露视频是否缺少异常处理或验收点","reward":"确认视频是否真的教会操作","segment_id":"CTA","quote":cta}}


class PublicV350Tests(unittest.TestCase):
    def test_plan_uses_current_need_and_three_distinct_entries(self):
        self.assertEqual(validate_plan_quality(plan(), REGISTRY, "ai_video"), [])

    def test_script_requires_spoken_before_after_and_transfer(self):
        p = plan()["selected"][0]
        s = script()
        self.assertEqual(validate_script_quality(s, p, REGISTRY, "ai_video"), [])
        del s["professional_decision"]["worked_example"]
        self.assertTrue(any("WORKED_EXAMPLE_" in e for e in validate_script_quality(s, p, REGISTRY, "ai_video")))

    def test_generic_calling_is_blocked(self):
        s = script(); s["calling_value_exchange"]["reward"] = "关注我"
        self.assertTrue(any("CALLING_REWARD_IS_ONLY_ENGAGEMENT_REQUEST" in e for e in validate_script_quality(s, plan()["selected"][0], REGISTRY, "ai_video")))

    def test_core_score_cannot_be_compensated_by_other_dimensions(self):
        s = script(); batch = {"scripts":[s]}
        dims = ["audience_need", "cover_click_reason", "opening_bridge", "body_payoff", "evidence_credibility", "platform_native", "cta_comment", "spoken_naturalness"]
        item = {"script_id":s["script_id"],"scorecard":{d:{"score":5 if d!="body_payoff" else 3} for d in dims},
          "worked_example_review":{"passed":True,"input_is_specific":True,"criterion_applied":True,"before_after_observable":True,"transferable_rule":True,"quote":s["professional_decision"]["worked_example"]["result_anchor"]["quote"],"reason":"输入、判断、结果和迁移规则均有对应证据。"},
          "calling_value_review":{"passed":True,"one_primary_action":True,"user_reward_is_clear":True,"not_engagement_only":True,"quote":s["calling_value_exchange"]["quote"],"reason":"单一行动具有明确理由和用户奖励。"},
          "click_chain_review":{"passed":True,"target_user_recognizes_value":True,"promise_is_specific":True,"body_fulfills_promise":True,"quote":s["first_8_progression"]["bridge_new_information"],"reason":"前八秒提供新信息，正文兑现承诺。"}}
        errs = validate_review_quality(batch,{"items":[item]},"ai_video")
        self.assertTrue(any("NONCOMPENSATORY_DIMENSION_FLOOR_FAILED:body_payoff:MIN_4" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
