#!/usr/bin/env python3
"""Current-release-only retrieval. Full source preservation; bounded task-local projections."""
import argparse,json,hashlib,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLATFORMS=('xiaohongshu','douyin','channels')
def load(p):return json.loads(Path(p).read_text())
def verified(root):
 root=Path(root).resolve();m=load(root/'KB-MANIFEST.json');seen=set()
 trust=load(ROOT/'assets/current-trust.json')
 if hashlib.sha256((root/'KB-MANIFEST.json').read_bytes()).hexdigest()!=trust['manifest_sha256']:raise ValueError('current engine manifest trust mismatch; cannot self-approve replacement cache')
 for a in m['assets']:
  if a['path'] in seen:raise ValueError('duplicate manifest path')
  seen.add(a['path']);p=(root/a['path']).resolve()
  if not p.is_relative_to(root):raise ValueError('unsafe manifest path')
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=a['sha256']:raise ValueError('hash mismatch: '+a['path'])
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='KB-MANIFEST.json'}
 if actual!=seen:raise ValueError('unlisted or retired files in current snapshot')
 required={'release-policy.json','asset-index.jsonl','standards/current-method.md','standards/20261118/source-audit.json','standards/20261118/source-manifest.json','standards/20261118/workbook-all-cells.json','standards/20261118/cell-treatment.json','shared/formulas.jsonl','shared/spoken-hooks.jsonl','shared/attention-genes.jsonl','shared/cta-comment-seeds.jsonl','shared/structure-references.jsonl','rubrics/quality.json','rubrics/selection.json','memory/events.jsonl'}
 required.update('platforms/'+p+'/current-examples.jsonl' for p in PLATFORMS)
 if not required<=seen:raise ValueError('manifest missing required runtime assets')
 policy=load(root/'release-policy.json')
 if policy.get('active_source_release')!=trust['source_release'] or policy.get('allowed_source_ids')!=['SRC'+str(i) for i in range(1,7)] or policy.get('sample_scope')!='illustration_only' or policy.get('version')!='3.0.0' or policy.get('old_examples_allowed') is not False or policy.get('legacy_fallback') is not False:raise ValueError('retired source release or legacy fallback is not permitted')
 idx=[json.loads(x) for x in (root/'asset-index.jsonl').read_text().splitlines() if x]
 if len(idx)!=len({x['path'] for x in idx}) or {x['path']:x['sha256'] for x in idx}!={x['path']:x['sha256'] for x in m['assets'] if x['path']!='asset-index.jsonl'}:raise ValueError('manifest/index mismatch')
 return m

def pack(root,brief):
 started=time.perf_counter();root=Path(root);m=verified(root);assets=[];coverage={};excluded=[]
 task=brief.get('content_task','diagnosis');objective=brief.get('objective','trust');context=brief.get('content_context',{})
 query=brief['topic']+brief['audience']+brief['goal']+json.dumps(context,ensure_ascii=False);q=re.sub(r'[^\w\u4e00-\u9fff]','',query);grams={q[i:i+2] for i in range(len(q)-1)}
 def jl(p):return [json.loads(x) for x in (root/p).read_text().splitlines() if x]
 def rank(rows):return sorted(rows,key=lambda a:(-sum(g in json.dumps(a,ensure_ascii=False) for g in grams),a.get('asset_id','')))
 def add(path,rows,why):
  for a in rows:assets.append({'asset_id':a.get('asset_id',a.get('id')),'source_path':path,'file_sha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'record_sha256':hashlib.sha256(json.dumps(a,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'match_reason':why,'ranking':{'semantic_match':'REQUIRES_EDITOR_DECISION','effectiveness':'NOT_RUN'},'record':a})
 available=any(x.get('status')=='available' and x.get('evidence_role') in ('proof','demonstration') for x in brief.get('production_resources',[]))
 families={'diagnosis':['F02','F01','F05','F11','F16'],'correction':['F12','F02','F11','F05'],'tutorial':['F03','F01','F18','F02'],'case':['F13','F15','F16','F10'],'comparison':['F04','F05','F11','F07'],'objection':['F06','F10','F11','F09'],'planning':['F05','F10','F16','F08'],'retention':['F18','F01','F06']}
 eligible=families.get(task,families['diagnosis'])[:]
 if objective in ('inquiry','purchase'):eligible+=['F07','F08','F06']
 if objective=='trust':eligible+=['F16','F11']
 if objective=='awareness':eligible+=['F09','F10']
 eligible=list(dict.fromkeys(eligible))
 lock=brief.get('formula_lock');allf=jl('shared/formulas.jsonl')
 if lock and lock not in {a['asset_id'] for a in allf}:raise ValueError('unknown locked formula')
 if lock:eligible=[lock.split(':')[-1]]
 for code in ['F03','F13','F14','F15','F16']:
  if code in eligible and not available:eligible.remove(code);excluded.append({'asset_id':'SHARED:'+code,'reason':'缺本次可用证明/演示素材，不以样例代替'})
 if lock and lock.split(':')[-1] not in eligible:raise ValueError('locked formula evidence unavailable; resolve input before intake')
 add('shared/formulas.jsonl',rank([a for a in allf if a['asset_id'].split(':')[-1] in eligible]),'共同任务/内容交付/证据先筛选，按需迁移结构')
 hs=[a for a in jl('shared/spoken-hooks.jsonl') if available or a['asset_id'] not in {'SHARED:H306','SHARED:H307','SHARED:H309','SHARED:H310','SHARED:H314','SHARED:H316'}]
 add('shared/spoken-hooks.jsonl',rank(hs),'当前表达机制；不把固定模板当好开场')
 ctas=jl('shared/cta-comment-seeds.jsonl');ids=['SHARED:CTA:04','SHARED:CTA:09'] if objective=='inquiry' else ['SHARED:CTA:10'] if objective=='purchase' else ['SHARED:CTA:01','SHARED:CTA:02','SHARED:CTA:03','SHARED:CTA:05','SHARED:CTA:06','SHARED:CTA:07','SHARED:CTA:08']
 add('shared/cta-comment-seeds.jsonl',[a for a in ctas if a['asset_id'] in ids],'动作服从本篇目的；自然交流可成立，咨询另核入口')
 for f in ['attention-genes','production-principles','source-excerpts','human-voice-patterns','structure-references']:add('shared/'+f+'.jsonl',jl('shared/'+f+'.jsonl'),'从本轮原件提炼的可迁移判断；非平台或效果认证')
 guidance={}
 def guide(path,text=None):guidance[path]={'source_path':path,'file_sha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'text':text if text is not None else (root/path).read_text()}
 for path in ['standards/current-method.md','shared/audience-value-translation.md','shared/creator-voice-profile.md','shared/human-voice.md']:guide(path)
 from illustration_contract import active
 ill=active(brief);profile=load(root/'domains/illustration/profile.json') if ill else None
 title_groups={a['asset_id']:[] for a in hs};title_lines=(root/'sources/current-cover-lines.txt').read_text().splitlines();maps=jl('sources/current-title-map.jsonl') if ill else []
 for a in maps:
  if a['hook_id'] in title_groups:title_groups[a['hook_id']].append({'mapping':a,'original_line':title_lines[a['source_line']-1],'status':'current_illustration_cover_only','topic_case_match':False})
 requested=set(brief.get('case_ids',[]));selected_count=0
 for p in brief['platforms']:
  if p not in PLATFORMS:raise ValueError('unsupported platform')
  for f in ['hooks','formula-applications','proofs','seo-keywords','entry-and-actions','routing']:
   rows=jl(f'platforms/{p}/{f}.jsonl')
   if f=='formula-applications':rows=[a for a in rows if a.get('formula_id','').split(':')[-1] in eligible]
   add(f'platforms/{p}/{f}.jsonl',rank(rows)[:18 if f=='formula-applications' else 3],'展示与节奏适配，不改变事实/共同任务，不是平台固定句式')
  allsamples=jl(f'platforms/{p}/current-examples.jsonl');selected=[]
  if ill:
   selected=rank([x for x in allsamples if not requested or x['sample_id'] in requested or x['sample_id'].split('-',1)[-1] in requested or x['asset_id'] in requested])[:2]
   add(f'platforms/{p}/current-examples.jsonl',selected,'本轮18稿的完整原文+逐镜卡+15封面覆盖；冲突随记录交付，不继承样例事实或评分')
  selected_count+=len(selected);coverage[p]={'current_editorial_examples_available':len(allsamples) if ill else 0,'current_editorial_examples_selected':len(selected),'approved_editorial_examples_available':0,'approved_editorial_examples_selected':0,'real_cases':0,'published_scripts':0,'constructed_examples_selected':0,'example_match_status':'CURRENT_DOMAIN_REFERENCE' if selected else 'GENERIC_GENES_ONLY','case_match_status':'NO_NEW_TASK_FACTS_FROM_EXAMPLES'}
 if ill:
  for path in ['standards/20261118/text/SRC1.txt','standards/20261118/text/SRC4.txt']:guide(path)
  audit=load(root/'standards/20261118/source-audit.json');guide('standards/20261118/source-audit.json',json.dumps(audit,ensure_ascii=False))
  add('domains/illustration/opening-references.jsonl',jl('domains/illustration/opening-references.jsonl'),'本轮来源类型的表达参照，不是已核实商业事实')
  profile['selected_current_samples']=selected_count
 scope=brief.get('brand_scope');memory=[x for x in jl('memory/events.jsonl') if scope and x.get('brand_scope')==scope and x.get('sync_status')=='synced'][-12:]
 rules={'current_verification':[]}
 for p in brief['platforms']:rules[p]={n:(root/f'rules/{p}/{n}.md').read_text() for n in ['official-rules','mechanisms','creative-hypotheses']};rules[p]['adapter']=(root/f'platforms/{p}/adapter.md').read_text()
 return {'engine_version':'3.0.0','version':m['version'],'brief_sha256':hashlib.sha256(json.dumps(brief,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'source':m.get('source',{}),'release_policy':load(root/'release-policy.json'),'assets':assets,'title_candidates_by_hook':title_groups,'title_source_fragments':[x for v in title_groups.values() for x in v],'must_read_guidance':guidance,'domain_profile':profile,'domain_case_coverage':{'explicitly_selected':selected_count if requested else 0,'independently_verified':0,'published_performance':'NOT_RUN'} if ill else None,'coverage':coverage,'rules':rules,'rubric':load(root/'rubrics/quality.json'),'excluded_candidates':excluded,'memory':memory,'retrieval_stats':{'elapsed_ms':round((time.perf_counter()-started)*1000,2),'selected_records':len(assets),'verified_files':len(m['assets']),'raw_operating_records_scanned':0,'title_mappings_scanned':len(maps),'source_excerpt_records':1,'objective':objective,'evidence_available':available,'performance_status':'NOT_RUN','source_release':'20261118-evening','legacy_candidates':0}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brief',required=True);p.add_argument('--kb',default=str(ROOT/'assets/kb-snapshot'));p.add_argument('--output',required=True);a=p.parse_args()
 try:
  out=pack(Path(a.kb),load(a.brief));Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out['retrieval_stats'],ensure_ascii=False))
 except (ValueError,OSError,KeyError) as e:p.exit(2,str(e)+'\n')
