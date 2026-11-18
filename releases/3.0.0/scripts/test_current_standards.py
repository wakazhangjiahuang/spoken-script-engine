"""Current-source replacement and actual deliverable regressions, not persuasion scores."""
import unittest,json,tempfile,shutil,copy
from pathlib import Path
from retrieve_assets import ROOT,pack,verified
from test_pipeline import fixture,prepare_run
from surface_contract import output_errors,visible_count,promised_item_errors,plan_errors
from export_xlsx import build
from openpyxl import load_workbook
class CurrentStandards(unittest.TestCase):
 def test_all_current_nonempty_cells_have_unique_treatment(self):
  p=ROOT/'assets/kb-snapshot/standards/20261118';data=json.loads((p/'cell-treatment.json').read_text());self.assertEqual(len(data),1229);self.assertEqual(len({r['locator'] for r in data}),1229)
 def test_current_18_scripts_and_15_separate_covers(self):
  k=ROOT/'assets/kb-snapshot';rows=[json.loads(x) for p in ['xiaohongshu','douyin','channels'] for x in (k/f'platforms/{p}/current-examples.jsonl').read_text().splitlines()];self.assertEqual(len(rows),18);self.assertEqual(sum(len(x['shots']) for x in rows),108);self.assertEqual(sum(x['latest_cover'] is not None for x in rows),15)
 def test_retired_snapshot_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'KB-MANIFEST.json').write_text(json.dumps({'version':'2.3.0','assets':[]}));self.assertRaises(ValueError,verified,p)
 def test_unlisted_old_example_cannot_sneak_in(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'kb';shutil.copytree(ROOT/'assets/kb-snapshot',p);(p/'old-approved.jsonl').write_text('old');self.assertRaisesRegex(ValueError,'unlisted or retired',verified,p)
 def test_non_illustration_gets_no_domain_samples_or_titles(self):
  b,_=fixture();b['brief'].update(domain='tourism',topic='摄影取景选择');p=pack(ROOT/'assets/kb-snapshot',b['brief']);self.assertIsNone(p['domain_profile']);self.assertEqual(p['title_source_fragments'],[]);self.assertFalse(any(x['record'].get('domain')=='illustration' for x in p['assets']));self.assertEqual(len([x for x in p['assets'] if x['record'].get('type')=='attention_gene']),9)
 def test_generic_design_service_is_not_automatically_illustration(self):
  b,_=fixture();b['brief'].update(domain='design_service',topic='建筑空间设计');self.assertIsNone(pack(ROOT/'assets/kb-snapshot',b['brief'])['domain_profile'])
 def test_cover_mapping_uses_actual_mechanism_not_round_robin(self):
  p=ROOT/'assets/kb-snapshot/sources/current-title-map.jsonl';d={x['title_id']:x for x in map(json.loads,p.read_text().splitlines())};self.assertEqual(d['COVER:WX-AC02']['hook_id'],'SHARED:H315');self.assertEqual(d['COVER:DY-AC03']['gene_id'],'G04')
 def test_composite_emoji_counts_as_one_visible_character(self):self.assertEqual(visible_count('👨‍👩‍👧‍👦'),1);self.assertEqual(visible_count('A B\n字'),4)
 def test_locked_overlength_kept_only_with_exact_exception(self):
  b,_=fixture();s=b['scripts'][0];s['cover_main']='这是一个需要保留的超长主标题原文';self.assertTrue(output_errors(s,b['brief']));b['brief']['copy_locks']=[{'plan_id':s['plan_id'],'source':'explicit-user-lock','cover_main':s['cover_main'],'allow_overlength':True}];self.assertFalse(output_errors(s,b['brief']));s['cover_main']+='改';self.assertTrue(output_errors(s,b['brief']))
 def test_top5_cannot_be_served_by_two_products(self):
  b,_=fixture();s=b['scripts'][0];s['cover_sub']='TOP 5 Style';s['content_items']=[{'label':'A'},{'label':'B'}];self.assertIn('not actually delivered',str(promised_item_errors(s)))
 def test_top_collection_requires_distinct_bound_items(self):
  b,_=fixture();s=b['scripts'][0];s['cover_sub']='TOP 2';s['content_items']=[{'label':'A','segment_id':'S3','quote':s['segments'][3]['text']},{'label':'B','segment_id':'S4','quote':s['segments'][4]['text']}];self.assertEqual(promised_item_errors(s),[]);s['content_items'][1]['label']='A';self.assertTrue(promised_item_errors(s))
 def test_disabled_comment_is_not_added_to_speech(self):
  with tempfile.TemporaryDirectory() as t:
   b,r=fixture();s=b['scripts'][0];s['comment_hook'].update(placement='disabled',line='本篇主动作是收藏，不启用评论请求');out=Path(t)/'x.xlsx';build(b,r,out,ROOT/'assets/kb-snapshot',{'editorial_status':'REVIEWED','publication_status':'NOT_READY'});w=load_workbook(out);row=list(w)[1][3];self.assertTrue(row[9].value.startswith('不并行启用'));self.assertNotIn('不启用评论',row[16].value);w.close()
 def test_same_version_rehashed_old_cache_cannot_self_approve(self):
  import hashlib
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'kb';shutil.copytree(ROOT/'assets/kb-snapshot',p);policy=json.loads((p/'release-policy.json').read_text());policy['active_source_release']='retired';(p/'release-policy.json').write_text(json.dumps(policy));m=json.loads((p/'KB-MANIFEST.json').read_text());a=next(x for x in m['assets'] if x['path']=='release-policy.json');a['sha256']=hashlib.sha256((p/'release-policy.json').read_bytes()).hexdigest();(p/'KB-MANIFEST.json').write_text(json.dumps(m));self.assertRaisesRegex(ValueError,'trust mismatch',verified,p)
 def test_four_function_blocks_are_valid(self):
  from validate_batch import check_blocks
  b,_=fixture();s=b['scripts'][0];s['segments']=[s['segments'][i] for i in [0,1,3,5]];self.assertEqual(check_blocks(s,b['brief']),[])
 def test_locked_timing_exception_is_explicit_and_not_publish_ready(self):
  from validate_batch import check_blocks,publication_ready
  b,r=fixture();s=b['scripts'][0];s['segments'][0]['duration_seconds']=6;self.assertTrue(check_blocks(s,b['brief']));b['brief']['copy_locks']=[{'plan_id':s['plan_id'],'source':'explicit source','hook':s['segments'][0]['text'],'suspense':s['segments'][1]['text'],'allow_timing_overrun':True}];s['timing_exception_note']='锁定原文，预计超过编辑标签，待真人与用户确认';self.assertEqual(check_blocks(s,b['brief']),[]);self.assertFalse(publication_ready(b,r))
 def test_spoken_money_alias_does_not_change_the_amount(self):
  from composition_contract import money_alias
  self.assertEqual(money_alias('300刀'),money_alias('300美元'));self.assertNotEqual(money_alias('500刀'),money_alias('300美元'))
 def test_money_cannot_match_inside_a_larger_number_or_strip_decimal(self):
  from composition_contract import money_alias
  for claim,source in [('300刀','1300美元'),('500刀','1500美元'),('3.00美元','300美元'),('300万元','300美元')]:self.assertFalse(money_alias(claim)&money_alias(source))
  self.assertEqual(money_alias('300.00刀'),money_alias('300美元'))
 def test_cover_and_shot_execution_identity_survive_export(self):
  with tempfile.TemporaryDirectory() as t:
   b,r=fixture();s=b['scripts'][0];out=Path(t)/'x.xlsx';build(b,r,out,ROOT/'assets/kb-snapshot',{'editorial_status':'REVIEWED','publication_status':'NOT_READY'});w=load_workbook(out);cover=[row for row in w['00使用总览'].iter_rows(values_only=True) if row[0]==s['id']+'/封面'];self.assertEqual(cover[0][3],s['cover']+'\n全片视觉与封面安排：'+s['director_plan']['visual_premise']);self.assertIn(s['director_plan']['editing_rule'],cover[0][4]);shot=list(w)[-1];self.assertTrue(shot['D3'].value.startswith(s['segments'][0]['id']+'｜'));self.assertTrue(shot['H3'].value.startswith('素材ID：'+s['segments'][0]['shot']['material_id']+'｜'));w.close()
 def test_optional_numeric_scores_may_be_absent(self):
  from validate_batch import validate
  from execution_contract import digest
  b,r=fixture();r['items'][0].pop('scores')
  with tempfile.TemporaryDirectory() as t:
   d=Path(t)/'run';f=prepare_run(d,b);r.update(batch_sha256=digest(f),decision_sha256=digest(d/'decision.json'),asset_pack_sha256=digest(d/'asset-pack.json'));self.assertTrue(validate(b,r,digest(f),run_dir=d)['passed'])
if __name__=='__main__':unittest.main()
