"""Source-to-speech bindings. Detect omissions; never certify persuasion by keyword or score."""
import re,itertools
from decimal import Decimal
from difflib import SequenceMatcher
EVIDENCE_FORMULAS={'SHARED:F03','SHARED:F13','SHARED:F14','SHARED:F15','SHARED:F16'}
NARRATIVE_FORMULAS={'SHARED:F13','SHARED:F15'}
ACTIONS={'comment','save','share','follow','inquiry','purchase','apply','none'}
def nonblank(x):return isinstance(x,str) and bool(x.strip())
def normalize(x):return ''.join(c.lower() for c in x if c.isalnum())
MONEY_PATTERN=re.compile(r'(?<![零〇一二两三四五六七八九十百千万亿0-9.])([零〇一二两三四五六七八九十百千万亿0-9]+(?:\.\d+)?)\s*(美刀|美元|万元|元稿费|元订单|刀|USD|US\$)(?![A-Za-z])',re.I)
def money_alias(text):
 """Exact amount/unit tokens; no substring match or currency/unit conversion."""
 result=set()
 for m in MONEY_PATTERN.finditer(text):
  number,unit=m.groups()
  if re.fullmatch(r'\d+(?:\.\d+)?',number):number=str(Decimal(number).normalize())
  unit='美元' if unit.lower() in ('美刀','美元','刀','usd','us$') else unit
  result.add((number,unit))
 return result
def slots(record):return [x for x in record.get('variables','').split('|') if x]
def beats(record):return record.get('structure','').split('→')
def speech_example(record):
 content=record.get('content',{})
 return '\n'.join(str(v) for k,v in content.items() if any(t in k for t in ('黄金三秒','悬念','正文','Calling')))
def anchor_error(anchor,script,allowed=None):
 if not isinstance(anchor,dict):return 'anchor must be object'
 g=next((g for g in script.get('segments',[]) if g.get('id')==anchor.get('segment_id')),None)
 surface=anchor.get('surface','speech');field={'speech':'text','visual':'visual','subtitle':'subtitle'}.get(surface)
 if not g or not field or not nonblank(anchor.get('quote')) or anchor['quote'] not in g.get(field,''):return 'anchor absent from actual '+surface
 if allowed is not None and g['id'] not in allowed:return 'anchor in wrong block'
 return None
def plan_errors(plan,brief,pack):
 errors=[];pool={a['asset_id']:a for a in pack['assets']};facts={f['id']:f for f in brief.get('facts',[])};resources={r['id']:r for r in brief.get('production_resources',[])}
 for p in plan.get('selected',[]):
  sid=p.get('id','?');c=p.get('audience_contract',{});recipe=p.get('source_recipe',{});refs=p.get('asset_refs',{})
  if not isinstance(c,dict) or any(not nonblank(c.get(k)) for k in ('question','payoff','motivation','route','action_reason')) or c.get('primary_action') not in ACTIONS:errors.append(sid+' audience contract missing');continue
  if brief.get('objective')=='inquiry' and c['primary_action']!='inquiry':errors.append(sid+' consultation intent reduced to generic interaction')
  if brief.get('objective')=='purchase' and c['primary_action']!='purchase':errors.append(sid+' purchase intent reduced to generic interaction')
  if not isinstance(recipe,dict):errors.append(sid+' source recipe missing');continue
  for role,key,sourcekey in [('hook','hook_template','spoken_structure'),('body','body_structure','structure'),('calling','calling_template','pattern')]:
   a=pool.get(refs.get(role,{}).get('asset_id'),{})
   if not a or recipe.get(key)!=a.get('record',{}).get(sourcekey):errors.append(sid+' source recipe mismatch '+role)
  gene=recipe.get('gene',{});ga=pool.get(gene.get('asset_id')) if isinstance(gene,dict) else None
  if not ga or ga['record'].get('type')!='attention_gene' or gene.get('record_sha256')!=ga['record_sha256'] or not nonblank(gene.get('transfer')) or not nonblank(gene.get('non_transfer')):errors.append(sid+' current attention gene and transfer scope missing')
  example=recipe.get('example',{});a=pool.get(example.get('asset_id')) if isinstance(example,dict) else None
  if not a or a.get('record',{}).get('type') not in ('approved_editorial_example','structure_reference','editorial_reference','current_editorial_example') or example.get('record_sha256')!=a.get('record_sha256'):errors.append(sid+' missing verified example reference')
  else:
   if not nonblank(example.get('source_quote')) or example['source_quote'] not in speech_example(a['record']):errors.append(sid+' example source quote absent')
   if example.get('match_level') not in ('task_match','structure_only') or any(not nonblank(example.get(k)) for k in ('transfer','non_transfer','mismatch')):errors.append(sid+' example transfer conditions missing')
  title=recipe.get('title',{});hook_id=refs.get('hook',{}).get('asset_id');titles=pack.get('title_candidates_by_hook',{}).get(hook_id,[])
  if not isinstance(title,dict):errors.append(sid+' title mapping missing')
  elif titles and title.get('status')=='no_fit':
   known={x['mapping']['title_id'] for x in titles};checked=title.get('checked_title_ids',[])
   if not isinstance(checked,list) or set(checked)!=known or not nonblank(title.get('reason')):errors.append(sid+' title no-fit lacks actual candidate review')
  elif titles:
   match=next((x for x in titles if x['mapping'].get('title_id')==title.get('title_id') and x['mapping'].get('source_line')==title.get('source_line') and x['original_line']==title.get('original_line')),None)
   if title.get('status') not in ('matched','adapted') or not match or not nonblank(title.get('retained')) or not nonblank(title.get('discarded')):errors.append(sid+' title source does not match chosen hook')
  elif title.get('original_line') or title.get('title_id'):errors.append(sid+' title source does not match current no-match scope')
  elif title.get('status')!='no_match' or not nonblank(title.get('reason')):errors.append(sid+' missing explicit title no-match reason')
  basis=p.get('proof_basis',[])
  if not isinstance(basis,list):errors.append(sid+' proof basis must be array');continue
  formula=refs.get('body',{}).get('asset_id')
  if (formula in EVIDENCE_FORMULAS or refs.get('hook',{}).get('asset_id') in {'SHARED:H306','SHARED:H307','SHARED:H309','SHARED:H310','SHARED:H314','SHARED:H316'}) and not basis:errors.append(sid+' selected mechanism needs scoped proof')
  for evidence in basis:
   if not isinstance(evidence,dict):errors.append(sid+' invalid proof basis');continue
   resource=resources.get(evidence.get('resource_id'),{});factids=evidence.get('fact_ids',[])
   if resource.get('status')!='available' or resource.get('evidence_role') not in ('proof','demonstration') or not nonblank(evidence.get('scope')):errors.append(sid+' unavailable or unscoped proof')
   if not isinstance(factids,list) or any(i not in facts or facts[i]['status']=='hypothetical' for i in factids):errors.append(sid+' proof fact unknown or hypothetical')
   if formula in NARRATIVE_FORMULAS and not factids:errors.append(sid+' narrative proof lacks current facts')
   supported=resource.get('supports_fact_ids')
   if supported is not None and any(i not in supported for i in factids):errors.append(sid+' resource does not support selected fact')
 return errors

def draft_errors(script,plan,pack,brief):
 sid=script['id'];errors=[];pool={a['asset_id']:a for a in pack['assets']};composition=script.get('composition')
 if not isinstance(composition,dict):return [sid+' missing source-to-speech composition']
 segs=script['segments'];opening={g['id'] for g in segs[:2]};before_call={g['id'] for g in segs[:-1]};body={g['id'] for g in segs[1:-1]};end={segs[-1]['id']}
 refs=plan['asset_refs'];hr=pool[refs['hook']['asset_id']]['record'];br=pool[refs['body']['asset_id']]['record']
 for field,key,expected,allowed in [('hook_slots','slot',slots(hr),opening),('body_beats','beat',beats(br),before_call)]:
  rows=composition.get(field,[])
  if not isinstance(rows,list) or any(not isinstance(x,dict) for x in rows):errors.append(sid+' invalid '+field);continue
  if [x.get(key) for x in rows]!=expected:errors.append(sid+' incomplete source '+field)
  for x in rows:
   e=anchor_error(x,script,allowed)
   if e:errors.append(sid+' '+field+' '+e)
   if field=='body_beats' and x.get('surface','speech')!='speech':errors.append(sid+' body formula must be spoken')
 for key,allowed in [('payoff',body),('takeaway',body),('calling',end)]:
  a=composition.get(key);e=anchor_error(a,script,allowed)
  if e:errors.append(sid+' '+key+' '+e)
  if isinstance(a,dict) and a.get('surface','speech')!='speech':errors.append(sid+' '+key+' cannot live only in production notes')
 if composition.get('audience_question')!=plan['audience_contract']['question']:errors.append(sid+' changed audience question')
 if composition.get('primary_action')!=plan['audience_contract']['primary_action']:errors.append(sid+' changed primary action')
 # Resolve every concrete high-risk assertion against current facts. A sample disclaimer cannot legalize invented earnings.
 facts={f['id']:f for f in brief.get('facts',[])};links=script.get('claim_links',[])
 pattern=re.compile(r'(?:[零〇一二两三四五六七八九十百千万亿0-9]+(?:\.\d+)?\s*(?:美刀|美元|万元|元稿费|元订单|个客户|单成交|刀)|赚了|赚到|客户(?:从|通过|找我|付了|给了)|上周|昨天|小费)')
 for g in segs:
  for sentence in re.split(r'(?<=[。！？!?\n])',g['text']):
   if not pattern.search(sentence):continue
   matches=[c for c in links if c.get('segment_id')==g['id'] and nonblank(c.get('claim')) and c['claim'] in sentence and pattern.search(c['claim']) and c.get('evidence_id') in facts and facts[c['evidence_id']]['status'] in ('provided','verified')]
   if not matches:errors.append(sid+' uncovered factual assertion '+sentence[:45]);continue
   for amount in money_alias(sentence):
    if not any(amount in money_alias(facts[c['evidence_id']]['text']) for c in matches):errors.append(sid+' factual amount exceeds linked source')
 return errors

def text_errors(script):
 errors=[];sid=script['id']
 for g in script['segments']:
  if re.search(r'【[^】]*(?:核实后|补齐|待补|按真实|占位)[^】]*】|\{\{.+?\}\}|\bTODO\b',g['text']):errors.append(sid+' unresolved production placeholder in speech')
  if re.search(r'我把这张上传的原稿|对应到实际产品，我会这样判断|直接看这张原稿里的位置',g['text']):errors.append(sid+' assistant analysis language in speech')
 ending=script['segments'][-1]['text']
 if re.search(r'(?:评论|留言)(?:区)?(?:留|写|打|扣)?\s*[「“\"].{1,10}[」”\"]',ending) and re.search(r'下一条|下条|我就知道|优先拆|继续分享',ending):errors.append(sid+' keyword bait replacing action value')
 return errors

def diversity_errors(scripts):
 errors=[]
 for a,b in itertools.combinations(scripts,2):
  if a['platform']!=b['platform']:continue # Same case/benefit may carry across platforms; adaptation is independently reviewed.
  left=normalize(''.join(g['text'] for g in a['segments'] if g.get('role') not in ('hook','suspense','calling')));right=normalize(''.join(g['text'] for g in b['segments'] if g.get('role') not in ('hook','suspense','calling')))
  left_core=normalize(''.join(g['text'] for g in a['segments'] if g.get('role') in ('judgment','value')));right_core=normalize(''.join(g['text'] for g in b['segments'] if g.get('role') in ('judgment','value')))
  if len(left_core)>=20 and left_core==right_core:errors.append('identical judgment and payoff: '+a['id']+'/'+b['id'])
  # Diagnose substantial reuse; do not require different formulas, tone, or words for their own sake.
  if min(len(left),len(right))>=80 and SequenceMatcher(None,left,right,autojunk=False).ratio()>=.86:errors.append('substantially reused body: '+a['id']+'/'+b['id'])
 return errors

def review_errors(review,scripts,plan,pack):
 errors=[];pool={a['asset_id']:a for a in pack['assets']};plans={p['id']:p for p in plan['selected']};rows=review.get('composition_checks',[])
 if not isinstance(rows,list) or len(rows)!=len(scripts) or {r.get('script_id') for r in rows if isinstance(r,dict)}!={s['id'] for s in scripts}:return ['missing source-fidelity editorial review']
 for s in scripts:
  row=next(r for r in rows if r['script_id']==s['id']);p=plans[s['plan_id']]
  for key in ('audience_payoff','source_fidelity','action_motive','fact_scope'):
   x=row.get(key,{})
   if not isinstance(x,dict) or x.get('passed') is not True or not nonblank(x.get('reason')):errors.append(s['id']+' composition review failed '+key);continue
   e=anchor_error(x,s)
   if e:errors.append(s['id']+' review '+key+' '+e)
  source=row.get('source_comparison',{})
  a=pool[p['asset_refs']['body']['asset_id']]
  if not isinstance(source,dict) or source.get('asset_id')!=a['asset_id'] or source.get('source_quote')!=a['record']['structure'] or not nonblank(source.get('deviation_judgment')):errors.append(s['id']+' missing literal source comparison')
 return errors
