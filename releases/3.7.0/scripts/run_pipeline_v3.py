#!/usr/bin/env python3
"""Authoritative v3.3.0 entrypoint. Wraps legacy pipeline with current domain routing and hard release gates."""
from __future__ import annotations
import argparse, json, sys, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(HERE))

def parse_args():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument('stage',choices=['intake','plan','draft','validate','export'])
    p.add_argument('--run',required=True); p.add_argument('--input'); p.add_argument('--review'); p.add_argument('--output'); p.add_argument('--kb'); p.add_argument('--request'); p.add_argument('--source',action='append',default=[])
    p.add_argument('--v41-review'); p.add_argument('--v41-report'); p.add_argument('--require-v41-full-validation',action='store_true')
    return p.parse_known_args()[0]

def call_core(core, argv):
    old=sys.argv[:]
    try:
        sys.argv=argv
        core.main()
    finally:
        sys.argv=old

def uses_historical_illustration_workbook(run):
    receipt = run / "event-001.json"
    return not receipt.is_file() or json.loads(receipt.read_text(encoding="utf-8")).get("task_mode") != "B"


def main():
    a=parse_args(); run=Path(a.run).resolve()
    # Patch current asset routing before importing the core pipeline (which imports functions by value).
    import retrieve_assets
    from illustration_assets_v2 import active as is_illustration, pack_illustration
    base_pack=retrieve_assets.pack
    def current_pack(kb,brief):
        p=base_pack(kb,brief)
        return pack_illustration(p,brief) if is_illustration(brief) else p
    retrieve_assets.pack=current_pack
    import illustration_contract
    import illustration_contract_v2 as iv2
    for name in ('active','intake_errors','plan_errors','draft_errors','review_errors'):
        setattr(illustration_contract,name,getattr(iv2,name))
    import ai_video_assets
    import ai_video_assets_v2
    ai_video_assets.stage_domain_assets=ai_video_assets_v2.stage_domain_assets
    ai_video_assets.record_sample_retrieval=ai_video_assets_v2.record_sample_retrieval
    import run_pipeline as core
    brief_path=run/'brief.json'
    illustration=is_illustration(json.loads(brief_path.read_text(encoding='utf-8'))) if brief_path.is_file() else False
    if a.stage=='export' and illustration and uses_historical_illustration_workbook(run):
        if not a.input or not a.review or not a.output: raise ValueError('illustration export requires --input --review --output')
        # Run the generic validation stage first; do not invoke the legacy five-sheet renderer.
        report=run/'generic-validation.json'
        args=[sys.argv[0],'validate','--run',str(run),'--input',str(Path(a.input).resolve()),'--review',str(Path(a.review).resolve()),'--output',str(report)]
        if a.kb: args += ['--kb',a.kb]
        call_core(core,args)
        from validate_illustration_run import validate as validate_run
        v=validate_run(run,a.input,a.review)
        if not v['passed']: raise SystemExit(2)
        production=run/'illustration-production.json'
        if not production.is_file(): raise ValueError('illustration-production.json missing; 04/05 execution cards cannot be guessed')
        from export_illustration_workbook import render
        render(a.input,production,a.output)
        from export_illustration_workbook import update_overview
        update_overview(a.output,publication_status=v['publication_status'],export_status='PASS')
        from validate_illustration_workbook import validate as validate_wb
        w=validate_wb(a.output,ROOT/'assets/illustration/source/1118illustration_spoken_原表保留_补充18篇_V2.0.xlsx')
        Path(str(a.output)+'.validation.json').write_text(json.dumps(w,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if not w['passed']: raise SystemExit(2)
        print(json.dumps({'status':v['publication_status'],'editorial_status':v['editorial_status'],'workbook_validation':'PASS','output':a.output},ensure_ascii=False,indent=2))
        return
    if a.stage in ('validate', 'export') and illustration and not uses_historical_illustration_workbook(run):
        if not a.input or not a.review:
            raise ValueError('illustration validation requires --input and --review')
        from validate_illustration_run import validate as validate_run
        result = validate_run(run, a.input, a.review, historical=False)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result['passed']:
            raise SystemExit(2)
    # All other stages and domains use the existing core pipeline plus patched current assets/contracts.
    call_core(core,sys.argv[:])
    if a.stage=='validate' and illustration and uses_historical_illustration_workbook(run):
        if not a.input or not a.review: raise ValueError('illustration validation requires --input and --review')
        from validate_illustration_run import validate as validate_run
        result=validate_run(run,a.input,a.review)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if not result['passed']: raise SystemExit(2)

if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as e:
        print(str(e),file=sys.stderr); raise SystemExit(2)
