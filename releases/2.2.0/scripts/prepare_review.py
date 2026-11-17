#!/usr/bin/env python3
"""Prepare a blind editorial view; bind original bytes, never expose producer selection scores."""
import json,argparse,hashlib,copy
from pathlib import Path
REMOVED={'selection_scores','内部评分','评分简评','historical_score_not_current'}
def clean(value):
 if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in REMOVED}
 if isinstance(value,list):return [clean(v) for v in value]
 return value
def prepare(run,batch):
 run=Path(run);batch=Path(batch)
 from execution_contract import provenance
 errors=provenance(run,batch)
 if errors:raise ValueError('Cannot review a structurally rejected or unbound draft: '+'; '.join(errors))
 def read(p):return json.loads(p.read_text())
 def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 data={'review_input_version':'2.2.0','blinding':{'producer_selection_scores':'REMOVED','reference_numeric_scores':'REMOVED','review_scope':'Independent model editing, not target-user or published performance'},'bindings':{'batch_sha256':h(batch),'decision_sha256':h(run/'decision.json'),'asset_pack_sha256':h(run/'asset-pack.json')},'brief':read(run/'brief.json'),'plan':clean(read(run/'decision.json')),'asset_pack':clean(read(run/'asset-pack.json')),'batch':read(batch),'source_manifest':read(run/'source-manifest.json'),'source_directory':str(run/'sources')}
 return data
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--batch',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 try:
  payload=prepare(a.run,a.batch)
  a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2));print(json.dumps({'review_input':str(a.output),'producer_scores':'REMOVED','original_bindings':'PRESERVED'}))
 except ValueError as e:p.exit(2,str(e)+'\n')
