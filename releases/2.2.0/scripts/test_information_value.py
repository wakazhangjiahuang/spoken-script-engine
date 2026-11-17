import unittest,copy
from test_pipeline import fixture
from illustration_contract import active,intake_errors,plan_errors,draft_errors,review_errors
from retrieve_assets import ROOT,pack
from execution_contract import check_plan
class InformationValueTests(unittest.TestCase):
 def brief(self):
  b,_=fixture();b=b['brief'];b.update(domain='illustration',audience_information={'primary_role':'designer','current_problem':'不知产品应用','direct_benefit':'美国浴巾项目的用途与渠道','information_type':'user_project','source_class':'user_project'},case_ids=['ILL:PROJECT:US-BABY-TOWEL-300']);b['facts']=[{'id':'F1','text':'美国母婴品牌','source':'用户陈述','status':'provided','evidence_class':'user_project','anchor_terms':['美国']},{'id':'F2','text':'Instagram','source':'用户陈述','status':'provided','evidence_class':'user_project','anchor_terms':['Instagram']}];return b
 def test_generic_route_unchanged(self):
  b,_=fixture();o=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertIsNone(o['domain_profile'])
 def test_profile_actual_text_loaded(self):
  o=pack(ROOT/'assets/kb-snapshot',self.brief());self.assertIn('核心痛点',o['must_read_guidance']['domains/illustration/standard-v0.2.md']['text'])
 def test_five_opening_sources_not_false_real_cases(self):
  o=pack(ROOT/'assets/kb-snapshot',self.brief());r=[a for a in o['assets'] if a['record'].get('type')=='domain_opening_reference'];self.assertEqual(len(r),5);self.assertTrue(all(a['record']['sample_scope']=='opening_and_value_brief' for a in r))
 def test_illustration_alias_loads_full_design_examples(self):
  o=pack(ROOT/'assets/kb-snapshot',self.brief());self.assertEqual(o['coverage']['douyin']['approved_editorial_examples_selected'],6)
 def test_user_reported_is_not_verified(self):
  o=pack(ROOT/'assets/kb-snapshot',self.brief());self.assertEqual(o['domain_case_coverage']['independently_verified'],0);self.assertEqual(o['domain_case_coverage']['explicitly_selected'],1)
 def test_no_case_injection_without_selection(self):
  b=self.brief();b.pop('case_ids');o=pack(ROOT/'assets/kb-snapshot',b);self.assertEqual(o['domain_case_coverage']['explicitly_selected'],0);self.assertFalse(any(a['record'].get('type')=='user_reported_project' for a in o['assets']))
 def test_missing_audience_contract_rejected(self):
  b=self.brief();b.pop('audience_information');self.assertTrue(intake_errors(b))
 def test_no_unrequested_tool_tutorial(self):
  b=self.brief();b['audience_information']['information_type']='explicit_technical_tutorial';self.assertIn('explicitly requested',str(intake_errors(b)))
 def test_current_user_project_may_stay_provided(self):
  self.assertFalse(intake_errors(self.brief()))
 def test_example_cannot_become_user_project(self):
  b=self.brief()
  for f in b['facts']:f['evidence_class']='historical_example'
  self.assertIn('current user-project facts',str(intake_errors(b)))
 def script(self):
  b,r=fixture();s=b['scripts'][0];s['segments'][0]['text']='美国品牌买什么图？';s['segments'][1]['text']='通过Instagram询盘，做秋冬浴巾。';s['information_delivery']={'primary_role':'designer','source_class':'user_project','tool_position':'support','opening_benefit':{'segment_id':'S0','quote':s['segments'][0]['text']},'new_fact':{'segment_id':'S1','quote':s['segments'][1]['text']},'viewer_use':{'segment_id':'S4','quote':s['segments'][4]['text']},'opening_fact_ids':['F1'],'new_fact_ids':['F2']};p={'information_contract':{k:s['information_delivery'][k] for k in ('primary_role','source_class','tool_position')}};return s,p
 def test_real_new_fact_anchors_pass(self):
  s,p=self.script();self.assertFalse(draft_errors(s,p,{'domain_profile':True},self.brief()))
 def test_repeating_same_fact_ids_rejected(self):
  s,p=self.script();s['information_delivery']['new_fact_ids']=['F1'];self.assertIn('no new fact',str(draft_errors(s,p,{'domain_profile':True},self.brief())))
 def test_second_fact_must_be_in_second_sentence(self):
  s,p=self.script();s['segments'][1]['text']='这一单很有意思。';s['information_delivery']['new_fact']['quote']=s['segments'][1]['text'];self.assertIn('new fact not in second',str(draft_errors(s,p,{'domain_profile':True},self.brief())))
 def test_notes_do_not_supply_spoken_value(self):
  s,p=self.script();s['information_delivery']['opening_benefit']={'segment_id':'S0','surface':'visual','quote':s['segments'][0]['visual']};self.assertIn('must be spoken',str(draft_errors(s,p,{'domain_profile':True},self.brief())))
 def test_independent_information_review_required(self):
  s,p=self.script();self.assertTrue(review_errors({},[s],{'domain_profile':True}))
 def test_blind_projection_removes_producer_scores(self):
  from prepare_review import clean
  value={'selected':[{'selection_scores':{'a':4},'asset_id':'keep'}],'content':{'内部评分':90,'正文':'保留正文'}}
  self.assertEqual(clean(value),{'selected':[{'asset_id':'keep'}],'content':{'正文':'保留正文'}})
 def test_rejected_artifact_cannot_be_prepared_for_review(self):
  import tempfile,json
  from pathlib import Path
  from test_pipeline import prepare_run
  from prepare_review import prepare
  with tempfile.TemporaryDirectory() as tmp:
   b,_=fixture();run=Path(tmp)/'run';batch=prepare_run(run,b)
   changed=json.loads(batch.read_text());changed['scripts'][0]['composition']['hook_slots'][0]['segment_id']='S5';batch.write_text(json.dumps(changed,ensure_ascii=False))
   with self.assertRaisesRegex(ValueError,'structurally rejected or unbound'):prepare(run,batch)
 def test_explicit_tutorial_still_needs_visible_test(self):
  b=self.brief();b['audience_information']['information_type']='explicit_technical_tutorial';b['explicit_technical_tutorial']=True;self.assertIn('visible demonstration',str(intake_errors(b)))
 def test_information_review_cannot_use_visual_in_place_of_speech(self):
  s,p=self.script();rows={k:{'passed':True,'segment_id':'S0','quote':s['segments'][0]['visual'],'surface':'visual','reason':'构造反例'} for k in ('opening_value','new_fact','story_decision','viewer_use','calling_input')}
  self.assertIn('must quote speech',str(review_errors({'information_checks':[{'script_id':s['id'],**rows}]},[s],{'domain_profile':True})))
 def test_rubric_keeps_original_weights(self):
  import json
  q=json.loads((ROOT/'assets/kb-snapshot/rubrics/quality.json').read_text());self.assertEqual([x['weight'] for x in q['dimensions']],[15,15,25,15,15,15])
if __name__=='__main__':unittest.main(verbosity=2)
