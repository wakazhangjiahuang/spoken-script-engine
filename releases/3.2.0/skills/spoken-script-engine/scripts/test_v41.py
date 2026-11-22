#!/usr/bin/env python3
import hashlib, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_v41 import validate, DIMENSIONS
from v41_routing import is_ai_video_brief


def make_fixture(n=1, score=5, hard_pass=True, blind="PASS", independent="separate_model"):
    scripts=[]; items=[]
    for i in range(n):
        sid=f"S{i+1:02d}"; tid=f"T{i+1:02d}"
        script={
            "id":sid,"script_id":sid,"topic_id":tid,"platform":"douyin","business_line":"A",
            "audience":"有直播素材、想持续生产短视频的直播商家",
            "cover_main":"直播回放还能怎么用？",
            "cover_sub":"按引流、种草和信任重新筛选内容",
            "segments":[
                {"id":"H1","role":"hook","text":"你直播后，就认为内容结束了吗？","duration_seconds":2.5},
                {"id":"H2","role":"suspense","text":"一场直播里，可能还藏着一整套可复用的内容。","duration_seconds":4.5},
                {"id":"B1","role":"judgment","text":"先看产品卖点、客户问题和真实演示，再按不同营销目标筛选片段。","duration_seconds":12},
                {"id":"E1","role":"evidence","text":"有后台数据时再核对互动表现；没有数据就只分析视频内容。","duration_seconds":8},
                {"id":"C1","role":"calling","text":"你现在最想复用的是产品介绍、客户答疑还是现场演示？","duration_seconds":3}
            ],
            "calling":{"line":"你现在最想复用的是产品介绍、客户答疑还是现场演示？"},
            "comment_hook":{"line":"你手里的直播主要是哪一类内容？"},
            "claim_ids":["CL-01"],"proof_plan":["EV-01"]
        }
        scripts.append(script)
        candidates=[
            {"candidate_id":"A1","hook_type":"loss","user_payoff":"减少直播回放闲置","click_reason":"发现已有素材未被利用","proof_plan":["EV-01"],"risk":["不能夸大收入"]},
            {"candidate_id":"A2","hook_type":"opportunity","user_payoff":"把一场直播转成不同营销内容","click_reason":"了解片段如何按营销目标重组","proof_plan":["EV-01"],"risk":["不能把矩阵分发称为裂变"]},
            {"candidate_id":"A3","hook_type":"workflow","user_payoff":"建立可复用的内容资产流程","click_reason":"获得下一步资产管理方法","proof_plan":["EV-01"],"risk":["需真实工作流"]}
        ]
        scorecard={}
        field_map = {
            "audience_need": ("audience", script["audience"]),
            "cover_click_reason": ("cover_main", script["cover_main"]),
            "opening_bridge": ("segments.0.text", script["segments"][0]["text"]),
            "body_payoff": ("segments.2.text", script["segments"][2]["text"]),
            "evidence_credibility": ("segments.3.text", script["segments"][3]["text"]),
            "platform_native": ("cover_sub", script["cover_sub"]),
            "cta_comment": ("comment_hook.line", "你手里的直播主要是哪一类内容？"),
            "human_voice_originality": ("segments.0.text", script["segments"][0]["text"])
        }
        for dim_id, dim in DIMENSIONS.items():
            field, quote = field_map[dim_id]
            scorecard[dim_id]={"score":score,"weight":dim["weight"],"field":field,"quote":quote,"reason":"具体依据说明，结构与本项要求相符。"}
        total=sum(score/5*dim["weight"] for dim in DIMENSIONS.values())
        gates={g:{"passed":hard_pass,"reason":"已按原始材料检查。","evidence_refs":["EV-01"]} for g in ["facts","promise_payoff","proof","platform","marketing","human_voice","direction","raw_first8","eight_deliverables"]}
        item={
            "script_id":sid,"topic_id":tid,
            "candidate_competition":{"locked":False,"candidates":candidates,"selected_candidate_id":"A2","selection_reason":"用户收益与证据最匹配。","counterargument":"矩阵分发并不等于裂变。","counterevidence":"没有分享机制时不使用裂变主张。","confidence":0.84,"unresolved_risks":[],"repair_fields":[]},
            "scorecard":scorecard,"reported_total_score":total,"hard_gates":gates,
            "review_routing":{
                "fast_screen":{"status":"PASS","role":"laya_like_fast_screen","reviewer_identity":"fast-reviewer","independence_level":"same_model_role"},
                "deep_review":{"status":"PASS","role":"jev_like_deep_review","reviewer_identity":"deep-reviewer","independence_level":independent},
                "critic":{"status":"PASS","role":"independent_critic","reviewer_identity":"critic-reviewer","independence_level":independent}
            },
            "decision":{"verdict":"STRONG_CANDIDATE" if total >= 85 else "CANDIDATE","reason":"结构、证据和评审均符合门禁。"},
            "human_voice_test":{"status":"PASS","reader_identity":"reader-1","reader_is_author":False,"evidence":"非作者朗读录音及问题记录。"},
            "blind_test":{"status":blind,"participants":5 if blind=="PASS" else 0,"reader_ids":["u1","u2","u3","u4","u5"] if blind=="PASS" else [],"correct_topic_count":4 if blind=="PASS" else 0,"correct_value_count":3 if blind=="PASS" else 0,"click_intent_count":3 if blind=="PASS" else 0}
        }
        items.append(item)
    manifest={"batch_id":"BATCH-TEST","unit_type":"platform_script","expected_topics":n,"expected_scripts":n,"expected_by_platform":{"douyin":n},"batch_stage":"sample_calibration","blind_test_scope":"all_scripts"}
    review={"contract_version":"1.0.0","batch_sha256":"pending","generator_identity":"writer-model","generator_model":"writer-model-v1","batch_manifest":manifest,"items":items,"diversity_review":{"status":"PASS","reviewed_script_count":n,"reviewer_identity":"diversity-reviewer","method":"clustered semantic review","near_duplicates":[]}}
    batch={"brief":{"business_line":"A"},"scripts":scripts}
    payload_sha=hashlib.sha256(json.dumps(batch,ensure_ascii=False,separators=(",", ":")).encode("utf-8")).hexdigest()
    review["batch_sha256"]=payload_sha
    return batch,review


class V41Tests(unittest.TestCase):
    def test_all_pass_requires_full_review(self):
        b,r=make_fixture(score=5)
        out=validate(b,r)
        self.assertEqual(out["status"],"PASS")
        self.assertTrue(out["passed"])

    def test_70_to_74_is_revise_not_pass(self):
        b,r=make_fixture(score=4)
        item=r["items"][0]
        item["scorecard"]["audience_need"]["score"]=2
        item["reported_total_score"]=74
        item["decision"]["verdict"]="REVISE"
        out=validate(b,r)
        self.assertEqual(out["items"][0]["score_band"],"REVISE")
        self.assertEqual(out["status"],"NEEDS_REVISION")

    def test_hard_gate_blocks_high_score(self):
        b,r=make_fixture(score=5,hard_pass=False)
        r["items"][0]["decision"]["verdict"]="BLOCKED"
        out=validate(b,r)
        self.assertEqual(out["items"][0]["score_band"],"BLOCKED")
        self.assertEqual(out["status"],"NEEDS_REVISION")

    def test_missing_blind_test_is_pending(self):
        b,r=make_fixture(score=5,blind="NOT_RUN")
        r["items"][0]["decision"]["verdict"]="VALIDATION_PENDING"
        out=validate(b,r)
        self.assertEqual(out["status"],"VALIDATION_PENDING")

    def test_same_model_roles_not_independent(self):
        b,r=make_fixture(score=5,independent="same_model_role")
        r["items"][0]["decision"]["verdict"]="VALIDATION_PENDING"
        out=validate(b,r)
        self.assertEqual(out["status"],"VALIDATION_PENDING")
        self.assertIn("independent_review",out["items"][0]["validation_pending"])

    def test_batch_average_cannot_hide_one_failed_item(self):
        b,r=make_fixture(n=2,score=5)
        r["items"][1]["scorecard"]["body_payoff"]["score"]=0
        r["items"][1]["scorecard"]["audience_need"]["score"]=0
        total=sum(x["score"] / 5 * x["weight"] for x in r["items"][1]["scorecard"].values())
        r["items"][1]["reported_total_score"]=total
        r["items"][1]["decision"]["verdict"]="REWRITE"
        out=validate(b,r)
        self.assertEqual(out["status"],"NEEDS_REVISION")
        self.assertEqual(out["items"][1]["score_band"],"REWRITE")
        self.assertFalse(out["average_used_for_release"])

    def test_count_mismatch_fails(self):
        b,r=make_fixture(n=1,score=5)
        r["batch_manifest"]["expected_scripts"]=2
        out=validate(b,r)
        self.assertIn("expected_scripts count mismatch",out["errors"])

    def test_quote_must_exist(self):
        b,r=make_fixture(score=5)
        r["items"][0]["scorecard"]["body_payoff"]["quote"]="不存在的原文"
        out=validate(b,r)
        self.assertTrue(any("score evidence quote absent" in x for x in out["items"][0]["errors"]))

    def test_locked_title_is_preserved(self):
        b,r=make_fixture(score=5)
        r["items"][0]["candidate_competition"]["locked"]=True
        r["items"][0]["candidate_competition"]["locked_fields"]={"cover_main":"原锁定标题"}
        out=validate(b,r)
        self.assertTrue(any("user-locked field changed" in x for x in out["items"][0]["errors"]))

    def test_semantically_same_candidates_are_flagged(self):
        b,r=make_fixture(score=5)
        cs=r["items"][0]["candidate_competition"]["candidates"]
        cs[1]["hook_type"]=cs[0]["hook_type"]
        cs[1]["user_payoff"]=cs[0]["user_payoff"]
        cs[1]["click_reason"]=cs[0]["click_reason"]
        r["items"][0]["decision"]["verdict"]="REVISE"
        out=validate(b,r)
        self.assertTrue(any("not substantively distinct" in x for x in out["items"][0]["errors"]))

    def test_100_topics_three_platforms_are_300_scripts(self):
        b,r=make_fixture(n=300,score=5)
        platforms=["douyin","xiaohongshu","wechat_channels"]
        for i,script in enumerate(b["scripts"]):
            topic=f"T{i%100+1:03d}"
            script["topic_id"]=topic
            script["platform"]=platforms[i//100]
            r["items"][i]["topic_id"]=topic
        r["batch_manifest"]["expected_topics"]=100
        r["batch_manifest"]["expected_scripts"]=300
        r["batch_manifest"]["expected_by_platform"]={"douyin":100,"xiaohongshu":100,"wechat_channels":100}
        r["batch_manifest"]["blind_test_scope"]="pilot_only"
        r["diversity_review"]["reviewed_script_count"]=300
        r["batch_sha256"]=hashlib.sha256(json.dumps(b,ensure_ascii=False,separators=(",", ":")).encode("utf-8")).hexdigest()
        out=validate(b,r)
        self.assertEqual(out["status"],"PASS")
        self.assertEqual(out["topic_count"],100)
        self.assertEqual(out["script_count"],300)

    def test_multi_platform_count_contract(self):
        b,r=make_fixture(n=2,score=5)
        b["scripts"][1]["platform"]="xiaohongshu"
        r["batch_manifest"]["expected_by_platform"]={"douyin":1,"xiaohongshu":1}
        r["batch_sha256"]=hashlib.sha256(json.dumps(b,ensure_ascii=False,separators=(",", ":")).encode("utf-8")).hexdigest()
        out=validate(b,r)
        self.assertEqual(out["status"],"PASS")

    def test_ai_video_domain_routes_to_v41(self):
        self.assertTrue(is_ai_video_brief({"domain":"ai_video"}))
        self.assertTrue(is_ai_video_brief({"quality_profile":"ai_video_v4_1"}))
        self.assertTrue(is_ai_video_brief({"business_line":"A"}))
        self.assertTrue(is_ai_video_brief({"business_lines":["B","C"]}))

    def test_reviewer_cannot_claim_independence_with_same_generator_identity(self):
        b,r=make_fixture(score=5)
        r["items"][0]["review_routing"]["critic"]["reviewer_identity"]="writer-model"
        r["items"][0]["decision"]["verdict"]="REVISE"
        out=validate(b,r)
        self.assertTrue(any("falsely marked independent" in x for x in out["items"][0]["errors"]))

    def test_non_ai_domains_do_not_load_ai_video_overlay(self):
        self.assertFalse(is_ai_video_brief({"domain":"illustration","business_line":"A"}))
        self.assertFalse(is_ai_video_brief({"domain":"tourism"}))
        self.assertFalse(is_ai_video_brief({"domain":"engineering_consulting"}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
