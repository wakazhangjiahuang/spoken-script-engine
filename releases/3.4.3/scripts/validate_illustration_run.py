#!/usr/bin/env python3
"""Per-script editorial scorecard and non-compensatory release gates for illustration V2.0."""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WEIGHTS={'audience_and_task':15,'entry_and_click_reason':15,'first_8_seconds':15,'professional_judgment_and_payoff':20,'facts_evidence_and_rights':15,'platform_native_expression':10,'calling_and_action':5,'spoken_naturalness':5}
PLATFORMS={'抖音':6,'微信视频号':6,'小红书':6}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def validate(run_dir,batch_path,review_path):
    run=Path(run_dir); errors=[]; warnings=[]
    brief=read(run/'brief.json'); decision=read(run/'decision.json'); pack=read(run/'asset-pack.json'); batch=read(batch_path); review=read(review_path)
    if brief.get('domain') not in ('illustration','print_design') and 'ILLUSTRATION-GUIDANCE-V2.0' not in set(pack.get('domain_asset_manifest',{}).get('required_source_asset_ids',[])): errors.append('run domain is not illustration')
    sr=decision.get('source_retrieval',{})
    conn=read(ROOT/'assets/connection-config.json')
    pinned=conn.get('spoken',{})
    if sr.get('retrieval_status') not in ('VERIFIED','OFFLINE_PINNED_FALLBACK'): errors.append('GitHub source retrieval not verified/pinned')
    if sr.get('retrieval_status')=='OFFLINE_PINNED_FALLBACK' and sr.get('offline_bundle_sha_verified') is not True: errors.append('offline fallback lacks full private-bundle SHA verification')
    if sr.get('asset_ref')!=pinned.get('asset_ref'): errors.append('GitHub active asset_ref differs from pinned connection-config')
    if sr.get('manifest_ref')!=pinned.get('manifest_ref'): errors.append('GitHub sample manifest_ref differs from pinned connection-config')
    if not sr.get('registry_sha256'): errors.append('source_retrieval missing registry SHA')
    required_assets={'ILLUSTRATION-GUIDANCE-V2.0','ILLUSTRATION-LOCK-BASELINE-V2.0','COVER-TITLE-GUIDE-V4','ILLUSTRATION-SIX-SHEET-TEMPLATE-V2.0'}
    loaded=set(sr.get('loaded_asset_ids',[]))
    if not required_assets.issubset(loaded): errors.append('source retrieval did not load all required current illustration assets')
    excluded=set(sr.get('excluded_asset_ids',[]))
    if not {'ILLUSTRATION-GUIDANCE-V1.0','ILLUSTRATION-18-SCRIPTS-V3.0'}.issubset(excluded): errors.append('retired V1.0/V3.0 illustration assets were not explicitly excluded')
    dm=pack.get('domain_asset_manifest',{})
    if dm.get('overlay_version')!='illustration-domain-2.0.0' or dm.get('all_current_assets_sha_verified') is not True: errors.append('illustration V2.0 private asset manifest not verified')
    if dm.get('current_guidance_text_loaded') is not True: errors.append('full current V2.0 guidance text was not loaded into the asset pack')
    if dm.get('legacy_platform_examples_loaded') != 0: errors.append('historical platform examples were not excluded from illustration retrieval')
    bg=decision.get('benchmark_governance',{})
    if bg.get('classification')!='BENCHMARK' or bg.get('score_applied') is not False or bg.get('rewrite_allowed') is not False: errors.append('benchmark governance missing or benchmark marked editable/scorable')
    if bg.get('benchmark_id')!='ILLUSTRATION-BENCHMARK-US-300USD-TOWEL-PRINT': errors.append('benchmark identity is not bound to the current immutable standard case')
    if any(x.get('sample_class')=='BENCHMARK' or 'BENCHMARK' in str(x.get('id','')).upper() for x in decision.get('selected',[])): errors.append('benchmark was included in selected derived scripts')
    scripts=batch.get('scripts',[]); ids=[x.get('id') for x in scripts]
    if any(x.get('sample_class')=='BENCHMARK' or 'BENCHMARK' in str(x.get('id','')).upper() for x in scripts): errors.append('BENCHMARK incorrectly included in the derived-script batch')
    if len(scripts)!=18 or len(set(ids))!=18: errors.append('illustration batch must contain 18 unique derived scripts')
    for p,n in PLATFORMS.items():
        if sum(1 for x in scripts if x.get('platform') in (p, {'抖音':'douyin','微信视频号':'channels','小红书':'xiaohongshu'}[p]))!=n:
            errors.append('platform count mismatch: '+p)
    score_path=run/'illustration-review.json'
    external_done=False; facts={}
    if not score_path.is_file(): errors.append('illustration-review.json missing; per-script scorecard cannot be skipped')
    else:
        score=read(score_path); reviewer=score.get('reviewer',{})
        if reviewer.get('independent') is not True or reviewer.get('mode') not in ('human','separate_model') or not reviewer.get('identity'):
            errors.append('illustration reviewer is not independently identified')
        if reviewer.get('same_model_role') is not False: errors.append('same-model or unverified reviewer cannot count as independent')
        if not reviewer.get('blind_packet_file') or not reviewer.get('review_evidence_file'):
            errors.append('reviewer blind packet and review evidence files are required')
        items=score.get('items',[])
        if score.get('blind_packet_sha256') != reviewer.get('blind_packet_sha256'): errors.append('top-level blind-packet SHA does not match reviewer record')
        if score.get('batch_sha256') != sha(batch_path): errors.append('scorecard is not bound to this exact batch SHA')
        if reviewer.get('blind_packet_sha256') and score.get('blind_packet_sha256') != reviewer.get('blind_packet_sha256'): errors.append('review blind-packet SHA mismatch')
        if len(items)!=18 or {x.get('script_id') for x in items}!=set(ids): errors.append('scorecard must contain one record per derived Script_ID')
        scores_by_script={}
        for item in items:
            sid=item.get('script_id')
            if item.get('sample_class')=='BENCHMARK' or 'BENCHMARK' in str(sid).upper(): errors.append('benchmark was incorrectly scored: '+str(sid)); continue
            dims=item.get('scores',{})
            if set(dims)!=set(WEIGHTS): errors.append(str(sid)+' score dimensions mismatch'); continue
            total=0
            for name,weight in WEIGHTS.items():
                d=dims[name]; value=d.get('score')
                if type(value) is not int or not 0<=value<=5 or not d.get('quote') or not d.get('reason'):
                    errors.append(str(sid)+' invalid score evidence: '+name); continue
                if value < 3: errors.append(str(sid)+' dimension below 3/5: '+name)
                total += value*weight/5
            item['computed_score']=round(total,1)
            scores_by_script[sid]=round(total,1)
            if total<70: errors.append(str(sid)+' below 70 editorial candidate floor; revise')
            if total>80: warnings.append(str(sid)+' above 80; still requires evidence and external validation; score is not market proof')
            gates=item.get('hard_gates',{})
            required=['lock_fields','facts','rights','promise_payoff','platform_fit','professional_value','script_04_05_mapping']
            failed=[k for k in required if gates.get(k) is not True]
            if failed: errors.append(str(sid)+' hard gate failure: '+','.join(failed))
            if failed and item.get('decision') not in ('REVISE','FAIL','PUBLISH_HOLD'): errors.append(str(sid)+' decision contradicts failed hard gates')
            if total<70 and item.get('decision')=='PASS': errors.append(str(sid)+' low score cannot be marked PASS')
            if item.get('decision') not in ('PASS','REVISE','FAIL','VALIDATION_PENDING','PUBLISH_HOLD'):
                errors.append(str(sid)+' missing explicit decision')
        blind=score.get('target_user_blind_read',{})
        readtest=score.get('non_author_read_test',{})
        external_done=(blind.get('status')=='PASS' and blind.get('participants',0)>=3 and readtest.get('status')=='PASS' and readtest.get('reader') and readtest.get('measured_seconds'))
        if not external_done: warnings.append('真人试读/目标用户盲读未完成：最终状态最多为VALIDATION_PENDING')
        facts=score.get('fact_and_rights_audit',{})
        if facts.get('status')!='PASS': warnings.append('事实/授权独立复核未完成：有强主张时必须PUBLISH_HOLD')
    result={'passed':not errors,'scores_by_script':locals().get('scores_by_script',{}),'editorial_status':'PASS' if not errors else 'REVISE','publication_status':'READY' if not errors and score_path.is_file() and external_done and facts.get('status')=='PASS' else 'VALIDATION_PENDING','errors':errors,'warnings':warnings,'weights':WEIGHTS,'batch_sha256':sha(batch_path),'review_sha256':sha(review_path),'scorecard_sha256':sha(score_path) if score_path.is_file() else None}
    Path(run/'illustration-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--run',required=True); p.add_argument('--batch',required=True); p.add_argument('--review',required=True); a=p.parse_args()
    r=validate(a.run,a.batch,a.review); print(json.dumps(r,ensure_ascii=False,indent=2))
    if not r['passed']: raise SystemExit(2)
if __name__=='__main__': main()
