#!/usr/bin/env python3
import unittest, tempfile, zipfile
from pathlib import Path
from content_decision_gate_v342 import validate_illustration_review, extract_text

NEED = {'source_asset_id':'ILLUSTRATION-GUIDANCE-V2.0','source_locator':'内容主线/L05 客户Brief开箱','source_quote':'客户只讲复古水彩，难确认最终使用要求'}
SCRIPT = {
 'id':'T01','script_id':'T01','cover_main':'插画Brief先补这三项','cover_sub':'版位、尺寸、工艺决定怎么画',
 'audience':'接单插画师','platform_rationale':'小红书采用可收藏的Brief核对清单，便于设计师搜索和复用。',
 'segments':[
  {'id':'S1','role':'hook','text':'客户说要复古水彩，你最先该问的不是颜色。'},
  {'id':'S2','role':'context','text':'这是模拟示意：假设Brief只有浴巾和复古水彩，没有版位、尺寸和工艺。'},
  {'id':'S3','role':'judgment','text':'先补齐产品版位和成品尺寸，再比较满版场景与局部角色；当前信息不足，我选择先锁定版位和尺寸。'},
  {'id':'S4','role':'value','text':'因为版位决定主体尺度，工艺影响细线和浅色表现；如果工艺已锁定，就可以直接进入画面测试。'},
  {'id':'S5','role':'calling','text':'先把产品版位、成品尺寸和印花工艺补进Brief，再开始画稿。'}],
 'professional_decision':{'viewer_task':'把模糊的复古水彩Brief转成可执行设计要求','audience_need_ref':NEED,
  'spoken_anchors':{'decision_reason':{'segment_id':'S4','quote':'因为版位决定主体尺度，工艺影响细线和浅色表现'}}},
 'calling':'先把产品版位、成品尺寸和印花工艺补进Brief，再开始画稿.'
}

class ReviewGateTests(unittest.TestCase):
 def _review(self):
  dims={
   'audience_and_task':{'score':3,'field':'professional_decision.viewer_task','quote':SCRIPT['professional_decision']['viewer_task'],'reason':'明确对应设计师当前任务与具体观看回报'},
   'entry_and_click_reason':{'score':4,'field':'cover_main','quote':'插画Brief先补这三项','reason':'标题指出用户需要补齐的事项'},
   'first_8_seconds':{'score':3,'segment_id':'S1','quote':'客户说要复古水彩，你最先该问的不是颜色。','reason':'开场指出具体沟通误区并建立观看理由'},
   'professional_judgment_and_payoff':{'score':5,'segment_id':'S3','quote':'我选择先锁定版位和尺寸。','reason':'说出当前约束下的具体选择'},
   'facts_evidence_and_rights':{'score':3,'segment_id':'S4','quote':'因为版位决定主体尺度，工艺影响细线和浅色表现','reason':'说明判断依据与适用条件，避免泛泛而谈'},
   'platform_native_expression':{'score':3,'field':'platform_rationale','quote':'小红书采用可收藏的Brief核对清单','reason':'解释平台内容任务与呈现方式'},
   'calling_and_action':{'score':3,'segment_id':'S5','quote':'先把产品版位、成品尺寸和印花工艺补进Brief，再开始画稿。','reason':'给出明确可执行的下一步和需要准备的输入'},
   'spoken_naturalness':{'score':3,'segment_id':'S2','quote':'这是模拟示意：假设Brief只有浴巾和复古水彩','reason':'口播清楚说明模拟前提，避免误认为真实项目'}
  }
  item={'script_id':'T01','scores':dims,'hard_gates':{k:True for k in ('lock_fields','facts','rights','promise_payoff','platform_fit','professional_value','script_04_05_mapping')},
   'source_need_review':{'passed':True,'quote':NEED['source_quote'],'reason':'逐字核对当前V2.0指导书中的需求原句'},
   'professional_decision_review':{'passed':True,'quote':SCRIPT['professional_decision']['spoken_anchors']['decision_reason']['quote'],'reason':'已核对方案差异、选择理由和适用边界均在口播中','options_materially_distinct':True,'choice_follows_constraints':True,'reason_is_specific':True,'boundary_is_valid':True,'viewer_action_is_useful':True},
   'decision':'VALIDATION_PENDING'}
  sha='a'*64
  review={'reviewer':{'mode':'human','identity':'independent-editor-01','independent':True,'same_model_role':False,'blind_packet_sha256':sha,'blind_packet_file':'blind-packet.md','review_evidence_file':'review-evidence.md','review_evidence_sha256':sha},'blind_packet_sha256':sha,'items':[item]}
  return review,item
 def test_dimension_quotes_and_floor_pass(self):
  review,_=self._review()
  self.assertEqual(validate_illustration_review({'scripts':[SCRIPT]},review),[])
 def test_dimension_below_three_blocks(self):
  review,item=self._review(); item['scores']['professional_judgment_and_payoff']['score']=2
  errors=validate_illustration_review({'scripts':[SCRIPT]},review)
  self.assertTrue(any('ILLUSTRATION_DIMENSION_BELOW_3' in x for x in errors))
 def test_quote_must_be_in_the_correct_surface(self):
  review,item=self._review(); item['scores']['entry_and_click_reason']['quote']='客户说要复古水彩'
  errors=validate_illustration_review({'scripts':[SCRIPT]},review)
  self.assertTrue(any('SCORE_QUOTE_NOT_IN_DECLARED_FIELD:entry_and_click_reason' in x for x in errors))

 def test_docx_text_extraction_reads_paragraph_content(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'guide.docx'
   xml='<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>当前目标需求原句</w:t></w:r></w:p></w:body></w:document>'
   with zipfile.ZipFile(path,'w') as z: z.writestr('word/document.xml',xml)
   self.assertIn('当前目标需求原句',extract_text(path))

 def test_same_model_reviewer_cannot_pass(self):
  review,_=self._review(); review['reviewer']['same_model_role']=True
  errors=validate_illustration_review({'scripts':[SCRIPT]},review)
  self.assertTrue(any('REVIEWER_NOT_INDEPENDENTLY_IDENTIFIED' in x for x in errors))

if __name__=='__main__': unittest.main(verbosity=2)
