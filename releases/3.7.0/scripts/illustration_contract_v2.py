#!/usr/bin/env python3
"""Illustration V2.0 intake/plan/draft/review gates."""
from __future__ import annotations
import re
from composition_contract import nonblank, anchor_error
from illustration_assets_v2 import active

REQUIRED_CONTRACT = ('audience_voice','viewer_task','current_belief','desired_outcome','core_tension','entry_competition','selected_angle_id','click_reason','promise_and_payoff','proof_plan','illustration_judgement','transferable_value','next_value','forbidden_claims')
INFO_CLASSES={'user_project','official_product','market_research','original_development','explicit_technical_tutorial','behind_scenes'}
SOURCE_CLASSES={'user_project','official_product','research','original_work','historical_example','hypothetical'}

def intake_errors(brief):
    if not active(brief): return []
    errors=[]; c=brief.get('audience_information',{})
    if not isinstance(c,dict) or any(not nonblank(c.get(k)) for k in ('primary_role','current_problem','direct_benefit','information_type','source_class')):
        return ['illustration V2.0: audience_information missing primary_role/current_problem/direct_benefit/information_type/source_class']
    if c.get('information_type') not in INFO_CLASSES: errors.append('illustration V2.0: invalid information_type')
    if c.get('source_class') not in SOURCE_CLASSES: errors.append('illustration V2.0: invalid source_class')
    if c.get('information_type')=='explicit_technical_tutorial':
        if brief.get('explicit_technical_tutorial') is not True: errors.append('illustration: technical tutorial must be explicitly requested')
        if not any(x.get('status')=='available' and x.get('evidence_role')=='demonstration' for x in brief.get('production_resources',[])):
            errors.append('illustration: technical tutorial needs visible demonstration resource')
    if c.get('source_class')=='user_project' and not any(f.get('evidence_class')=='user_project' for f in brief.get('facts',[])):
        errors.append('illustration: user project must be grounded in current user-provided facts')
    return errors

def plan_errors(plan,brief,pack):
    if not pack.get('domain_profile') or not active(brief): return []
    errors=intake_errors(brief)
    selected=plan.get('selected',[])
    if not selected: return errors+['illustration V2.0: plan has no selected scripts']
    for p in selected:
        sid=p.get('id','UNKNOWN'); c=p.get('information_contract') or p.get('expression_contract',{})
        missing=[k for k in REQUIRED_CONTRACT if k not in c or (k!='entry_competition' and k!='forbidden_claims' and not nonblank(c.get(k)))]
        if missing:
            errors.append(sid+' expression contract missing: '+','.join(missing)); continue
        entries=c.get('entry_competition')
        if not isinstance(entries,list) or len(entries)<3:
            errors.append(sid+' must compare at least three distinct content entries')
        else:
            ids=[x.get('entry_id') for x in entries if isinstance(x,dict)]
            mechanisms=[x.get('mechanism') for x in entries if isinstance(x,dict)]
            if len(ids)<3 or len(set(ids))<3: errors.append(sid+' entry competition must contain three distinct candidates')
            if len(mechanisms)<3 or any(not nonblank(x) for x in mechanisms) or len(set(mechanisms))<3: errors.append(sid+' entry competition must use three materially different mechanisms, not title rewrites')
            if any(not nonblank(x.get('audience_benefit')) or not nonblank(x.get('evidence_fit')) or not nonblank(x.get('risk')) for x in entries if isinstance(x,dict)):
                errors.append(sid+' entry competition missing audience benefit/evidence fit/risk')
            if c.get('selected_angle_id') not in ids: errors.append(sid+' selected_angle_id must match one compared entry')
        if not isinstance(c.get('forbidden_claims'),list): errors.append(sid+' forbidden_claims must be a list')
        if p.get('sample_class')=='BENCHMARK' or p.get('asset_id','').startswith('ILLUSTRATION-BENCHMARK'):
            errors.append(sid+' benchmark must not be selected as a derived script/few-shot')
        audience=brief.get('audience_information',{})
        if c.get('audience_voice') and audience.get('primary_role') and audience.get('primary_role') not in str(c['audience_voice']):
            # Audience_Voice is free text; avoid brittle equality. This check is intentionally omitted if no exact structured role exists.
            pass
    return errors

def draft_errors(script,plan,pack,brief):
    if not pack.get('domain_profile') or not active(brief): return []
    errors=[]; sid=script.get('id','UNKNOWN'); segs=script.get('segments',[])
    roles=[x.get('role') for x in segs]
    for role in ('hook','suspense','context','judgment','value','calling'):
        if role not in roles: errors.append(sid+' missing segment role '+role)
    # Immutable source fields are checked against the lock manifest when the script belongs to the baseline batch.
    lm=pack.get('lock_manifest',{}); lock=next((x for x in lm.get('scripts',[]) if x.get('script_id')==sid),None)
    if lock:
        if len(segs) != 6:
            errors.append(sid+' historical illustration workbook requires six script segments')
        values=lock['fields']
        expected_platform=lock.get('platform')
        platform=script.get('platform')
        aliases={'douyin':'抖音','channels':'微信视频号','视频号':'微信视频号','xiaohongshu':'小红书'}
        if aliases.get(platform,platform)!=expected_platform: errors.append(sid+' platform does not match original lock baseline')
        actual={'封面主标题':script.get('cover_main'),'封面副标题':script.get('cover_sub'),'0–3秒｜黄金三秒（原文锁定）':segs[0].get('text') if segs else None,'3–8秒（原文锁定）':segs[1].get('text') if len(segs)>1 else None}
        for k,v in values.items():
            if actual.get(k)!=v: errors.append(sid+' immutable field changed: '+k)
    d=script.get('information_delivery',{})
    if not isinstance(d,dict): return errors+[sid+' information_delivery missing']
    for key,allowed in [('opening_benefit',{segs[0]['id']} if segs else set()),('new_fact',{segs[1]['id']} if len(segs)>1 else set()),('viewer_use',{x['id'] for x in segs if x.get('role') in ('judgment','value')})]:
        e=anchor_error(d.get(key),script,allowed)
        if e: errors.append(sid+' information '+key+' '+e)
    opening=d.get('opening_fact_ids',[]); fresh=d.get('new_fact_ids',[])
    if not isinstance(fresh,list) or not fresh or set(fresh).issubset(set(opening or [])):
        errors.append(sid+' second block must add a new fact or explicit new information')
    if d.get('surface','speech')!='speech': errors.append(sid+' viewer value must be spoken, not hidden in notes/visuals')
    return errors

def review_errors(review,scripts,pack):
    if not pack.get('domain_profile'): return []
    rows=review.get('information_checks',[]); errors=[]
    if not isinstance(rows,list) or len(rows)!=len(scripts) or {r.get('script_id') for r in rows if isinstance(r,dict)}!={s['id'] for s in scripts}:
        return ['independent illustration information-value review missing']
    for s in scripts:
        r=next(x for x in rows if x.get('script_id')==s['id'])
        for k in ('opening_value','new_fact','story_decision','viewer_use','calling_input'):
            a=r.get(k,{})
            if not isinstance(a,dict) or a.get('passed') is not True or not nonblank(a.get('reason')):
                errors.append(s['id']+' information review failed '+k); continue
            roles={'opening_value':{'hook'},'new_fact':{'suspense'},'story_decision':{'context','judgment','value'},'viewer_use':{'judgment','value'},'calling_input':{'calling'}}
            allowed={g['id'] for g in s['segments'] if g.get('role') in roles[k]}
            e=anchor_error(a,s,allowed)
            if e: errors.append(s['id']+' information review '+k+' '+e)
            if a.get('surface','speech')!='speech': errors.append(s['id']+' information review must quote spoken content '+k)
    return errors
