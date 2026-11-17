"""Contract regression fixtures; scores are synthetic, not independent content assessment."""
import copy,hashlib,itertools,json,tempfile,time,unittest,shutil
from pathlib import Path
from validate_batch import validate,DIMS
from retrieve_assets import pack,verified,ROOT
from sync_memory import enqueue,acknowledge,write_plan

def fixture(platforms=('douyin',),count=1):
 brief={'content_task':'diagnosis','objective':'education','input_resolution':['显式合成夹具，无质量认证'],'task_id':'contract-fixture','topic':'示例任务','audience':'小团队','goal':'理解检查方法','platforms':list(platforms),'facts':[],
  'content_context':{'scene':'桌面','problem':'缺字段','memory_point':'先确认','content_type':'教程'},'voice_profile':'普通解释',
  'production_resources':[{'id':'PHONE','description':'手机固定机位','status':'available'}],'count_per_platform':{p:count for p in platforms},'duration_limit_seconds':60,'speech_chars_per_second':4.2}
 scripts=[]
 for plat in platforms:
  for i in range(count):
   sid=f'{plat}-{i}';texts=['先检查这张表。','缺的是数据，还是判断标准？',f'这是{plat}的示例第{i+1}步。',['空白格先标待确认，再按来源核对。','先把公斤和吨分列，再确认是否允许换算。','重复记录先比编号，不按名称直接删除。','把负责人和截止日分开核对，缺少一项就标出来。','流程状态与完成日期分别保留，避免提前结项。','把异常金额单列复核，普通条目继续处理。'][i%6]+({'xiaohongshu':'先留可复查的原始列。','douyin':'当场圈出一行演示。','channels':'交接时把核对责任写清。'}[plat]),['下次交表先检查来源和状态。','汇总前先确认单位口径。','去重时先确定唯一记录编号。','排期先补责任人和期限。','结项前检查日期是否有据。','先核对异常，再合并总表。'][i%6],'你最常缺哪一列？']
   segs=[{'id':f'S{j}','duration_seconds':[3,5,8,10,8,6][j],'role':['hook','suspense','context','judgment','value','calling'][j],'purpose':['停留','悬念','背景','判断','价值','行动'][j],'text':t,'visual':'手机固定，对镜指向示意表','subtitle':'待确认',
    'shot':{'framing':'中近景','camera':'固定手机','action':'指向表格空白格','material_id':'PHONE','edit_cue':'同机位，不切','sound':'人声','subtitle_focus':'待确认','silent_hold_seconds':0}} for j,t in enumerate(texts)]
   scripts.append({'id':sid,'platform':plat,'topic':brief['topic'],'audience':brief['audience'],'funnel_stage':'认知','decision_stage':'认知','positioning':'示例说明',
    'angle':{'problem':f'问题{i}','benefit':f'判断{i}','proof_organization':f'顺序{i}'},'formula_id':f'SHARED:F{[2,5,11,2][i%4]:02d}','hook_id':'SHARED:H301',
    'title':'检查表格','cover':'先看缺项','publish_description':'建议流程示例','keywords':['任务表'],'segments':segs,'claim_links':[],'unverified_claims':[],
    'selected_reason':'对应本任务','value_translation':'知道哪一格需要核对','hook_plan':{'alternate_hook_id':'SHARED:H302','alternate_text':'表里这一格空着。','stop_reason':'相关任务','continue_reason':'给检查方法','promise':'检查缺项','payoff_segment_id':'S3','selection_reason':'可展示'},
    'calling':{'kind':'question','line':texts[-1],'viewer_reason':'分享常见缺项','comment_signal':'缺失列名','next_topic':'核对该列'},
    'director_plan':{'format':'对镜','visual_premise':'表格','performance_note':'自然解释','continuity':'保持表格状态','editing_rule':'判断变化才切','fallback':'无表格时用空白纸写字段','shoot_order':['S0','S1','S2','S3','S4','S5']}})
 batch={'engine_version':'2.1.0','performance_status':'NOT_RUN','brief':brief,'scripts':scripts}
 items=[]
 for s in scripts:
  anchor={'segment_id':'S1','quote':s['segments'][1]['text'],'reason':'合成结构夹具，不认证内容质量'}
  items.append({'script_id':s['id'],'gates_passed':True,'issues':[],'scores':{d:{'score':4,'segment_id':'S'+str({'hook_strength':0,'suspense':1,'professional_judgment':3,'aesthetic_expression':3,'buyer_value':4,'cta_persuasion':5}[d]),'quote':s['segments'][{'hook_strength':0,'suspense':1,'professional_judgment':3,'aesthetic_expression':3,'buyer_value':4,'cta_persuasion':5}[d]]['text'],'reason':'合成合同测试，不认证质量'} for d in DIMS},'gate_checks':{d:{'passed':True,**anchor} for d in ['facts','promise_payoff','proof','platform','marketing','human_voice','direction']}})
 review={'batch_sha256':'0'*64,'reviewer':{'identity':'synthetic-test-fixture','mode':'isolated_review','independent':True},'items':items,
  'diversity':[{'platform':p,'a':a['id'],'b':b['id'],'real_difference_passed':True,'reason':'合成夹具字段不同'} for p in platforms for a,b in itertools.combinations([s for s in scripts if s['platform']==p],2)],
  'cross_platform':[{'platform_a':a,'platform_b':b,'real_difference_passed':True,'reason':'合成夹具检查配对'} for a,b in itertools.combinations(platforms,2)],
  'platform_checks':[{'platform':p,'status':'PARTIAL','source_urls':[],'checked_at':'2026-11-04','scope':'仅保守草稿','restrictions':['发布前核验'],'publish_ready':False} for p in platforms]}
 for script in scripts:
  script['plan_id']=script['id'];script['calling'].update(intent='education',qualification='示例输入',next_step='检查示例')
  script['asset_applications']=[{'role':role,'asset_id':asset,'segment_id':g['id'],'quote':g['text'],'transformation':'合成合同夹具，不证明使用质量'} for role,asset,g in [('hook',script['hook_id'],script['segments'][0]),('body',script['formula_id'],script['segments'][3]),('calling','SHARED:CTA:01',script['segments'][-1])]]
 review['commercial_checks']=[{'script_id':s['id'],'buyer_decision':'合成字段测试','payoff_quote':s['segments'][1]['text'],'contact_reason':'不用于质量判断','passes':True} for s in scripts]
 review['asset_checks']=[{'script_id':s['id'],'application_is_substantive':True,'reason':'合成声明，仅检验合同，不认证内容'} for s in scripts]
 review['decision_sha256']='0'*64;review['asset_pack_sha256']='0'*64
 review['composition_checks']=[{'script_id':s['id'],**{k:{'passed':True,'segment_id':'S3','quote':s['segments'][3]['text'],'reason':'仅合成字段测试，不认证语义'} for k in ('audience_payoff','source_fidelity','action_motive','fact_scope')},'source_comparison':{'asset_id':s['formula_id'],'source_quote':next(a['record']['structure'] for a in pack(ROOT/'assets/kb-snapshot',brief)['assets'] if a['asset_id']==s['formula_id']),'deviation_judgment':'仅合成结构测试'}} for s in scripts]
 review['review_limitations']='合成自写review，不是独立评审或质量证据'
 return batch,review

from execution_contract import fresh,event,digest,check_plan,provenance

def prepare_run(path,batch):
 path.mkdir();fresh(path/'brief.json',batch['brief']);assets=pack(ROOT/'assets/kb-snapshot',batch['brief']);fresh(path/'asset-pack.json',assets);shutil.copytree(ROOT/'assets/kb-snapshot',path/'knowledge');(path/'sources').mkdir();(path/'sources/01.txt').write_text('Synthetic request fixture, not a real customer case');fresh(path/'source-manifest.json',{'original_request_captured':True,'attachments_captured':0,'sources':[{'original_name':'request.txt','stored_path':'sources/01.txt','sha256':digest(path/'sources/01.txt')}],'kb_manifest_sha256':digest(path/'knowledge/KB-MANIFEST.json')});event(path,'intake',['brief.json','asset-pack.json','source-manifest.json','sources/01.txt']);pool={x['asset_id']:x for x in assets['assets']};selected=[]
 for s in batch['scripts']:
  platform=next(x for x in assets['assets'] if x['source_path'].startswith('platforms/'+s['platform']+'/') and x['record'].get('type')=='platform_routing')
  refs={role:{'asset_id':ident,'record_sha256':pool[ident]['record_sha256'],'why':'合成合同夹具'} for role,ident in [('hook',s['hook_id']),('body',s['formula_id']),('calling','SHARED:CTA:01'),('platform',platform['asset_id'])]}
  selected.append({'id':s['plan_id'],'platform':s['platform'],'objective':batch['brief']['objective'],**{k:'合成合同字段，不认证质量' for k in ['buyer_decision','tension','stakes','intervention','proof','payoff','cta_reason','qualification','next_step']},'asset_refs':refs,'selection_scores':{d:{'score':4,'reason':'合成合同测试'} for d in ['audience_relevance','evidence_fit','platform_fit','action_fit']}})
 plan={'selected':selected,'rejected':[{'platform':p,'reason':'合成弃选依据','selection_scores':{d:{'score':2,'reason':'合成弃选条件'} for d in ['audience_relevance','evidence_fit','platform_fit','action_fit']}} for p in batch['brief']['platforms']]};augment_composition_fixture(plan,batch,assets);assert not check_plan(plan,batch['brief'],assets);fresh(path/'decision.json',plan);event(path,'plan',['decision.json']);fresh(path/'batch-v1.json',batch);event(path,'draft',['batch-v1.json']);return path/'batch-v1.json'


def augment_composition_fixture(plan,batch,assets):
 from composition_contract import slots,beats,speech_example
 pool={a['asset_id']:a for a in assets['assets']}
 for p,s in zip(plan['selected'],batch['scripts']):
  h=pool[p['asset_refs']['hook']['asset_id']]['record'];b=pool[p['asset_refs']['body']['asset_id']]['record'];c=pool[p['asset_refs']['calling']['asset_id']]['record'];example=pool['STRUCTURE:OUTCOME-NEED-METHOD-TRANSFER-ACTION']
  p['audience_contract']={'question':'检查缺项','payoff':'核对来源和状态','motivation':'仅合成测试','route':'教程','primary_action':'comment','action_reason':'合成结构测试'}
  ts=assets['title_candidates_by_hook'].get(p['asset_refs']['hook']['asset_id'],[])
  title={'status':'matched','title_id':ts[0]['mapping']['title_id'],'source_line':ts[0]['mapping']['source_line'],'original_line':ts[0]['original_line'],'retained':'合成测试','discarded':'合成测试'} if ts else {'status':'no_match','reason':'没有标题原行'}
  p['source_recipe']={'hook_template':h['spoken_structure'],'body_structure':b['structure'],'calling_template':c['pattern'],'example':{'asset_id':example['asset_id'],'record_sha256':example['record_sha256'],'source_quote':speech_example(example['record']).splitlines()[0],'match_level':'structure_only','transfer':'只测引用字段','non_transfer':'所有案例事实','mismatch':'合成测试不是内容生产'},'title':title};p['proof_basis']=[]
  s['composition']={'audience_question':p['audience_contract']['question'],'primary_action':'comment','hook_slots':[{'slot':slot,'segment_id':'S0','quote':s['segments'][0]['text']} for slot in slots(h)],'body_beats':[{'beat':beat,'segment_id':'S3','quote':s['segments'][3]['text']} for beat in beats(b)],'payoff':{'segment_id':'S3','quote':s['segments'][3]['text']},'takeaway':{'segment_id':'S4','quote':s['segments'][4]['text']},'calling':{'segment_id':'S5','quote':s['segments'][5]['text']}}

class PipelineTest(unittest.TestCase):
 def setUp(self):self.b,self.r=fixture()
 def evaluate(self,b=None,r=None):
  b=b or self.b;r=r or self.r
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'run';file=prepare_run(path,b);r['batch_sha256']=digest(file);r['decision_sha256']=digest(path/'decision.json');r['asset_pack_sha256']=digest(path/'asset-pack.json');return validate(b,r,digest(file),run_dir=path)
 def reject(self,mutate,needle):
  mutate(self.b,self.r);v=self.evaluate();self.assertFalse(v['passed'],v);self.assertTrue(any(needle in x for x in v['errors']),v)
 def test_valid_structural_fixture(self):self.assertTrue(self.evaluate()['passed'])
 def test_missing_run_rejected(self):self.assertIn('recorded pre-draft',str(validate(self.b,self.r,'a'*64)))
 def test_failed_commercial_review(self):self.reject(lambda b,r:r['commercial_checks'][0].update(passes=False),'commercial editorial')
 def test_nominal_asset_application(self):self.reject(lambda b,r:r['asset_checks'][0].update(application_is_substantive=False),'nominally')
 def test_low_buyer_value(self):self.reject(lambda b,r:r['items'][0]['scores']['buyer_value'].update(score=2),'low dimension buyer_value')
 def test_low_cta(self):self.reject(lambda b,r:r['items'][0]['scores']['cta_persuasion'].update(score=2),'low dimension cta_persuasion')
 def test_bad_payoff_quote(self):self.reject(lambda b,r:r['commercial_checks'][0].update(payoff_quote='不存在'),'payoff quote')
 def test_missing_review(self):self.assertFalse(validate(self.b,None,'a'*64)['passed'])
 def test_bad_rule_source(self):self.reject(lambda b,r:r['platform_checks'][0].update(status='VERIFIED',source_urls=['https://example.org/'],publish_ready=True),'official platform host')
 def test_partial_not_ready(self):self.reject(lambda b,r:r['platform_checks'][0].update(publish_ready=True),'partial platform')
 def test_bad_rule_date(self):self.reject(lambda b,r:r['platform_checks'][0].update(checked_at='0000-99-99'),'invalid platform check')
 def test_quote_mismatch(self):self.reject(lambda b,r:r['items'][0]['gate_checks']['marketing'].update(quote='不存在'),'gate quote')
 def test_unknown_material(self):self.reject(lambda b,r:b['scripts'][0]['segments'][0]['shot'].update(material_id='missing'),'unknown shot')
 def test_silent_time(self):self.reject(lambda b,r:b['scripts'][0]['segments'][0]['shot'].update(silent_hold_seconds=12),'insufficient read time')
 def test_wrong_calling_intent(self):self.reject(lambda b,r:b['scripts'][0]['calling'].update(intent='inquiry'),'Calling changed objective')
 def test_application_quote(self):self.reject(lambda b,r:b['scripts'][0]['asset_applications'][0].update(quote='不存在'),'unbound asset')
 def test_tampered_plan(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)/'run';p=prepare_run(r,self.b);x=json.loads((r/'decision.json').read_text());x['selected'][0]['objective']='inquiry';(r/'decision.json').write_text(json.dumps(x));self.assertIn('modified stage artifact decision.json',provenance(r,p))
 def test_stale_review(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)/'run';p=prepare_run(r,self.b);self.assertIn('review not bound',str(validate(self.b,self.r,digest(p),run_dir=r)))
 def test_draft_before_plan_cli(self):
  import subprocess
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);fresh(p/'batch.json',self.b);res=subprocess.run([__import__('sys').executable,str(ROOT/'scripts/run_pipeline.py'),'draft','--run',str(p),'--input',str(p/'batch.json')],capture_output=True,text=True);self.assertNotEqual(res.returncode,0);self.assertIn('seal plan',res.stderr)
 def test_retrieval_coverage_and_empty_cases(self):
  out=pack(ROOT/'assets/kb-snapshot',self.b['brief']);paths={x['source_path'] for x in out['assets']};self.assertIn('platforms/douyin/hooks.jsonl',paths);self.assertIn('platforms/douyin/formula-applications.jsonl',paths);self.assertEqual(out['coverage']['douyin']['real_cases'],0);self.assertLess(len(out['assets']),100)
 def test_intent_changes_retrieval(self):
  a=pack(ROOT/'assets/kb-snapshot',self.b['brief']);b=copy.deepcopy(self.b['brief']);b['objective']='inquiry';c=pack(ROOT/'assets/kb-snapshot',b);self.assertNotEqual([x['asset_id'] for x in a['assets']],[x['asset_id'] for x in c['assets']]);self.assertIn('SHARED:CTA:09',[x['asset_id'] for x in c['assets']])
 def test_snapshot_corrupt(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'file').write_text('bad');fresh(p/'KB-MANIFEST.json',{'assets':[{'path':'file','sha256':'0'*64}]})
   with self.assertRaises(ValueError):verified(p)
 def test_rubric_schema_parity(self):
  d=json.loads((ROOT/'schemas/review.schema.json').read_text());self.assertEqual(d['properties']['items']['items']['properties']['scores']['required'],DIMS)
 def test_locked_structure_two_distinct_tasks(self):
  b,r=fixture(count=2);b['brief']['formula_lock']='SHARED:F02';s=b['scripts'][1];s['formula_id']='SHARED:F02';s['asset_applications'][1]['asset_id']='SHARED:F02';r['composition_checks'][1]['source_comparison'].update(asset_id='SHARED:F02',source_quote='症状→判据→行动→复测');self.assertTrue(self.evaluate(b,r)['passed'])
 def test_phone_is_not_proof(self):self.assertFalse(pack(ROOT/'assets/kb-snapshot',self.b['brief'])['retrieval_stats']['evidence_available'])
 def test_purchase_cta(self):
  b=copy.deepcopy(self.b['brief']);b['objective']='purchase';self.assertIn('SHARED:CTA:10',[x['asset_id'] for x in pack(ROOT/'assets/kb-snapshot',b)['assets']])
 def test_batch_object_matches_bytes(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d)/'run';p=prepare_run(r,self.b);self.b['scripts'][0]['title']='changed outside accepted file';self.assertIn('batch object differs',str(validate(self.b,self.r,digest(p),run_dir=r)))

 def test_unrelated_domain_gets_no_example(self):
  b=copy.deepcopy(self.b['brief']);b['topic']='门店预约规则';o=pack(ROOT/'assets/kb-snapshot',b);self.assertEqual(o['coverage']['douyin']['constructed_examples_selected'],0)
 def test_ai_illustration_keeps_design_domain(self):
  b=copy.deepcopy(self.b['brief']);b['topic']='AI母婴印花';o=pack(ROOT/'assets/kb-snapshot',b);self.assertEqual([x['record']['domain'] for x in o['assets'] if x['record'].get('type')=='constructed_worked_example'],['design_service'])

 def test_memory_idempotent(self):
  with tempfile.TemporaryDirectory() as d:
   e={'task_id':'t','source_hash':'a','result_version':'1.6.0','brand_scope':'b','feedback':'用户明确修改'};q=Path(d)/'queue';self.assertFalse(enqueue(e,q)['duplicate']);self.assertTrue(enqueue(e,q)['duplicate'])

if __name__=='__main__':unittest.main(verbosity=2)
