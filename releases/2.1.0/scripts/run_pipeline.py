#!/usr/bin/env python3
"""One run directory: intake, seal plan, submit versioned draft, validate, export."""
import argparse,json,sys,shutil,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
from execution_contract import read,fresh,event,check_plan,provenance,digest
from retrieve_assets import ROOT,pack
def main():
 p=argparse.ArgumentParser();p.add_argument('stage',choices=['intake','plan','draft','validate','export']);p.add_argument('--run',required=True);p.add_argument('--input');p.add_argument('--review');p.add_argument('--output');p.add_argument('--kb',help='Verified fixed-version cache; copied into RUN');p.add_argument('--request',help='Exact original request text file');p.add_argument('--source',action='append',default=[],help='Raw attachment; repeat per source');a=p.parse_args();r=Path(a.run)
 if a.stage=='intake':
  from validate_batch import schema_errors,DECISION_STAGES
  if not a.request:raise ValueError('original request file is required')
  b=read(a.input);e=schema_errors(b,read(ROOT/'schemas/brief.schema.json'))
  if b.get('decision_stage') and DECISION_STAGES.get(b['decision_stage'])!=b.get('funnel_stage'):e.append('inconsistent brief decision stage')
  if e:raise ValueError('; '.join(e))
  sources=[Path(x).resolve() for x in ([a.request] if a.request else [])+a.source]
  if any(not x.is_file() for x in sources):raise ValueError('raw source file missing')
  pack(Path(a.kb) if a.kb else ROOT/'assets/kb-snapshot',b) # Fail before creating a run if the source or locked formula is invalid.
  r.mkdir(parents=True,exist_ok=False);shutil.copytree(Path(a.kb) if a.kb else ROOT/'assets/kb-snapshot',r/'knowledge');fresh(r/'brief.json',b);fresh(r/'asset-pack.json',pack(r/'knowledge',b));files=['brief.json','asset-pack.json'];raw=[]
  for i,source in enumerate(sources,1):
   name='sources/'+str(i).zfill(2)+source.suffix;target=r/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target);raw.append({'original_name':source.name,'stored_path':name,'sha256':digest(target)});files.append(name)
  fresh(r/'source-manifest.json',{'original_request_captured':bool(a.request),'attachments_captured':len(a.source),'sources':raw,'semantic_fidelity':'REQUIRES_REVIEW_AGAINST_ORIGINAL_REQUEST','kb_manifest_sha256':digest(r/'knowledge/KB-MANIFEST.json')});files.append('source-manifest.json');event(r,'intake',files)
 elif a.stage=='plan':
  if sorted(r.glob('event-*.json'))!=[r/'event-001.json'] or list(r.glob('batch*.json')):raise ValueError('plan must precede every submitted draft; start a new run for changed brief')
  d=read(a.input);e=check_plan(d,read(r/'brief.json'),read(r/'asset-pack.json'))
  if e:raise ValueError('; '.join(e))
  fresh(r/'decision.json',d);event(r,'plan',['decision.json'])
 elif a.stage=='draft':
  if not (r/'event-002.json').is_file() or read(r/'event-002.json')['kind']!='plan':raise ValueError('seal plan before drafting')
  existing=sorted(r.glob('batch-v*.json'))
  if len(existing)>=3:raise ValueError('two revision limit; report remaining gaps')
  b=read(a.input);n=len(existing)+1;target=r/f'batch-v{n}.json';fresh(target,b);event(r,'draft' if n==1 else 'revision',[target.name]);e=provenance(r,target)
  if e:
   # Keep rejected artifact/receipt for audit; cannot silently rewrite history.
   raise ValueError('; '.join(e))
 elif a.stage in ('validate','export'):
  from validate_batch import validate
  b=Path(a.input);review=read(a.review);v=validate(read(b),review,digest(b),run_dir=r,kb=r/'knowledge')
  if a.output and a.stage=='validate':Path(a.output).write_text(json.dumps(v,ensure_ascii=False,indent=2))
  print(json.dumps(v,ensure_ascii=False))
  if not v['passed']:raise ValueError('draft not ready for reviewed export')
  if a.stage=='export':
   if not a.output:raise ValueError('missing XLSX output')
   import os
   subprocess.run([os.environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),str(ROOT/'scripts/render_spoken_xlsx.mjs'),str(b),a.review,a.output,str(r/'knowledge'),str(r)],check=True)
  return
 print(json.dumps({'stage':a.stage,'run':str(r),'recorded':True,'private_reasoning_order_proven':False}))
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as e:print(str(e),file=sys.stderr);sys.exit(2)
