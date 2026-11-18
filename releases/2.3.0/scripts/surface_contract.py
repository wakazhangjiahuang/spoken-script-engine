"""Eight deliverables and blinded opening handoff. Checks bindings, never predicts clicks."""
import hashlib,json
from composition_contract import nonblank
OPENING_CHECKS=('self_relevance','valuable_information','specific_opportunity','continuation','cover_fidelity','fact_scope')
SURFACES=('cover_main','cover_sub','hook','suspense','body','calling','storyboard','comment_hook')
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def first8_packet(candidates,brief):
 # Deliberately exclude the producer's motivation/payoff, plan, scores, and preferred candidate.
 keys=('id','plan_id','platform','mechanism_id','cover_main','cover_sub','hook','suspense','first_shot','proof_fact_ids')
 return {'version':'2.3.0','target_audience':brief['audience'],'candidates':[{k:c[k] for k in keys if k in c} for c in candidates]}
def candidate_surface(candidate,surface):
 if surface=='first_shot':return candidate.get('first_shot',{}).get('visual','')
 return candidate.get(surface,'') if surface in ('cover_main','cover_sub','hook','suspense') else ''
def plan_errors(plan,brief,pack):
 if not pack.get('domain_profile'):return []
 candidates=plan.get('opening_candidates');review=plan.get('opening_review');errors=[]
 if not isinstance(candidates,list) or not candidates or not isinstance(review,dict):return ['opening candidates and independent first8 review required before plan']
 ids=[c.get('id') for c in candidates if isinstance(c,dict)]
 if len(ids)!=len(candidates) or len(set(ids))!=len(ids):return ['opening candidate IDs invalid/duplicate']
 facts={f['id'] for f in brief['facts']};resources={r['id'] for r in brief['production_resources']};pool={a['asset_id']:a for a in pack['assets']}
 for c in candidates:
  if any(not nonblank(c.get(k)) for k in ('id','plan_id','platform','mechanism_id','cover_main','cover_sub','hook','suspense')):errors.append('opening candidate has blank public deliverable')
  if c.get('platform') not in brief['platforms'] or pool.get(c.get('mechanism_id'),{}).get('source_path')!='shared/spoken-hooks.jsonl':errors.append('opening candidate platform/mechanism unmatched')
  shot=c.get('first_shot',{})
  if not isinstance(shot,dict) or not nonblank(shot.get('visual')) or shot.get('material_id') not in resources:errors.append('opening candidate first-shot resource/focus missing')
  if not isinstance(c.get('proof_fact_ids'),list) or not c['proof_fact_ids'] or not set(c['proof_fact_ids'])<=facts:errors.append('opening candidate current proof facts missing')
 if review.get('panel_sha256')!=canonical(first8_packet(candidates,brief)):errors.append('opening review not bound to raw first8 panel')
 who=review.get('reviewer',{})
 if who.get('independent') is not True or not nonblank(who.get('identity')):errors.append('independent first8 reviewer missing')
 rows=review.get('items',[])
 if not isinstance(rows,list) or {r.get('candidate_id') for r in rows if isinstance(r,dict)}!=set(ids) or len(rows)!=len(ids):return errors+['opening review candidates mismatch']
 byid={c['id']:c for c in candidates};reports={r['candidate_id']:r for r in rows}
 for p in plan.get('selected',[]):
  own=[c for c in candidates if c.get('plan_id')==p['id']]
  if len(own)<2 or len({c.get('mechanism_id') for c in own})<2:errors.append(p['id']+' needs at least two genuinely different opening mechanisms')
  chosen=byid.get(p.get('opening_candidate_id'));r=reports.get(p.get('opening_candidate_id'),{})
  if not chosen or chosen.get('plan_id')!=p['id'] or chosen['platform']!=p['platform']:errors.append(p['id']+' selected opening mismatch');continue
  if chosen['mechanism_id']!=p['asset_refs']['hook']['asset_id']:errors.append(p['id']+' selected opening mechanism changed')
  if r.get('verdict')!='RECOMMEND_FOR_DRAFT':errors.append(p['id']+' first8 must be rewritten before full draft')
  if not all(nonblank(r.get(k)) for k in ('viewer_restatement','reason_to_watch','reason_to_continue')):errors.append(p['id']+' raw first8 viewer judgement missing')
  for k in OPENING_CHECKS:
   a=r.get('checks',{}).get(k,{})
   if a.get('passed') is not True or not nonblank(a.get('reason')):errors.append(p['id']+' first8 rejected '+k);continue
   if k=='self_relevance' and a.get('surface')!='hook':errors.append(p['id']+' self relevance must be in actual first spoken sentence')
   if k=='continuation' and a.get('surface')!='suspense':errors.append(p['id']+' continuation must be in actual second spoken block')
   actual=candidate_surface(chosen,a.get('surface'))
   if not nonblank(a.get('quote')) or a['quote'] not in actual:errors.append(p['id']+' first8 quote absent '+k)
 return errors
def draft_errors(script,plan=None,document=None):
 errors=[];sid=script['id']
 for k in ('cover_main','cover_sub'):
  if not nonblank(script.get(k)):errors.append(sid+' explicit '+k+' required; publish title is not a cover subtitle')
 if script.get('cover_main')==script.get('cover_sub'):errors.append(sid+' cover main/sub merely duplicate')
 comment=script.get('comment_hook',{})
 if not isinstance(comment,dict) or any(not nonblank(comment.get(k)) for k in ('line','viewer_reason','input','next_step','intent','placement')):errors.append(sid+' separate comment hook contract missing')
 elif comment['intent']!=script.get('calling',{}).get('intent'):errors.append(sid+' comment hook changed business intent')
 elif comment['placement'] not in ('ending','pinned_comment'):errors.append(sid+' invalid comment placement')
 elif comment['placement']=='ending' and comment['line'] not in script['segments'][-1]['text']:errors.append(sid+' ending comment hook not actually spoken')
 if plan and plan.get('opening_candidate_id') and document:
  chosen=next((c for c in document.get('opening_candidates',[]) if c['id']==plan['opening_candidate_id']),{})
  actual={'cover_main':script.get('cover_main'),'cover_sub':script.get('cover_sub'),'hook':script['segments'][0]['text'],'suspense':script['segments'][1]['text']}
  if any(actual[k]!=chosen.get(k) for k in actual):errors.append(sid+' changed reviewed first8 deliverable; re-review opening')
  if script['segments'][0]['visual']!=chosen.get('first_shot',{}).get('visual'):errors.append(sid+' changed reviewed first-shot evidence')
 return errors
def delivery_packet(script):
 return {'id':script['id'],'platform':script['platform'],'target_audience':script['audience'],'publish_title':script['title'],'cover_main':script.get('cover_main'),'cover_sub':script.get('cover_sub'),'segments':[{k:g[k] for k in ('id','role','text','visual','subtitle','shot') if k in g} for g in script['segments']],'comment_hook':script.get('comment_hook')}
def review_errors(review,scripts):
 rows=review.get('delivery_checks',[]);errors=[]
 if not isinstance(rows,list) or len(rows)!=len(scripts) or {r.get('script_id') for r in rows if isinstance(r,dict)}!={s['id'] for s in scripts}:return ['eight-deliverable content review missing']
 for s in scripts:
  r=next(x for x in rows if x['script_id']==s['id']);segs=s['segments']
  values={'cover_main':s.get('cover_main',''),'cover_sub':s.get('cover_sub',''),'hook':segs[0]['text'],'suspense':segs[1]['text'],'body':'\n'.join(g['text'] for g in segs[2:-1]),'calling':segs[-1]['text'],'storyboard':'\n'.join(g['visual']+'\n'+g['shot']['action'] for g in segs),'comment_hook':s.get('comment_hook',{}).get('line','')}
  if r.get('delivery_sha256')!=canonical(delivery_packet(s)):errors.append(s['id']+' content review not bound to visible delivery')
  for key in SURFACES:
   a=r.get(key,{})
   if a.get('passed') is not True or not nonblank(a.get('reason')):errors.append(s['id']+' rejected deliverable '+key)
   if not nonblank(a.get('quote')) or a['quote'] not in values[key]:errors.append(s['id']+' delivery review quote absent '+key)
 return errors
