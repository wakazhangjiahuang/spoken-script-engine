#!/usr/bin/env python3
"""Deterministic contract checks, independent review binding. Not a semantic judge."""
import argparse,json,hashlib,re,itertools,sys
from datetime import date
from urllib.parse import urlparse
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUBRIC=json.loads((ROOT/'assets/kb-snapshot/rubrics/quality.json').read_text())
DIMS=[x['id'] for x in RUBRIC['dimensions']];WEIGHTS=[x['weight'] for x in RUBRIC['dimensions']]
def schema_errors(value,schema,path='$'):
 errors=[];kind=schema.get('type')
 check={'object':lambda x:isinstance(x,dict),'array':lambda x:isinstance(x,list),'string':lambda x:isinstance(x,str),'number':lambda x:type(x) in [int,float],'boolean':lambda x:type(x)==bool,'integer':lambda x:type(x)==int}
 if kind and not check[kind](value):return [path+' expected '+kind]
 if 'enum' in schema and value not in schema['enum']:errors.append(path+' invalid enum')
 if isinstance(value,dict):
  errors += [path+' missing '+k for k in schema.get('required',[]) if k not in value]
  if schema.get('additionalProperties') is False:errors += [path+' unexpected '+k for k in value if k not in schema.get('properties',{})]
  for k,v in value.items():
   if k in schema.get('properties',{}):errors+=schema_errors(v,schema['properties'][k],path+'.'+k)
 if isinstance(value,list):
  if len(value)<schema.get('minItems',0):errors.append(path+' too few items')
  if schema.get('uniqueItems') and len(set(json.dumps(x,sort_keys=True) for x in value))!=len(value):errors.append(path+' duplicate items')
  for i,v in enumerate(value):errors+=schema_errors(v,schema.get('items',{}),path+'['+str(i)+']')
 if isinstance(value,str):
  if len(value)<schema.get('minLength',0):errors.append(path+' empty string')
  if 'pattern' in schema and not re.search(schema['pattern'],value):errors.append(path+' invalid pattern')
 if type(value) in [int,float]:
  if 'exclusiveMinimum' in schema and value<=schema['exclusiveMinimum']:errors.append(path+' invalid minimum')
  if 'minimum' in schema and value<schema['minimum']:errors.append(path+' below minimum')
  if 'maximum' in schema and value>schema['maximum']:errors.append(path+' above maximum')
  if not __import__('math').isfinite(value):errors.append(path+' nonfinite number')
 return errors
def units(text):return len(re.findall(r'[\u4e00-\u9fff]|[A-Za-z0-9]+',text))
DECISION_STAGES = {
 '认知': '认知', '兴趣': '认知', '信任': '考虑', '考虑': '考虑',
 '咨询/转化': '行动', '复购与传播': '使用',
}
COMMENT_KINDS = {'experience', 'question', 'choice', 'need'}

def normalized_speech(value):
 return ''.join(character.lower() for character in value if character.isalnum())

def check_script_plan(script, brief, allowed_hooks):
 errors = []
 sid = script['id']
 required = ('decision_stage', 'value_translation', 'hook_plan', 'calling')
 missing = [field for field in required if field not in script]
 if missing:
  return [sid + ' missing ' + ', '.join(missing)]
 stage = script['decision_stage']
 if DECISION_STAGES[stage] != script['funnel_stage']:
  errors.append(sid + ' inconsistent decision stage')
 if brief.get('stage_locked') and brief.get('decision_stage', stage) != stage:
  errors.append(sid + ' decision stage lock')
 segments = script['segments']
 hook = script['hook_plan']
 if hook['alternate_hook_id'] not in allowed_hooks or hook['alternate_hook_id'] == script['hook_id']:
  errors.append(sid + ' invalid alternate hook mechanism')
 if normalized_speech(hook['alternate_text']) == normalized_speech(segments[0]['text']):
  errors.append(sid + ' duplicate alternate hook wording')
 if hook['payoff_segment_id'] not in {segment['id'] for segment in segments[1:-1]}:
  errors.append(sid + ' payoff must be in the body before Calling')
 calling = script['calling']
 if calling['line'] not in segments[-1]['text']:
  errors.append(sid + ' Calling line absent from ending')
 if calling['kind'] in COMMENT_KINDS and not all(calling.get(key) for key in ('comment_signal', 'next_topic')):
  errors.append(sid + ' missing comment signal or follow-up topic')
 if calling['kind'] == 'service' and not calling.get('channel_basis'):
  errors.append(sid + ' missing verified channel basis')
 return errors

def check_platform_comparisons(platforms, review):
 expected = {frozenset(pair) for pair in itertools.combinations(platforms, 2)}
 comparisons = review.get('cross_platform')
 if comparisons is None:
  return ['cross-platform review missing']
 observed = [frozenset((item['platform_a'], item['platform_b'])) for item in comparisons]
 if len(observed) != len(expected) or set(observed) != expected:
  return ['cross-platform review pairs mismatch']
 return ['cross-platform semantic diversity failed' for item in comparisons if not item['real_difference_passed']]

def check_direction(script,brief):
 errors=[];sid=script['id'];resources={r['id']:r for r in brief['production_resources']}
 order=script['director_plan']['shoot_order'];ids=[g['id'] for g in script['segments']]
 if len(order)!=len(ids) or set(order)!=set(ids):errors.append(sid+' shooting order must cover every segment exactly once')
 for segment in script['segments']:
  resource=segment['shot']['material_id']
  if resource!='NONE' and resource not in resources:errors.append(sid+' unknown shot resource '+resource)
  if resource in resources and resources[resource]['status']=='unavailable':errors.append(sid+' unavailable material used '+resource)
 return errors

def check_release_gates(batch,review):
 errors=[];platforms=batch['brief']['platforms'];checks=review.get('platform_checks',[])
 if len(checks)!=len(platforms) or {c['platform'] for c in checks}!=set(platforms):errors.append('platform checks missing/duplicate')
 for c in checks:
  try:
   from datetime import datetime
   from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
   today=datetime.now(ZoneInfo(batch['brief'].get('timezone','UTC'))).date()
   checked=date.fromisoformat(c['checked_at'])
   if checked>today:errors.append('platform check date is in the future')
  except (ValueError,ZoneInfoNotFoundError):errors.append('invalid platform check date or timezone')
  official={'xiaohongshu':('xiaohongshu.com','xhscdn.com'),'douyin':('douyin.com','douyinstatic.com','draftstatic.com'),'channels':('weixin.qq.com','weixin110.qq.com','wx.qq.com')}[c['platform']]
  for url in c['source_urls']:
   host=urlparse(url).hostname or ''
   if not any(host==domain or host.endswith('.'+domain) for domain in official):errors.append('source is not an official platform host')
  if c['status']=='PARTIAL' and c['publish_ready']:errors.append('partial platform evidence cannot be publication ready')
  if c['status']=='VERIFIED' and not c['source_urls']:errors.append('verified platform needs source URLs')
  if any(not u.startswith('https://') for u in c['source_urls']):errors.append('invalid platform source URL')
 for item in review['items']:
  script=next((s for s in batch['scripts'] if s['id']==item['script_id']),None)
  if not script:continue
  for name,gate in item['gate_checks'].items():
   segment=next((g for g in script['segments'] if g['id']==gate['segment_id']),None)
   if not gate['passed']:errors.append(item['script_id']+' failed release gate '+name)
   if not segment or gate['quote'] not in segment['text']:errors.append(item['script_id']+' gate quote absent '+name)
 return errors

def check_blocks(script,brief):
 errors=[];sid=script['id'];segs=script['segments'];roles=[g['role'] for g in segs]
 if roles[:2]!=['hook','suspense'] or roles[-1]!='calling' or not any(r in ('context','judgment','value') for r in roles[2:-1]):errors.append(sid+' missing opening, body or Calling function')
 if roles.count('hook')!=1 or roles.count('suspense')!=1 or roles.count('calling')!=1:errors.append(sid+' repeated opening/Calling block')
 if segs[0]['duration_seconds']>3 or sum(g['duration_seconds'] for g in segs[:2])>8:
  locks=[r for r in brief.get('copy_locks',[]) if r.get('plan_id')==script.get('plan_id')]
  kept=any(r.get('source') and r.get('allow_timing_overrun') is True and r.get('hook')==segs[0]['text'] and r.get('suspense')==segs[1]['text'] for r in locks)
  if not kept or not script.get('timing_exception_note'):errors.append(sid+' opening exceeds 3/8-second budget')
 if normalized_speech(segs[0]['text'])==normalized_speech(segs[1]['text']):errors.append(sid+' suspense repeats hook')
 if any(re.match(r'^(案例|专业判断|观众所得)[：:]',g['text']) for g in segs):errors.append(sid+' production labels inside spoken text')
 test=script.get('read_test',{})
 if test.get('status')=='MEASURED':
  if type(test.get('seconds')) not in (int,float) or not test.get('evidence'):errors.append(sid+' measured read test missing evidence/time')
  elif test['seconds']>brief.get('duration_limit_seconds',60):errors.append(sid+' measured duration limit')
 return errors

def publication_ready(batch,review):
 if any(s['segments'][0]['duration_seconds']>3 or sum(g['duration_seconds'] for g in s['segments'][:2])>8 for s in batch['scripts']):return False
 if not review or not review.get('platform_checks') or not all(x['publish_ready'] and x['status']=='VERIFIED' for x in review['platform_checks']):return False
 used={g['shot']['material_id'] for s in batch['scripts'] for g in s['segments']}
 resources={x['id']:x for x in batch['brief']['production_resources']}
 if 'NONE' in used or any(resources.get(i,{}).get('status')!='available' for i in used):return False
 return all(s.get('read_test',{}).get('status')=='MEASURED' and s['read_test'].get('evidence') and type(s['read_test'].get('seconds')) in (int,float) and s['read_test']['seconds']<=batch['brief'].get('duration_limit_seconds',60) for s in batch['scripts'])

def validate(batch,review=None,sha=None,kb=None,legacy=False,run_dir=None):
 errors=[];warnings=[]
 bs=json.loads((ROOT/'schemas/spoken-batch.schema.json').read_text())
 if legacy:
  bs['required']=[x for x in bs['required'] if x not in ('engine_version','performance_status')]
  bs['properties'].pop('engine_version',None)
  bs['properties']['brief']['required']=[x for x in bs['properties']['brief']['required'] if x not in ('content_context','voice_profile','production_resources','objective','input_resolution')]
  bs['properties']['scripts']['items']['required']=[x for x in bs['properties']['scripts']['items']['required'] if x not in ('decision_stage','value_translation','hook_plan','calling','director_plan','plan_id','asset_applications','cover_main','cover_sub','comment_hook')]
  bs['properties']['scripts']['items']['properties']['calling']['required']=[x for x in bs['properties']['scripts']['items']['properties']['calling']['required'] if x not in ('intent','qualification','next_step')]
  bs['properties']['scripts']['items']['properties']['segments']['items']['required'].remove('shot')
 errors+=schema_errors(batch,bs)
 if errors:return {'passed':False,'errors':errors,'warnings':warnings}
 if not legacy:
  if not run_dir:errors.append('recorded pre-draft plan/run directory required')
  else:
   from execution_contract import provenance
   # Find the exact accepted bytes; canonical JSON equivalence cannot replace byte binding.
   candidates=list(Path(run_dir).glob('batch-v*.json'))
   matched=next((p for p in candidates if hashlib.sha256(p.read_bytes()).hexdigest()==sha),None)
   if not matched:errors.append('batch not submitted to this run')
   else:
    if json.loads(matched.read_text())!=batch:errors.append('batch object differs from submitted bytes')
    errors.extend(provenance(run_dir,matched))
 from retrieve_assets import verified
 kb=Path(kb) if kb else ROOT/'assets/kb-snapshot'
 try:
  manifest=verified(kb)
  if not legacy and (manifest.get('version')!='3.0.0' or json.loads((kb/'rubrics/quality.json').read_text())!=RUBRIC):raise ValueError('knowledge rubric incompatible with engine 3.0.0')
  allowed_formulas={json.loads(x)['asset_id'] for x in (kb/'shared/formulas.jsonl').read_text().splitlines() if x}
  allowed_hooks={json.loads(x)['asset_id'] for x in (kb/'shared/spoken-hooks.jsonl').read_text().splitlines() if x}
  if any(asset['path'] == 'shared/spoken-hooks.jsonl' for asset in manifest['assets']):
   allowed_hooks.update(json.loads(line)['asset_id'] for line in (kb/'shared/spoken-hooks.jsonl').read_text().splitlines() if line)
 except (ValueError,OSError,KeyError) as e:return {'passed':False,'errors':['knowledge validation: '+str(e)],'warnings':warnings}
 b=batch['brief'];scripts=batch['scripts'];plats=b['platforms'];ids=[s['id'] for s in scripts];rate=b.get('speech_chars_per_second',4.2);facts={f['id']:f for f in b['facts']}
 current_contract = not legacy or batch.get('engine_version') == '1.4.0'
 expected_counts={p:b.get('count_per_platform',{}).get(p,3) for p in plats}
 if not legacy:
  allowed_hooks={x for x in allowed_hooks if re.fullmatch(r'SHARED:H3[0-9]{2}',x)}
  resource_ids=[r['id'] for r in b['production_resources']]
  if len(resource_ids)!=len(set(resource_ids)):errors.append('duplicate production resource IDs')
  if set(b.get('count_per_platform',{}))-set(plats):errors.append('count declared for unselected platform')
 if current_contract:
  if 'content_context' not in b:
   errors.append('missing brief content context')
  if 'decision_stage' in b and DECISION_STAGES[b['decision_stage']] != b.get('funnel_stage'):
   errors.append('inconsistent brief decision stage')
 if len(facts)!=len(b['facts']):errors.append('duplicate fact IDs')
 if len(ids)!=len(set(ids)):errors.append('duplicate script IDs')
 if set(s['platform'] for s in scripts)!=set(plats) or len(scripts)!=sum(expected_counts.values()):errors.append('platform/count contract')
 for s in scripts:
  if s['formula_id'] not in allowed_formulas or s['hook_id'] not in allowed_hooks:errors.append(s['id']+' unknown knowledge asset reference')
  if b.get('formula_lock') and s['formula_id']!=b['formula_lock']:errors.append(s['id']+' explicit formula lock')
  sid=s['id'];segments=s['segments'];segids=[g['id'] for g in segments];text='\n'.join(g['text'] for g in segments)
  if len(set(segids))!=len(segids):errors.append(sid+' duplicate segments')
  if b.get('topic_locked',True) and s['topic']!=b['topic']:errors.append(sid+' topic lock')
  if b.get('stage_locked') and s['funnel_stage']!=b['funnel_stage']:errors.append(sid+' stage lock')
  if current_contract:errors.extend(check_script_plan(s,b,allowed_hooks))
  if not legacy:
   errors.extend(check_direction(s,b));errors.extend(check_blocks(s,b))
   from surface_contract import draft_errors as surface_errors
   errors.extend(surface_errors(s))
   from composition_contract import text_errors
   errors.extend(text_errors(s))
  if s['unverified_claims']:errors.append(sid+' unresolved claims')
  seconds=sum(g['duration_seconds'] for g in segments)
  if seconds>b.get('duration_limit_seconds',60):errors.append(sid+' duration limit')
  for g in segments:
   if units(g['text'])/rate+g.get('shot',{}).get('silent_hold_seconds',0)>g['duration_seconds']+0.5:errors.append(sid+'/'+g['id']+' insufficient read time')
  for c in s['claim_links']:
   if c['segment_id'] not in segids or c['evidence_id'] not in facts:errors.append(sid+' invalid evidence reference')
   elif c['claim'] not in next(x['text'] for x in segments if x['id']==c['segment_id']):errors.append(sid+' claim anchor absent')
   elif facts[c['evidence_id']]['status']=='hypothetical' and not re.search('假设|举例|示例',text):errors.append(sid+' unlabeled hypothetical claim')
  for forbidden in b.get('forbidden_claims',[]):
   if forbidden and forbidden in text:errors.append(sid+' forbidden claim '+forbidden)
 for plat in plats:
  ss=[s for s in scripts if s['platform']==plat]
  if len(ss)!=expected_counts[plat]:errors.append(plat+' script count mismatch');continue

  for a,c in itertools.combinations(ss,2):
   if sum(a['angle'][k]!=c['angle'][k] for k in ['problem','benefit','proof_organization'])<2:errors.append(plat+' declared information diversity')
   if ''.join(g['text'] for g in a['segments'])==''.join(g['text'] for g in c['segments']):errors.append(plat+' duplicate body')
 if current_contract:
  for left,right in itertools.combinations(scripts,2):
   if left['platform'] == right['platform']:
    continue
   left_body = normalized_speech(''.join(segment['text'] for segment in left['segments'][1:-1]))
   right_body = normalized_speech(''.join(segment['text'] for segment in right['segments'][1:-1]))
   if left_body and left_body == right_body:
    public=lambda s:[(g['text'],g['visual'],g['duration_seconds'],g['shot']['edit_cue']) for g in s['segments']]
    if public(left)==public(right):errors.append('identical cross-platform delivery: '+left['id']+'/'+right['id'])
    else:warnings.append('Shared case body: independently review first-shot, evidence order and tempo; do not force a new audience or benefit.')
 if not legacy:
  from composition_contract import diversity_errors
  errors.extend(diversity_errors(scripts))
 if review is None:errors.append('independent review missing')
 else:
  rs=json.loads((ROOT/'schemas/review.schema.json').read_text())
  if legacy:
   rs['required']=[x for x in rs['required'] if x not in ('platform_checks','cross_platform','commercial_checks','asset_checks','review_limitations','decision_sha256','asset_pack_sha256')]
   rs['properties']['items']['items']['required'].remove('gate_checks')
   olddims=['audience_value','logic','promise_payoff','evidence','speakability','platform_fit','stage_action','shootability']
   score_schema=rs['properties']['items']['items']['properties']['scores'];sample=next(iter(score_schema['properties'].values()));score_schema['required']=olddims;score_schema['properties']={d:sample for d in olddims}
  re_errors=schema_errors(review,rs)
  if re_errors:return {'passed':False,'errors':errors+re_errors,'warnings':warnings}
  if (not legacy and not sha) or (sha and review.get('batch_sha256')!=sha):errors.append('review not bound to this batch')
  if not legacy and run_dir:
   from execution_contract import digest
   for name,file in [('decision_sha256','decision.json'),('asset_pack_sha256','asset-pack.json')]:
    if review.get(name)!=digest(Path(run_dir)/file):errors.append('review not bound to '+file)
  if current_contract:errors.extend(check_platform_comparisons(plats,review))
  from surface_contract import output_errors
  for script in scripts:errors.extend(output_errors(script,b))
  if not legacy:
   errors.extend(check_release_gates(batch,review))
   from surface_contract import review_errors as delivery_review_errors
   errors.extend(delivery_review_errors(review,scripts))
   content=review.get('content_decisions',[])
   if len(content)!=len(scripts) or {r.get('script_id') for r in content}!=set(ids) or any(r.get('verdict')!='DRAFT_FOR_USER_REVIEW' or not r.get('reason') for r in content):errors.append('visible content judgement missing or rejected')
   if run_dir:
    from composition_contract import review_errors
    errors.extend(review_errors(review,scripts,json.loads((Path(run_dir)/'decision.json').read_text()),json.loads((Path(run_dir)/'asset-pack.json').read_text())))
    from illustration_contract import review_errors as information_review_errors
    errors.extend(information_review_errors(review,scripts,json.loads((Path(run_dir)/'asset-pack.json').read_text())))
  who=review.get('reviewer',{})
  if who.get('independent') is not True or who.get('mode') not in ['independent_thread','isolated_review','human'] or not who.get('identity'):errors.append('review execution identity missing')
  ri=review.get('items',[])
  if len(ri)!=len(ids) or set(x.get('script_id') for x in ri)!=set(ids):errors.append('review count/IDs')
  for item in ri:
   sid=item.get('script_id');s=next((s for s in scripts if s['id']==sid),None)
   if not s:continue
   if item.get('gates_passed') is not True or item.get('issues'):errors.append(str(sid)+' semantic hard gate/issue')
   total=0
   for dim,weight in zip(olddims if legacy else (DIMS if item.get('scores') else []),[15,15,15,15,10,10,10,10] if legacy else WEIGHTS):
    d=item.get('scores',{}).get(dim,{})
    if not isinstance(d,dict):errors.append(str(sid)+' invalid review dimension '+dim);continue
    score=d.get('score');sg=next((g for g in s['segments'] if g['id']==d.get('segment_id')),None)
    if type(score)!=int or score not in range(5) or not sg or not d.get('quote') or d['quote'] not in sg['text'] or not d.get('reason'):errors.append(str(sid)+' review evidence '+dim);continue
    role_requirements={'hook_strength':{'hook'},'suspense':{'suspense'},'professional_judgment':{'judgment'},'aesthetic_expression':{'judgment','value'},'buyer_value':{'judgment','value'},'cta_persuasion':{'calling'}}
    if not legacy and sg and sg.get('role') not in role_requirements.get(dim,set()):errors.append(str(sid)+' wrong scoring block '+dim)
    if score<3:warnings.append(str(sid)+' optional diagnostic low dimension '+dim)
    total+=score*weight/4
   if RUBRIC.get('minimum_total') is not None and total<RUBRIC['minimum_total']:errors.append(str(sid)+' diagnostic total below configured minimum')
  if not legacy:
   for key in ['commercial_checks','asset_checks']:
    checks=review.get(key,[])
    if len(checks)!=len(ids) or {c.get('script_id') for c in checks}!=set(ids):errors.append(key+' missing/duplicate scripts')
    for c in checks:
     s=next((x for x in scripts if x['id']==c.get('script_id')),None)
     if not s:continue
     if key=='asset_checks' and not c.get('application_is_substantive'):errors.append(s['id']+' assets only nominally applied')
     if key=='commercial_checks':
      if not c.get('passes'):errors.append(s['id']+' commercial editorial review failed')
      if c.get('payoff_quote') not in '\n'.join(x['text'] for x in s['segments'][1:-1]):errors.append(s['id']+' commercial payoff quote absent')
  div=review.get('diversity',[])
  for plat in plats:
   pids=[s['id'] for s in scripts if s['platform']==plat]
   for a,c in itertools.combinations(pids,2):
    matches=[d for d in div if d.get('platform')==plat and {d.get('a'),d.get('b')}=={a,c}]
    if len(matches)!=1 or matches[0].get('real_difference_passed') is not True or not matches[0].get('reason'):errors.append(plat+' semantic diversity review '+a+'/'+c)
 ready=publication_ready(batch,review) if not legacy else False
 warnings.append('professional equivalence and actual performance require separate human/publishing evaluation')
 return {'passed':not errors,'errors':errors,'warnings':warnings,'scripts':len(scripts),'platforms':plats,'validation_scope':'artifact_contract_and_declared_editorial_review; not measured persuasion','editorial_status':'REVIEWED' if not errors else 'NEEDS_REVISION','publication_status':'READY_FOR_USER_REVIEW' if ready and not errors else 'NEEDS_READ_MATERIAL_OR_PLATFORM_CHECK','performance_status':'NOT_RUN','user_acceptance_status':'NOT_REVIEWED','marketing_effectiveness':'NOT_MEASURED'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--batch',required=True);p.add_argument('--review');p.add_argument('--output');p.add_argument('--kb');p.add_argument('--run-dir');p.add_argument('--legacy',action='store_true',help='Historical inspection, not reviewed export');a=p.parse_args()
 try:
  raw=Path(a.batch).read_bytes();b=json.loads(raw);r=json.loads(Path(a.review).read_text()) if a.review else None;v=validate(b,r,hashlib.sha256(raw).hexdigest(),a.kb,a.legacy,a.run_dir)
  if a.output:Path(a.output).write_text(json.dumps(v,ensure_ascii=False,indent=2))
  print(json.dumps(v,ensure_ascii=False));raise SystemExit(0 if v['passed'] else 2)
 except (ValueError,KeyError,OSError) as e:p.exit(2,str(e)+'\n')
