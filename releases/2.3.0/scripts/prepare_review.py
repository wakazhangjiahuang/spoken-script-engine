#!/usr/bin/env python3
"""Prepare a blind editorial view; bind original bytes, never expose producer selection scores."""
import json,argparse,hashlib,copy
from pathlib import Path
REMOVED={'selection_scores','内部评分','评分简评','historical_score_not_current'}
def clean(value):
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in REMOVED}
 if isinstance(value,list):return [clean(v) for v in value]
 return value
def prepare(run,batch,phase='content',content_review=None):
 run=Path(run);batch=Path(batch)
 from execution_contract import provenance
 errors=provenance(run,batch)
 if errors:raise ValueError('Cannot review a structurally rejected or unbound draft: '+'; '.join(errors))
 def read(p):return json.loads(p.read_text())
 def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 from surface_contract import delivery_packet
 b=read(batch);brief=read(run/'brief.json');pack=read(run/'asset-pack.json');sm=read(run/'source-manifest.json')
 data={'review_input_version':'2.3.0','phase':phase,'blinding':{'producer_selection_scores':'REMOVED','producer_payoff_explanations':'HIDDEN_UNTIL_CONTENT_JUDGEMENT','review_scope':'Independent model editing, not target-user or published performance'},'bindings':{'batch_sha256':h(batch),'decision_sha256':h(run/'decision.json'),'asset_pack_sha256':h(run/'asset-pack.json')},'actual_request':(run/sm['sources'][0]['stored_path']).read_text(),'production_resources':brief['production_resources'],'deliverables':[delivery_packet(s) for s in b['scripts']],'source_manifest':sm,'source_directory':str((run/'sources').resolve()),'rubric':pack['rubric'],'domain_standard':{k:v for k,v in pack.get('must_read_guidance',{}).items() if k.startswith('domains/')}}
 if phase=='fidelity':
  if not content_review:raise ValueError('record the visible-delivery content judgement before revealing the production plan')
  r=read(content_review)
  if r.get('batch_sha256')!=h(batch) or r.get('reviewer',{}).get('independent') is not True:raise ValueError('content judgement is not independently bound to this batch')
  decisions=r.get('content_decisions',[])
  if {x.get('script_id') for x in decisions}!={s['id'] for s in b['scripts']} or any(x.get('verdict')!='DRAFT_FOR_USER_REVIEW' for x in decisions):raise ValueError('rewrite rejected content before formula-fidelity review')
  data.update(content_review_sha256=h(content_review),brief=brief,plan=clean(read(run/'decision.json')),asset_pack=clean(pack),batch=clean(b))
 elif phase!='content':raise ValueError('unknown review phase')
 return data
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--batch',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--phase',choices=['content','fidelity'],default='content');p.add_argument('--content-review',type=Path);a=p.parse_args()
 try:
  payload=prepare(a.run,a.batch,a.phase,a.content_review)
  a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps({'review_input':str(a.output),'producer_scores':'REMOVED','original_bindings':'PRESERVED'}))
 except ValueError as e:p.exit(2,str(e)+'\n')
