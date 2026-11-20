"""Observed failure modes as contract tests; no synthetic review is quality evidence."""
import copy,json,tempfile,unittest
from pathlib import Path
from test_pipeline import fixture,prepare_run
from surface_contract import *
from prepare_review import prepare
from execution_contract import digest
from retrieve_assets import ROOT
from export_xlsx import build
from openpyxl import load_workbook
class SurfaceTests(unittest.TestCase):
 def candidates(self):
  b,_=fixture();b=b['brief'];b['facts']=[{'id':'F1','text':'示意中的商品','status':'provided','source':'test'}]
  c={'id':'A','plan_id':'douyin-0','platform':'douyin','mechanism_id':'SHARED:H301','cover_main':'具体应用结果','cover_sub':'明确案例及品类','hook':'图案用于哪种商品？','suspense':'本例是指定产品。','first_shot':{'visual':'指向具名商品与图案','material_id':'PHONE'},'proof_fact_ids':['F1']};alt=copy.deepcopy(c);alt.update(id='B',mechanism_id='SHARED:H312')
  rows=[]
  for q in (c,alt):rows.append({'candidate_id':q['id'],'verdict':'RECOMMEND_FOR_DRAFT','viewer_restatement':'仅合成结构测试','reason_to_watch':'合成测试','reason_to_continue':'合成测试','checks':{k:{'passed':True,'surface':'suspense' if k=='continuation' else 'hook','quote':q['suspense'] if k=='continuation' else q['hook'],'reason':'合成引用测试，不认证内容'} for k in OPENING_CHECKS}})
  plan={'opening_candidates':[c,alt],'opening_review':{'panel_sha256':canonical(first8_packet([c,alt],b)),'reviewer':{'independent':True,'identity':'synthetic-not-a-quality-review'},'items':rows},'selected':[{'id':'douyin-0','platform':'douyin','opening_candidate_id':'A','asset_refs':{'hook':{'asset_id':'SHARED:H301'}}}]};pack={'domain_profile':True,'assets':[{'asset_id':'SHARED:H301','source_path':'shared/spoken-hooks.jsonl'},{'asset_id':'SHARED:H312','source_path':'shared/spoken-hooks.jsonl'}]};return b,plan,pack
 def test_valid_bound_opening_handshake_can_proceed(self):
  b,p,k=self.candidates();self.assertEqual(plan_errors(p,b,k),[])
 def test_raw_panel_cannot_expose_producer_reason(self):
  b,p,_=self.candidates();p['opening_candidates'][0]['why_care']='hidden';p['opening_candidates'][0]['selection_scores']={'a':4};raw=json.dumps(first8_packet(p['opening_candidates'],b));self.assertNotIn('hidden',raw);self.assertNotIn('selection_scores',raw)
 def test_opening_must_be_reviewed_before_plan(self):
  b,p,k=self.candidates();p.pop('opening_review');self.assertIn('before plan',str(plan_errors(p,b,k)))
 def test_changed_first_screen_invalidates_judgement(self):
  b,p,k=self.candidates();p['opening_candidates'][0]['hook']='已改过的首句';self.assertIn('not bound',str(plan_errors(p,b,k)))
 def test_body_cannot_repair_relevance_in_first_sentence(self):
  b,p,k=self.candidates();p['opening_review']['items'][0]['checks']['self_relevance']['surface']='first_shot';self.assertIn('actual first spoken',str(plan_errors(p,b,k)))
 def test_declared_opportunity_veto_cannot_be_offset_by_scores(self):
  b,p,k=self.candidates();p['selection_scores']={'all':4};p['opening_review']['items'][0]['checks']['task_value']['passed']=False;self.assertIn('first8 rejected task_value',str(plan_errors(p,b,k)))
 def test_cover_fields_do_not_alias_publish_title(self):
  b,_=fixture();s=b['scripts'][0];s.pop('cover_sub');self.assertIn('publish title is not',str(draft_errors(s)))
 def test_identical_main_and_sub_rejected(self):
  b,_=fixture();s=b['scripts'][0];s['cover_sub']=s['cover_main'];self.assertIn('merely duplicate',str(draft_errors(s)))
 def test_comment_keeps_the_business_intent(self):
  b,_=fixture();s=b['scripts'][0];s['comment_hook']['intent']='purchase';self.assertIn('changed business intent',str(draft_errors(s)))
 def test_content_packet_hides_plan_and_producer_payoff(self):
  with tempfile.TemporaryDirectory() as d:
   b,_=fixture();p=Path(d)/'run';f=prepare_run(p,b);r=prepare(p,f);self.assertNotIn('plan',r);self.assertNotIn('asset_pack',r);self.assertNotIn('selected_reason',json.dumps(r['deliverables']));self.assertEqual(r['phase'],'content')
 def test_fidelity_cannot_precede_content_judgement(self):
  with tempfile.TemporaryDirectory() as d:
   b,_=fixture();p=Path(d)/'run';f=prepare_run(p,b)
   with self.assertRaisesRegex(ValueError,'before revealing'):prepare(p,f,'fidelity')
 def test_platform_adaptation_does_not_force_different_viewer_benefits(self):
  from composition_contract import diversity_errors
  b,_=fixture(('xiaohongshu','douyin'));a,c=b['scripts'];c['segments']=copy.deepcopy(a['segments']);c['segments'][0]['visual']='同案不同首镜编排';self.assertEqual(diversity_errors([a,c]),[])
 def test_cover_sub_and_comment_survive_real_xlsx_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   b,r=fixture();s=b['scripts'][0];s['title']='这是独立发布标题';s['cover_sub']='这是封面专用副标题';s['comment_hook']['line']='这是独立置顶评论';s['comment_hook']['placement']='pinned_comment';out=Path(d)/'roundtrip.xlsx';build(b,r,out,ROOT/'assets/kb-snapshot',{'editorial_status':'REVIEWED','publication_status':'NOT_READY'});w=load_workbook(out);row=list(w)[1][3];self.assertEqual(row[4].value,'这是封面专用副标题');self.assertEqual(row[9].value,'这是独立置顶评论');self.assertNotIn('这是独立置顶评论',row[16].value);w.close()
if __name__=='__main__':unittest.main(verbosity=2)
