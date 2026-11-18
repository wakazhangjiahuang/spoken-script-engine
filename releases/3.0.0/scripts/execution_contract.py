"""Recorded artifact order and exact bindings, not proof of private reasoning."""
import json,hashlib,os,datetime
from pathlib import Path
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def fresh(p,value):
 with Path(p).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def event(run,kind,files):
 run=Path(run);events=sorted(run.glob('event-*.json'));previous=digest(events[-1]) if events else None
 fresh(run/f'event-{len(events)+1:03}.json',{'kind':kind,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'previous':previous,'files':{x:digest(run/x) for x in files}})
def selection_errors(selected,rejected):
 policy=read(Path(__file__).resolve().parents[1]/'assets/kb-snapshot/rubrics/selection.json');errors=[]
 for group,rows in [('selected',selected),('rejected',rejected)]:
  for row in rows:
   scores=row.get('selection_scores',{});total=0
   if not scores:continue
   if not isinstance(scores,dict) or set(scores)!=set(policy['dimensions']):errors.append(group+' missing selection scores');continue
   for name,weight in policy['dimensions'].items():
    v=scores[name]
    if not isinstance(v,dict) or type(v.get('score'))!=int or v['score'] not in range(5) or not isinstance(v.get('reason'),str) or not v['reason'].strip():errors.append(group+' invalid selection score '+name);continue
    total+=v['score']*weight/4
    if group=='selected' and policy.get('minimum_each') is not None and v['score']<policy['minimum_each']:errors.append('selected low '+name)
   if group=='selected' and policy.get('minimum_total') is not None and total<policy['minimum_total']:errors.append('selected total below 80')
 return errors
def check_plan(plan,brief,pack):
 if not isinstance(plan,dict):return ['plan must be an object']
 selected=plan.get('selected',[]);rejected=plan.get('rejected',[])
 if not isinstance(selected,list) or not isinstance(rejected,list) or any(not isinstance(x,dict) for x in selected+rejected):return ['plan selected/rejected must be arrays of objects']
 fields=['id','platform','objective','buyer_decision','tension','stakes','intervention','proof','payoff','cta_reason','qualification','next_step']
 if any(not isinstance(x.get(k),str) or not x[k].strip() for x in selected for k in fields):return ['plan fields must be nonblank strings']
 if any(not isinstance(x.get('asset_refs'),dict) or any(not isinstance(x['asset_refs'].get(role),dict) for role in ['hook','body','calling','platform']) for x in selected):return ['plan asset_refs must contain four role objects']
 if any(not isinstance(x['asset_refs'][role].get(k),str) or not x['asset_refs'][role][k].strip() for x in selected for role in ['hook','body','calling','platform'] for k in ['asset_id','record_sha256','why']):return ['source references must be nonblank strings']
 errors=selection_errors(selected,rejected);ids=[x.get('id') for x in selected];pool={a['asset_id']:a for a in pack['assets']}
 if any(x.get('platform') not in brief['platforms'] for x in selected+rejected):errors.append('plan has unselected platform')
 if len(set(ids))!=len(ids):errors.append('duplicate plan IDs')
 for p in brief['platforms']:
  n=brief.get('count_per_platform',{}).get(p,3)
  if sum(x.get('platform')==p for x in selected)!=n:errors.append(p+' selected count')
  if not any(x.get('platform')==p and x.get('reason') for x in rejected):errors.append(p+' missing rejected candidate and reason')
  formulas=[x.get('asset_refs',{}).get('body',{}).get('asset_id') for x in selected if x.get('platform')==p]
  if brief.get('formula_lock'):
   if any(f!=brief['formula_lock'] for f in formulas):errors.append(p+' explicit formula lock')

 for x in selected:
  for k in ['id','platform','buyer_decision','tension','stakes','intervention','proof','payoff','cta_reason','qualification','next_step']:
   if not x.get(k):errors.append('plan missing '+k)
  if x.get('objective')!=brief['objective']:errors.append('plan changed objective')
  refs=x.get('asset_refs',{})
  for role in ['hook','body','calling','platform']:
   ref=refs.get(role,{});asset=pool.get(ref.get('asset_id'))
   if not asset or ref.get('record_sha256')!=asset['record_sha256']:errors.append('plan unmatched source '+role);continue
   if not ref.get('why'):errors.append('plan no match rationale '+role)
   path=asset['source_path']
   if role=='hook' and path!='shared/spoken-hooks.jsonl':errors.append('hook must be canonical spoken hook')
   if role=='body' and path!='shared/formulas.jsonl':errors.append('body must be canonical formula')
   if role=='body' and asset['asset_id'] in {'SHARED:F03','SHARED:F13','SHARED:F14','SHARED:F15','SHARED:F16'} and not any(m.get('status')=='available' and m.get('evidence_role') in ('proof','demonstration') for m in brief.get('production_resources',[])):errors.append('selected formula requires available evidence')
   if role=='calling' and path!='shared/cta-comment-seeds.jsonl':errors.append('calling source type')
   if role=='platform' and not path.startswith('platforms/'+x.get('platform','')+'/'):errors.append('wrong platform source')
   if role=='platform' and asset['record'].get('formula_id') and asset['record']['formula_id']!=refs.get('body',{}).get('asset_id'):errors.append('platform application formula mismatch')
   if role=='platform' and asset['record'].get('canonical_hook_id') and asset['record']['canonical_hook_id']!=refs.get('hook',{}).get('asset_id'):errors.append('platform application hook mismatch')
   if role=='calling' and brief['objective'] in ('inquiry','purchase') and asset['record'].get('objective')!=brief['objective']:errors.append('business CTA asset mismatch')
 from composition_contract import plan_errors
 errors.extend(plan_errors(plan,brief,pack))
 from illustration_contract import plan_errors as information_plan_errors
 errors.extend(information_plan_errors(plan,brief,pack))
 from surface_contract import plan_errors as opening_plan_errors
 errors.extend(opening_plan_errors(plan,brief,pack))
 return errors
def provenance(run,batch_path=None):
 run=Path(run);errors=[];events=sorted(run.glob('event-*.json'));previous=None;seen=[]
 if not events:return ['no stage receipts']
 for i,p in enumerate(events):
  e=read(p);kind=e.get('kind');files=e.get('files',{})
  if not isinstance(files,dict):errors.append('invalid receipt files');continue
  expected_kind='intake' if i==0 else 'plan' if i==1 else 'draft' if i==2 else 'revision'
  if kind!=expected_kind or i>4:errors.append('invalid receipt stage order')
  required={'brief.json','asset-pack.json','source-manifest.json'} if i==0 else {'decision.json'} if i==1 else {f'batch-v{i-1}.json'}
  if not required<=set(files):errors.append('missing required receipt binding '+str(kind))
  if e.get('previous')!=previous:errors.append('broken receipt chain')
  for name,sha in files.items():
   target=(run/name).resolve()
   if not target.is_relative_to(run.resolve()) or not target.is_file() or digest(target)!=sha:errors.append('modified stage artifact '+name)
  previous=digest(p);seen.append(kind)
 if len(events)<3:errors.append('required intake→plan→draft order absent')
 if errors:return errors
 sm=read(run/'source-manifest.json');raw=sm.get('sources',[]);intake_files=read(events[0])['files']
 if sm.get('original_request_captured') is not True or not raw:errors.append('original request absent from source manifest')
 if len(raw)!=1+sm.get('attachments_captured',-1):errors.append('raw source count mismatch')
 for source in raw:
  name=source.get('stored_path');sha=source.get('sha256')
  if not isinstance(name,str) or not name.startswith('sources/') or name not in intake_files or intake_files[name]!=sha:errors.append('raw source not sealed in intake')
 km=run/'knowledge/KB-MANIFEST.json'
 if not km.is_file() or not sm.get('kb_manifest_sha256') or digest(km)!=sm['kb_manifest_sha256']:errors.append('run knowledge manifest changed or absent')
 if errors:return errors
 b=read(batch_path) if batch_path else None;brief=read(run/'brief.json');pack=read(run/'asset-pack.json');plan=read(run/'decision.json')
 if pack['brief_sha256']!=canonical(brief):errors.append('retrieval brief changed')
 errors+=check_plan(plan,brief,pack)
 if b:
  if canonical(b['brief'])!=canonical(brief):errors.append('draft changed locked brief')
  accepted=[h for e in events for n,h in read(e)['files'].items() if n.startswith('batch-v')]
  if digest(batch_path) not in accepted:errors.append('batch was not submitted after plan')
  drafts=[e for e in events if read(e)['kind'] in ('draft','revision')]
  if drafts and digest(batch_path) not in read(drafts[-1])['files'].values():errors.append('stale draft revision')
  selected={x['id']:x for x in plan['selected']}
  submitted=[x.get('plan_id') for x in b['scripts']]
  if len(submitted)!=len(selected) or len(set(submitted))!=len(submitted) or set(submitted)!=set(selected):errors.append('selected plans must be consumed exactly once')
  for s in b['scripts']:
   p=selected.get(s.get('plan_id'))
   if not p:errors.append('unknown plan '+s['id']);continue
   if p['platform']!=s['platform'] or p['asset_refs']['body']['asset_id']!=s['formula_id'] or p['asset_refs']['hook']['asset_id']!=s['hook_id']:errors.append('draft changed selected mechanism '+s['id'])
   roles=set()
   for a in s.get('asset_applications',[]):
    roles.add(a['role']);g=next((x for x in s['segments'] if x['id']==a['segment_id']),None);ref=p['asset_refs'].get(a['role'],{})
    if a['asset_id']!=ref.get('asset_id') or not g or a['quote'] not in g['text']:errors.append('unbound asset application '+s['id'])
   if not {'hook','body','calling'}<=roles:errors.append('missing substantive asset application '+s['id'])
   if s['calling'].get('intent')!=brief['objective']:errors.append('draft Calling changed objective '+s['id'])
   from composition_contract import draft_errors
   errors.extend(draft_errors(s,p,pack,brief))
   from illustration_contract import draft_errors as information_draft_errors
   errors.extend(information_draft_errors(s,p,pack,brief))
   from surface_contract import draft_errors as surface_errors
   errors.extend(surface_errors(s,p,plan))
 return errors
