#!/usr/bin/env python3
"""Verify the complete snapshot; load bounded curated assets, never raw title/operations corpora."""
import argparse,json,hashlib,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PLATFORMS=('xiaohongshu','douyin','channels')
def load(p):return json.loads(Path(p).read_text())
def verified(root):
 root=Path(root).resolve();m=load(root/'KB-MANIFEST.json');seen=set()
 for a in m['assets']:
  if a['path'] in seen:raise ValueError('duplicate manifest path')
  seen.add(a['path']);p=(root/a['path']).resolve()
  if not p.is_relative_to(root):raise ValueError('unsafe manifest path')
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=a['sha256']:raise ValueError('hash mismatch: '+a['path'])
 required={'asset-index.jsonl','shared/formulas.jsonl','shared/hooks.jsonl','shared/spoken-hooks.jsonl','shared/needs.jsonl','shared/human-voice.md','shared/human-voice-patterns.jsonl','shared/creator-voice-profile.md','shared/cta-comment-seeds.jsonl','shared/matching.md','memory/events.jsonl'}
 required.update({'rubrics/selection.json','shared/production-principles.jsonl','rubrics/quality.json','shared/source-excerpts.jsonl','shared/cta-comment-seeds.jsonl'})
 for platform in PLATFORMS:
  required.update({f'platforms/{platform}/{name}.jsonl' for name in ('hooks','formula-applications','worked-examples','cases-index','scripts-index','segments','proofs','seo-keywords','entry-and-actions','approved-examples','routing')})
  required.update({f'rules/{platform}/{name}.md' for name in ('official-rules','mechanisms','creative-hypotheses')})
  required.add(f'platforms/{platform}/adapter.md')
 if not required <= seen:raise ValueError('manifest missing required runtime assets: '+','.join(sorted(required-seen)))
 index=[json.loads(x) for x in (root/'asset-index.jsonl').read_text().splitlines() if x]
 indexed={x['path']:x['sha256'] for x in index};manifested={x['path']:x['sha256'] for x in m['assets'] if x['path']!='asset-index.jsonl'}
 if len(indexed)!=len(index) or indexed!=manifested:raise ValueError('manifest/index mismatch')
 return m
def pack(root,brief):
 """Bounded candidates with exact record/file provenance. Examples are not evidence."""
 started=time.perf_counter();root=Path(root);m=verified(root);assets=[];coverage={};excluded=[]
 objective=brief.get('objective','trust');context=brief.get('content_context',{})
 query=' '.join([brief['topic'],brief['audience'],brief['goal'],json.dumps(context,ensure_ascii=False)])
 grams=set(re.sub(r'[^\w\u4e00-\u9fff]','',query)[i:i+2] for i in range(max(0,len(re.sub(r'[^\w\u4e00-\u9fff]','',query))-1)))
 def jl(p):return [json.loads(x) for x in (root/p).read_text().splitlines() if x]
 def relevance(x):return sum(g in json.dumps(x,ensure_ascii=False) for g in grams)
 def rank(rows):return sorted(rows,key=lambda x:(-relevance(x),x.get('asset_id','')))
 def add(p,records,why):
  for a in records:
   assets.append({'asset_id':a.get('asset_id',a.get('id')),'source_path':p,'file_sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'record_sha256':hashlib.sha256(json.dumps(a,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'match_reason':why,'ranking':{'lexical_overlap':relevance(a),'semantic_match':'REQUIRES_EDITOR_DECISION','effectiveness':'NOT_RUN'},'record':a})
 # Intent and evidence availability choose families; lexical score only ranks inside eligible families.
 available=any(x.get('status')=='available' and x.get('evidence_role') in ('proof','demonstration') for x in brief.get('production_resources',[]))
 task=brief.get('content_task','diagnosis')
 families={'diagnosis':['F02','F01','F05','F11','F16'],'correction':['F12','F02','F11','F05'],'tutorial':['F03','F01','F18','F02'],'case':['F13','F15','F16','F10'],'comparison':['F04','F05','F11','F07'],'objection':['F06','F10','F11','F09'],'planning':['F05','F10','F16','F08'],'retention':['F18','F01','F06']}
 eligible=families.get(task,families['diagnosis'])[:]
 if objective in ('inquiry','purchase'):eligible+=['F07','F08','F06']
 if objective=='trust':eligible+=['F16','F11']
 if objective=='awareness':eligible+=['F09','F10']
 if objective=='retention':eligible+=['F18']
 eligible=list(dict.fromkeys(eligible))
 lock=brief.get('formula_lock')
 all_formulas=jl('shared/formulas.jsonl')
 if lock and lock not in {a['asset_id'] for a in all_formulas}:raise ValueError('unknown locked formula')
 if lock:eligible=[lock.split(':')[-1]]
 for code in ('F03','F13','F14','F15','F16'):
  # Historical narratives, a camera, and planned footage are not available proof.
  if code in eligible and not available:
   excluded.append({'asset_id':'SHARED:'+code,'reason':'没有available且标proof/demonstration的本次素材；如锁定，需先补证据或明确示例'})
   eligible.remove(code)
 if lock and lock.split(':')[-1] not in eligible:raise ValueError('locked formula evidence unavailable; resolve input before intake')
 add('shared/formulas.jsonl',rank([a for a in all_formulas if a['asset_id'].split(':')[-1] in eligible]),'任务 '+task+' ×目标 '+objective+' ×可用证据；关键词仅排序')
 hooks=jl('shared/spoken-hooks.jsonl')
 # All 17 mechanisms are discoverable; evidence-specific mechanisms are excluded when no proof exists.
 proof_hooks={'H306','H307','H309','H310','H314','H316'}
 hs=[a['asset_id'].split(':')[-1] for a in hooks if available or a['asset_id'].split(':')[-1] not in proof_hooks]
 for a in hooks:
  if a['asset_id'].split(':')[-1] not in hs:excluded.append({'asset_id':a['asset_id'],'reason':'结果/对照入口需要本次可见证明'})
 add('shared/spoken-hooks.jsonl',rank([a for a in hooks if a['asset_id'].split(':')[-1] in hs])[:8],'按本次任务排序的口播机制；最终选择须由正文证据兑现')
 hs=[a['asset_id'].split(':')[-1] for a in assets if a['source_path']=='shared/spoken-hooks.jsonl']
 ctas=jl('shared/cta-comment-seeds.jsonl');add('shared/cta-comment-seeds.jsonl',[x for x in ctas if x['asset_id'] in (['SHARED:CTA:04','SHARED:CTA:09'] if objective=='inquiry' else ['SHARED:CTA:10'] if objective=='purchase' else ['SHARED:CTA:01','SHARED:CTA:06','SHARED:CTA:07'])],'锁定业务目的，渠道与动作另行核验')
 add('shared/production-principles.jsonl',jl('shared/production-principles.jsonl'),'已确认手册的通用创作判断；原件可追溯')
 add('shared/source-excerpts.jsonl',rank(jl('shared/source-excerpts.jsonl'))[:3],'原始运营表的可追溯方法片段；不是案例事实')
 add('shared/human-voice-patterns.jsonl',rank(jl('shared/human-voice-patterns.jsonl'))[:3],'按语境检查书面腔与抽象赞美，保留原事实和条件，不机械替词')
 # Upstream title assets remain titles; retrieve mappings and original lines, never call them spoken hooks.
 title_lines=(root/'sources/xhs_ai_title_formula_knowledge_v2.txt').read_text().splitlines()
 mapping=jl('sources/title-to-spoken-hook-map.jsonl')
 usable=[x for x in mapping if x.get('decision')!='discarded' and x.get('hook_id') in ['SHARED:'+h for h in hs]]
 candidates=[]
 for x in usable:
  n=x.get('source_line',0);original=title_lines[n-1] if isinstance(n,int) and 0<n<=len(title_lines) else ''
  candidates.append({'mapping':x,'original_line':original,'status':'upstream_title_only','topic_case_match':False})
 titles=rank(candidates)[:3]
 rules={'current_verification':jl('rules/current-verification.jsonl')}
 for p in brief['platforms']:
  if p not in PLATFORMS:raise ValueError('unsupported platform')
  rules[p]={n:(root/f'rules/{p}/{n}.md').read_text() for n in ['official-rules','mechanisms','creative-hypotheses']}
  rules[p]['adapter']=(root/f'platforms/{p}/adapter.md').read_text()
  for coll,limit in [('hooks',3),('formula-applications',6),('proofs',1),('seo-keywords',1),('entry-and-actions',1)]:
   add(f'platforms/{p}/{coll}.jsonl',rank(jl(f'platforms/{p}/{coll}.jsonl'))[:limit],'平台 '+p+' 的入口/证明/行动组织；创作方法不等于算法权重')
  add(f'platforms/{p}/routing.jsonl',jl(f'platforms/{p}/routing.jsonl'),'本平台通用证据组织；专业公式应用不匹配时使用，仍须解释迁移')
  examples=jl(f'platforms/{p}/worked-examples.jsonl');subject=brief['topic']+' '+json.dumps(context,ensure_ascii=False)
  domain=brief.get('domain') or ('design_service' if re.search('印花|插画|图案|母婴|床品|纹理',subject) else 'ai_service' if re.search('报表|自动化|Agent|知识库|AI系统|企业系统',subject,re.I) else None)
  chosen=[x for x in examples if x['domain']==domain][:1]
  add(f'platforms/{p}/worked-examples.jsonl',chosen,'构造示范，仅迁移论证方法，不借用客户/成效')
  approved=jl(f'platforms/{p}/approved-examples.jsonl');matched=rank([x for x in approved if x['domain']==domain])[:2]
  add(f'platforms/{p}/approved-examples.jsonl',matched,'已认可编辑样稿；不继承客户叙述/旧评分/业绩')
  coverage[p]={'approved_editorial_examples_available':len(approved),'approved_editorial_examples_selected':len(matched),'real_cases':len(jl(f'platforms/{p}/cases-index.jsonl')),'published_scripts':len(jl(f'platforms/{p}/scripts-index.jsonl')),'constructed_examples_selected':len(chosen),'example_match_status':'DOMAIN_METHOD_ONLY' if chosen else 'NO_DOMAIN_EXAMPLE_MATCH','case_match_status':'NO_VERIFIED_CASE_AVAILABLE'}
 scope=brief.get('brand_scope')
 memory=[x for x in jl('memory/events.jsonl') if scope and x.get('brand_scope')==scope and x.get('sync_status')=='synced'][-12:]
 return {'engine_version':'2.0.0','version':m['version'],'brief_sha256':hashlib.sha256(json.dumps(brief,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'source':m.get('source',{}),'assets':assets,'title_source_fragments':titles,'rules':rules,'coverage':coverage,'memory':memory,'rubric':load(root/'rubrics/quality.json'),'excluded_candidates':excluded,'retrieval_stats':{'elapsed_ms':round((time.perf_counter()-started)*1000,2),'selected_records':len(assets),'verified_files':len(m['assets']),'raw_operating_records_scanned':0,'title_mappings_scanned':len(mapping),'source_excerpt_records':sum(a['source_path']=='shared/source-excerpts.jsonl' for a in assets),'objective':objective,'evidence_available':available,'performance_status':'NOT_RUN'}}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brief',required=True);p.add_argument('--kb',default=str(ROOT/'assets/kb-snapshot'));p.add_argument('--output',required=True);a=p.parse_args()
 try:
  o=pack(Path(a.kb),load(a.brief));raw=json.dumps(o,ensure_ascii=False,indent=2);Path(a.output).write_text(raw);print(json.dumps({'version':o['version'],'bytes':len(raw.encode()),**o['retrieval_stats']},ensure_ascii=False))
 except (ValueError,OSError,KeyError) as e:p.exit(2,str(e)+'\n')
