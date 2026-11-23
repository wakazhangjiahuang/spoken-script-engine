#!/usr/bin/env python3
"""v3.4.4 authoritative entrypoint: source binding + spoken-depth + domain review."""
from __future__ import annotations
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))
from asset_path_bootstrap import ensure_asset_aliases
from content_decision_gate_v342 import (build_source_registry,validate_plan,validate_batch,
    validate_illustration_review,verify_external_evidence)
from content_depth_gate_v344 import validate_content_depth
from validate_v41 import validate as validate_v41_review

def _args():
 p=argparse.ArgumentParser(add_help=False);p.add_argument('stage',choices=['intake','plan','draft','validate','export'])
 p.add_argument('--run',required=True);p.add_argument('--input');p.add_argument('--request');p.add_argument('--review')
 p.add_argument('--v41-review');p.add_argument('--output');p.add_argument('--require-v41-full-validation',action='store_true')
 return p.parse_known_args()[0]
def _read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def _domain(brief):
 d=str(brief.get('domain','')).strip().lower().replace('-','_')
 if d in {'ai_video','ai_video_business','aivideo','ai视频','ai视频业务'} or brief.get('quality_profile')=='ai_video_v4_1': return 'ai_video'
 if d in {'illustration','print_design','illustration_surface_pattern_textile_print'}: return 'illustration'
 return d or 'general'
def _patch_asset_routes():
 import illustration_assets_v2,ai_video_assets_v2
 original=illustration_assets_v2.active
 def active_v344(brief):
  domain=str(brief.get('domain','')).lower().replace('-','_');topic=str(brief.get('topic',''))
  return original(brief) or (domain=='design_service' and any(x in topic for x in ('插画','印花')))
 illustration_assets_v2.active=active_v344
 from illustration_assets_v2_v342 import pack_illustration
 from ai_video_assets_v2_v342 import stage_domain_assets
 illustration_assets_v2.pack_illustration=pack_illustration
 ai_video_assets_v2.stage_domain_assets=stage_domain_assets
def _context(run,brief):
 pack_path=run/'asset-pack.json';pack=_read(pack_path) if pack_path.is_file() else {}
 return pack,build_source_registry(ROOT,run,brief,pack)
def _guidance_errors(run,brief,pack):
 domain=_domain(brief);guidance=pack.get('must_read_guidance',{}) if isinstance(pack,dict) else {};errors=[]
 if domain=='illustration':
  required={'ILLUSTRATION-GUIDANCE-V2.0','COVER-TITLE-GUIDE-V4'}
  loaded={v.get('source_asset_id') for v in guidance.values() if isinstance(v,dict) and v.get('text')}
  if not required.issubset(loaded):errors.append('ILLUSTRATION_CURRENT_GUIDANCE_OR_TITLE_V4_NOT_LOADED')
  if pack.get('domain_asset_manifest',{}).get('legacy_platform_examples_loaded')!=0:errors.append('ILLUSTRATION_LEGACY_PLATFORM_EXAMPLES_NOT_EXCLUDED')
 elif domain=='ai_video':
  required={'AI-VIDEO-BUSINESS-GUIDE-V4.1','AI-VIDEO-TEAM-GUIDE-20261123'}
  loaded={v.get('source_asset_id') for v in guidance.values() if isinstance(v,dict) and v.get('text')}
  if not required.issubset(loaded):errors.append('AI_VIDEO_V4_1_BUSINESS_GUIDE_OR_CURRENT_TEAM_GUIDE_NOT_LOADED')
  dm_path=run/'domain-asset-manifest.json'
  if not dm_path.is_file():errors.append('AI_VIDEO_DOMAIN_ASSET_MANIFEST_MISSING')
  else:
   if not required.issubset(set(_read(dm_path).get('must_read_source_asset_ids',[]))):errors.append('AI_VIDEO_CURRENT_GUIDANCE_NOT_IN_MUST_READ_ROUTE')
 return errors
def _preflight(a):
 run=Path(a.run).resolve();bp=run/'brief.json';brief=_read(bp) if bp.is_file() else {}
 if not brief and a.request and Path(a.request).is_file():
  req=_read(a.request);brief=req.get('brief',req) if isinstance(req,dict) else {}
 domain=_domain(brief);ensure_asset_aliases(ROOT,run,domain=domain)
 if a.stage=='intake':return
 pack,registry=_context(run,brief);ge=_guidance_errors(run,brief,pack)
 if ge:raise SystemExit('v3.4.4 source-loading preflight blocked:\n- '+'\n- '.join(ge))
 dp=run/'decision.json';decision=_read(dp) if dp.is_file() else {}
 if a.stage=='plan':
  if not a.input:raise ValueError('plan requires --input decision JSON')
  errs=validate_plan(_read(a.input),brief,registry)
  if errs:raise SystemExit('v3.4.4 plan source-binding blocked:\n- '+'\n- '.join(errs))
  return
 if a.stage=='draft':
  errs=validate_plan(decision,brief,registry)
  if errs:raise SystemExit('v3.4.4 sealed plan source-binding blocked:\n- '+'\n- '.join(errs))
  return
 if a.stage not in ('validate','export'):return
 if not a.input:raise ValueError('validate/export requires --input batch JSON')
 batch=_read(a.input);sm=_read(run/'source-manifest.json') if (run/'source-manifest.json').is_file() else {}
 errors=validate_batch(batch,brief,pack,decision,registry,sm)
 if domain=='ai_video':
  if not a.v41_review:errors.append('AI_VIDEO_V4_1_REVIEW_REQUIRED')
  else:
   review=_read(a.v41_review)
   raw_sha=hashlib.sha256(Path(a.input).read_bytes()).hexdigest()
   payload_sha=hashlib.sha256(json.dumps(batch,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
   if review.get('batch_sha256') not in (raw_sha,payload_sha):errors.append('AI_VIDEO_V4_1_REVIEW_NOT_BOUND_TO_BATCH_BYTES')
   review['batch_sha256_payload']=payload_sha
   result=validate_v41_review(batch,review)
   if result.get('status') in ('NEEDS_REVISION','INVALID_INPUT'):
    errors.extend(['AI_VIDEO_V4_1_FORMAL_VALIDATOR:'+x for x in result.get('errors',[])])
   if a.require_v41_full_validation and result.get('status')!='PASS':
    errors.append('AI_VIDEO_FULL_VALIDATION_REQUIRED:'+str(result.get('status')))
   depth,_=validate_content_depth(batch,review,'ai_video');errors.extend(depth)
   errors.extend(verify_external_evidence(review,run))
 elif domain=='illustration':
  sp=run/'illustration-review.json'
  if not sp.is_file():errors.append('ILLUSTRATION_SCORECARD_MISSING')
  else:
   review=_read(sp);errors.extend(validate_illustration_review(batch,review,Path(a.input)))
   depth,_=validate_content_depth(batch,review,'illustration');errors.extend(depth)
   errors.extend(verify_external_evidence(review,run))
 if errors:raise SystemExit('v3.4.4 content-quality preflight blocked:\n- '+'\n- '.join(errors))
def _postflight(a):
 run=Path(a.run).resolve()
 if a.stage=='intake':
  errors=_guidance_errors(run,_read(run/'brief.json'),_read(run/'asset-pack.json'))
  if errors:raise SystemExit('v3.4.4 intake did not load current guidance:\n- '+'\n- '.join(errors))
 elif a.stage=='plan':
  brief=_read(run/'brief.json');_,registry=_context(run,brief);errors=validate_plan(_read(run/'decision.json'),brief,registry)
  if errors:raise SystemExit('v3.4.4 sealed plan failed source binding:\n- '+'\n- '.join(errors))
 elif a.stage=='draft':
  brief=_read(run/'brief.json');pack,registry=_context(run,brief)
  batches=sorted(run.glob('batch-v*.json'),key=lambda p:int(__import__('re').search(r'v(\d+)',p.stem).group(1)) if __import__('re').search(r'v(\d+)',p.stem) else -1)
  if not batches:raise ValueError('draft stage did not create a versioned batch')
  sm=_read(run/'source-manifest.json') if (run/'source-manifest.json').is_file() else {}
  errors=validate_batch(_read(batches[-1]),brief,pack,_read(run/'decision.json'),registry,sm)
  if errors:raise SystemExit('v3.4.4 draft failed source/decision gate:\n- '+'\n- '.join(errors))
def main():
 a=_args();_patch_asset_routes();_preflight(a)
 import run_pipeline_v3
 run_pipeline_v3.main();_postflight(a)
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,OSError,zipfile.BadZipFile) as exc:
  print(str(exc),file=sys.stderr);raise SystemExit(2)
