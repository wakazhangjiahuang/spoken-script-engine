import unittest,copy,tempfile,json
from pathlib import Path
from test_pipeline import fixture,prepare_run
from execution_contract import read,check_plan,digest,provenance
from retrieve_assets import ROOT,pack
from composition_contract import text_errors,diversity_errors,plan_errors,draft_errors,review_errors
from validate_batch import validate
class CompositionTests(unittest.TestCase):
 def case(self):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);b,r=fixture();p=Path(d.name)/'run';f=prepare_run(p,b);return b,r,p,read(p/'decision.json'),read(p/'asset-pack.json')
 def test_required_guidance_actually_loaded(self):
  b,_=fixture();p=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertIn('用户利益',p['must_read_guidance']['shared/audience-value-translation.md']['text']);self.assertTrue(p['title_candidates_by_hook'])
 def test_every_eligible_hook_reachable(self):
  b,_=fixture();b['brief']['production_resources'][0]['evidence_role']='proof';p=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertEqual(len([a for a in p['assets'] if a['source_path']=='shared/spoken-hooks.jsonl']),17)
 def test_missing_recipe_cannot_seal(self):
  b,r,p,d,a=self.case();d['selected'][0].pop('source_recipe');self.assertTrue(check_plan(d,b['brief'],a))
 def test_formula_source_text_not_decorative(self):
  b,r,p,d,a=self.case();d['selected'][0]['source_recipe']['body_structure']='我说了专业判断';self.assertIn('source recipe mismatch body',str(check_plan(d,b['brief'],a)))
 def test_example_quote_must_exist(self):
  b,r,p,d,a=self.case();d['selected'][0]['source_recipe']['example']['source_quote']='不存在';self.assertIn('example source quote absent',str(check_plan(d,b['brief'],a)))
 def test_title_must_match_selected_mechanism(self):
  b,r,p,d,a=self.case();d['selected'][0]['source_recipe']['title']['original_line']='随便选一条爆款';self.assertIn('title source does not match',str(check_plan(d,b['brief'],a)))
 def test_body_cannot_omit_source_beats(self):
  b,r,p,d,a=self.case();b['scripts'][0]['composition']['body_beats'].pop();self.assertIn('incomplete source body_beats',str(draft_errors(b['scripts'][0],d['selected'][0],a,b['brief'])))
 def test_metadata_cannot_substitute_payoff(self):
  b,r,p,d,a=self.case();b['scripts'][0]['composition']['payoff']={'segment_id':'S3','surface':'visual','quote':b['scripts'][0]['segments'][3]['visual']};self.assertIn('cannot live only',str(draft_errors(b['scripts'][0],d['selected'][0],a,b['brief'])))
 def test_unlinked_earnings_fail(self):
  b,r,p,d,a=self.case();b['scripts'][0]['segments'][0]['text']='靠这套画风，我赚了500美刀！';self.assertIn('uncovered factual assertion',str(draft_errors(b['scripts'][0],d['selected'][0],a,b['brief'])))
 def test_chinese_earnings_need_source(self):
  b,r,p,d,a=self.case();b['scripts'][0]['segments'][3]['text']='这幅画到手五百刀。';self.assertIn('uncovered factual assertion',str(draft_errors(b['scripts'][0],d['selected'][0],a,b['brief'])))
 def test_disclaimer_does_not_fix_placeholder(self):
  b,r=fixture();b['scripts'][0]['segments'][3]['text']='【按真实过程补齐】客户付了钱';self.assertIn('placeholder',str(text_errors(b['scripts'][0])))
 def test_analyst_voice_rejected(self):
  b,r=fixture();b['scripts'][0]['segments'][3]['text']='我把这张上传的原稿当作观察样本';self.assertTrue(text_errors(b['scripts'][0]))
 def test_keyword_comment_not_default(self):
  b,r=fixture();b['scripts'][0]['segments'][-1]['text']='评论「接单」，我下一条就演示';self.assertIn('keyword bait',str(text_errors(b['scripts'][0])))
 def test_changed_angle_does_not_hide_same_body(self):
  b,r=fixture(count=2)
  for s in b['scripts']:
   s['segments'][3]['text']='先把作品对应到实际产品，再列产品用途和授权范围。'*8
  self.assertTrue(diversity_errors(b['scripts']))
 def test_close_word_swap_still_rejected(self):
  b,r=fixture(count=2)
  for s in b['scripts']:s['segments'][3]['text']='先把作品对应到实际产品，再列产品用途和授权范围。'*8
  b['scripts'][1]['segments'][3]['text']=b['scripts'][1]['segments'][3]['text'].replace('实际','具体');self.assertTrue(diversity_errors(b['scripts']))
 def test_real_body_difference_allowed(self):
  b,r=fixture(count=2);b['scripts'][0]['segments'][3]['text']='确定客户用途再决定授权范围。'*8;b['scripts'][1]['segments'][3]['text']='先画短线长线和转弯，检查笔压变化。'*8;self.assertEqual(diversity_errors(b['scripts']),[])
 def test_no_forced_formula_diversity(self):
  b,r,p,d,a=self.case();self.assertFalse(check_plan(d,b['brief'],a))
 def test_source_fidelity_review_missing_fails(self):
  b,r,p,d,a=self.case();r.pop('composition_checks');self.assertIn('missing source-fidelity',str(review_errors(r,b['scripts'],d,a)))
 def test_review_must_quote_actual_speech(self):
  b,r,p,d,a=self.case();r['composition_checks'][0]['action_motive']['quote']='编辑认为很好';self.assertIn('anchor absent',str(review_errors(r,b['scripts'],d,a)))
 def test_wrong_amount_not_supported_by_other_fact(self):
  b,r,p,d,a=self.case();b['brief']['facts']=[{'id':'F1','text':'金额300美元','status':'provided','source':'用户'}];b['scripts'][0]['segments'][3]['text']='我赚了500美元。';b['scripts'][0]['claim_links']=[{'segment_id':'S3','claim':'我赚了500美元。','evidence_id':'F1'}];self.assertIn('amount exceeds',str(draft_errors(b['scripts'][0],d['selected'][0],a,b['brief'])))
if __name__=='__main__':unittest.main(verbosity=2)
