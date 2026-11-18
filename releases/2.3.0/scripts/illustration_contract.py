"""Domain-specific information-value checks. Semantic relevance still requires independent editing."""
import re
from composition_contract import nonblank,anchor_error
INFO={'user_project','official_product','market_research','original_development','explicit_technical_tutorial','behind_scenes'}
CLASSES={'user_project','official_product','research','original_work','historical_example','hypothetical'}
def active(brief):
 domain=brief.get('domain')
 if domain:return domain in ('illustration','design_service')
 return bool(re.search('插画|印花|母婴图案|床品图案',brief.get('topic','')))
def intake_errors(brief):
 if not active(brief):return []
 c=brief.get('audience_information',{});errors=[]
 if not isinstance(c,dict) or any(not nonblank(c.get(k)) for k in ('primary_role','current_problem','direct_benefit','information_type','source_class')):return ['illustration audience-information brief missing']
 if c['primary_role'] not in ('designer','beginner','brand_factory','trader') or c['information_type'] not in INFO or c['source_class'] not in CLASSES:errors.append('illustration brief invalid audience/information class')
 if c['information_type']=='explicit_technical_tutorial':
  if brief.get('explicit_technical_tutorial') is not True:errors.append('technical tutorial must be explicitly requested')
  if not any(x.get('status')=='available' and x.get('evidence_role')=='demonstration' for x in brief.get('production_resources',[])):errors.append('technical tutorial needs available visible demonstration')
 if c['source_class']=='user_project' and not any(f.get('evidence_class')=='user_project' for f in brief.get('facts',[])):errors.append('user project must come from current user-project facts, not an example')
 return errors
def plan_errors(plan,brief,pack):
 if not pack.get('domain_profile'):return []
 errors=intake_errors(brief);pool={a['asset_id']:a for a in pack['assets']}
 for p in plan.get('selected',[]):
  sid=p['id'];c=p.get('information_contract',{});b=brief.get('audience_information',{})
  if not isinstance(c,dict) or any(not nonblank(c.get(k)) for k in ('primary_role','opening_benefit','new_fact','viewer_use','information_type','source_class','tool_position')):errors.append(sid+' information-value plan missing');continue
  if any(c[k]!=b.get(k) for k in ('primary_role','information_type','source_class')):errors.append(sid+' information/audience plan changed brief')
  if c['tool_position'] not in ('support','explicit_tutorial'):errors.append(sid+' invalid tool position')
  if c['tool_position']=='explicit_tutorial' and brief.get('explicit_technical_tutorial') is not True:errors.append(sid+' tool became unrequested tutorial')
  r=p.get('source_recipe',{}).get('opening_reference',{});a=pool.get(r.get('asset_id')) if isinstance(r,dict) else None
  if not a or a['record'].get('type')!='domain_opening_reference' or r.get('record_sha256')!=a['record_sha256']:errors.append(sid+' domain opening reference missing')
  elif r.get('source_quote')!=a['record']['opening'] or not nonblank(r.get('adaptation')):errors.append(sid+' domain opening source mismatch')
  elif a['record']['source_class']!=c['source_class']:errors.append(sid+' wrong evidence class for opening reference')
 return errors
def draft_errors(script,plan,pack,brief):
 if not pack.get('domain_profile'):return []
 errors=[];sid=script['id'];d=script.get('information_delivery',{});c=plan['information_contract'];segs=script['segments'];body={g['id'] for g in segs[1:-1]}
 if not isinstance(d,dict):return [sid+' information delivery missing']
 for key,allowed in [('opening_benefit',{segs[0]['id']}),('new_fact',{segs[1]['id']}),('viewer_use',body)]:
  a=d.get(key);e=anchor_error(a,script,allowed)
  if e:errors.append(sid+' information '+key+' '+e)
  if isinstance(a,dict) and a.get('surface','speech')!='speech':errors.append(sid+' information value must be spoken')
 for k in ('primary_role','source_class','tool_position'):
  if d.get(k)!=c[k]:errors.append(sid+' changed information '+k)
 facts={f['id']:f for f in brief['facts']};opening=d.get('opening_fact_ids',[]);fresh=d.get('new_fact_ids',[])
 if not isinstance(opening,list) or not isinstance(fresh,list) or not fresh or any(i not in facts for i in opening+fresh):errors.append(sid+' missing current new-fact references')
 elif not set(fresh)-set(opening):errors.append(sid+' no new fact after opening')
 else:
  quote=d.get('new_fact',{}).get('quote','')
  for i in fresh:
   terms=facts[i].get('anchor_terms',[])
   if terms and not any(term in quote for term in terms):errors.append(sid+' new fact not in second spoken block: '+i)
 return errors
def review_errors(review,scripts,pack):
 if not pack.get('domain_profile'):return []
 rows=review.get('information_checks',[]);errors=[]
 if not isinstance(rows,list) or len(rows)!=len(scripts) or {r.get('script_id') for r in rows if isinstance(r,dict)}!={s['id'] for s in scripts}:return ['independent information-value review missing']
 for s in scripts:
  r=next(x for x in rows if x['script_id']==s['id'])
  for k in ('opening_value','new_fact','story_decision','viewer_use','calling_input'):
   a=r.get(k,{})
   if not isinstance(a,dict) or a.get('passed') is not True or not nonblank(a.get('reason')):errors.append(s['id']+' information review failed '+k);continue
   roles={'opening_value':{'hook'},'new_fact':{'suspense'},'story_decision':{'context','judgment','value'},'viewer_use':{'judgment','value'},'calling_input':{'calling'}}
   allowed={g['id'] for g in s['segments'] if g['role'] in roles[k]}
   e=anchor_error(a,s,allowed)
   if e:errors.append(s['id']+' information review '+k+' '+e)
   if a.get('surface','speech')!='speech':errors.append(s['id']+' information review must quote speech '+k)
 return errors
