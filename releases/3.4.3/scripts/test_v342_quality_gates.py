#!/usr/bin/env python3
import unittest
from content_decision_gate_v342 import validate_need_ref, validate_professional_decision, validate_plan, validate_batch

REGISTRY = {'ILLUSTRATION-GUIDANCE-V2.0': {'asset_id':'ILLUSTRATION-GUIDANCE-V2.0','text':'内容主线\nL05 客户Brief开箱\n客户只讲复古水彩，难确认最终使用要求。'}}
NEED = {'source_asset_id':'ILLUSTRATION-GUIDANCE-V2.0','source_locator':'内容主线/L05 客户Brief开箱','source_quote':'客户只讲复古水彩，难确认最终使用要求'}

def script():
    return {'id':'T01','plan_id':'T01','topic_id':'T01','viewer_task':'把模糊的复古水彩Brief转成可执行设计要求',
      'segments':[
        {'id':'S1','role':'hook','text':'客户说要复古水彩，你最先该问的不是颜色。'},
        {'id':'S2','role':'context','text':'这是模拟示意：假设Brief只有浴巾和复古水彩，没有版位、尺寸和工艺。'},
        {'id':'S3','role':'judgment','text':'先补齐产品版位和成品尺寸，再比较满版场景与局部角色；当前信息不足，我选择先锁定版位和尺寸。'},
        {'id':'S4','role':'value','text':'因为版位决定主体尺度，工艺影响细线和浅色表现；如果工艺已锁定，就可以直接进入画面测试。'},
        {'id':'S5','role':'calling','text':'先把产品版位、成品尺寸和印花工艺补进Brief，再开始画稿。'}],
      'professional_decision':{
        'audience_need_ref':NEED,'viewer_task':'把模糊的复古水彩Brief转成可执行设计要求','case_mode':'simulated',
        'concrete_input':'模拟Brief只有浴巾品类和复古水彩风格，没有版位、尺寸与工艺',
        'constraints':['产品版位未确认，无法确定主体占比','印花工艺未知，不能预设细线和浅色表现'],
        'options_considered':[{'option':'先画满版场景','tradeoff':'画面完整，但局部产品位可能无法直接复用'}, {'option':'先锁定版位和尺寸','tradeoff':'前期多一次沟通，但能先确定主体尺度和细节边界'}],
        'chosen_option':'先锁定版位和尺寸','rejected_option':'先画满版场景',
        'decision_reason':'当前Brief缺少版位和工艺两个决定性条件，先确认它们比直接画满版更能避免方向性返工。',
        'source_status':'SIMULATED','evidence_refs':['ILLUSTRATION-GUIDANCE-V2.0','SIMULATED:BRIEF-01'],
        'applicability_boundary':'适用于前期用途和工艺未明确的Brief；若产品版位与工艺已锁定，可直接进入构图和打样验证。',
        'viewer_action':'先向客户确认版位、成品尺寸和印花工艺，再开始画稿。',
        'spoken_anchors':{
          'chosen_option':{'segment_id':'S3','quote':'我选择先锁定版位和尺寸。'},
          'rejected_option':{'segment_id':'S3','quote':'再比较满版场景与局部角色'},
          'decision_reason':{'segment_id':'S4','quote':'因为版位决定主体尺度，工艺影响细线和浅色表现'},
          'applicability_boundary':{'segment_id':'S4','quote':'如果工艺已锁定，就可以直接进入画面测试。'},
          'viewer_action':{'segment_id':'S5','quote':'先把产品版位、成品尺寸和印花工艺补进Brief，再开始画稿。'}},
        'simulation_disclosure':{'segment_id':'S2','quote':'这是模拟示意：假设Brief只有浴巾和复古水彩'}
      }}

class V342GateTests(unittest.TestCase):
    def test_need_quote_must_exist_verbatim(self):
        bad=dict(NEED,source_quote='品牌客户都喜欢复古水彩')
        self.assertTrue(validate_need_ref(bad,REGISTRY,'illustration'))
    def test_need_locator_must_exist(self):
        bad=dict(NEED,source_locator='第九章/完全不存在')
        self.assertTrue(validate_need_ref(bad,REGISTRY,'illustration'))
    def test_wrong_domain_source_id_blocked(self):
        bad=dict(NEED,source_asset_id='OLD-SAMPLE-V3.0')
        self.assertTrue(validate_need_ref(bad,REGISTRY,'illustration'))
    def test_decision_requires_all_spoken_anchors(self):
        s=script(); del s['professional_decision']['spoken_anchors']['decision_reason']
        errors=validate_professional_decision(s,NEED,REGISTRY,{'ILLUSTRATION-GUIDANCE-V2.0','SIMULATED:BRIEF-01'},'illustration')
        self.assertTrue(any('SPOKEN_DECISION_ANCHOR_MISSING:decision_reason' in x for x in errors))
    def test_decision_anchor_must_match_actual_speech(self):
        s=script(); s['professional_decision']['spoken_anchors']['chosen_option']['quote']='先确认一个需求就好'
        errors=validate_professional_decision(s,NEED,REGISTRY,{'ILLUSTRATION-GUIDANCE-V2.0','SIMULATED:BRIEF-01'},'illustration')
        self.assertTrue(any('SPOKEN_DECISION_ANCHOR_NOT_VERBATIM:chosen_option' in x for x in errors))
    def test_synonym_options_are_not_real_competition(self):
        s=script(); s['professional_decision']['options_considered']=[{'option':'先锁定版位和尺寸','tradeoff':'前期多一次沟通，但能确定细节边界'},{'option':'先锁定版位与尺寸','tradeoff':'先做沟通再开始设计，减少后期返工'}]
        s['professional_decision']['chosen_option']='先锁定版位和尺寸'; s['professional_decision']['rejected_option']='先锁定版位与尺寸'
        errors=validate_professional_decision(s,NEED,REGISTRY,{'ILLUSTRATION-GUIDANCE-V2.0','SIMULATED:BRIEF-01'},'illustration')
        self.assertTrue(any('OPTIONS_ARE_PARAPHRASES' in x for x in errors))
    def test_simulation_must_be_spoken(self):
        s=script(); s['professional_decision']['simulation_disclosure']['quote']='这是一个真实客户项目'
        errors=validate_professional_decision(s,NEED,REGISTRY,{'ILLUSTRATION-GUIDANCE-V2.0','SIMULATED:BRIEF-01'},'illustration')
        self.assertTrue(any('SIMULATION_DISCLOSURE_NOT_SPOKEN' in x for x in errors))
    def test_plan_and_script_must_share_same_need_ref(self):
        s=script(); s['professional_decision']['audience_need_ref']=dict(NEED,source_quote='别的需求')
        plan={'selected':[{'id':'T01','viewer_task':s['viewer_task'],'audience_need_ref':NEED,'proof_plan':['V2.0 guide']} ]}
        errors=validate_batch({'scripts':[s]},{'domain':'illustration'},{'assets':[]},plan,REGISTRY)
        self.assertTrue(any('SCRIPT_AUDIENCE_NEED_REF_DIFFERS_FROM_APPROVED_PLAN' in x for x in errors))
    def test_old_six_script_pattern_rejected(self):
        batch={'scripts':[{'id':f'OLD-{i}','segments':[{'id':'S1','role':'hook','text':'通用步骤'}]} for i in range(6)]}
        decision={'selected':[{'id':f'OLD-{i}','viewer_task':'一个普通任务','audience_need_ref':NEED} for i in range(6)]}
        errors=validate_batch(batch,{'domain':'illustration'},{'assets':[]},decision,REGISTRY)
        self.assertEqual(sum('PROFESSIONAL_DECISION_MISSING' in x for x in errors),6)

if __name__ == '__main__':
    unittest.main(verbosity=2)
