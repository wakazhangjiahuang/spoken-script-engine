#!/usr/bin/env python3
"""v3.4.2 authoritative entrypoint: source loading -> plan binding -> draft gate -> review -> export."""
from __future__ import annotations
import argparse, json, sys, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from asset_path_bootstrap import ensure_asset_aliases
from content_decision_gate_v342 import (build_source_registry, validate_plan, validate_batch,
    validate_ai_video_review, validate_illustration_review, verify_external_evidence)


def _args():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('stage', choices=['intake','plan','draft','validate','export'])
    p.add_argument('--run', required=True)
    p.add_argument('--input')
    p.add_argument('--request')
    p.add_argument('--review')
    p.add_argument('--v41-review')
    p.add_argument('--output')
    p.add_argument('--require-v41-full-validation', action='store_true')
    return p.parse_known_args()[0]


def _read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _domain(brief):
    d = str(brief.get('domain', '')).strip().lower().replace('-', '_')
    if d in {'ai_video','ai_video_business','aivideo','ai视频','ai视频业务'} or brief.get('quality_profile') == 'ai_video_v4_1':
        return 'ai_video'
    if d in {'illustration','print_design','illustration_surface_pattern_textile_print'}:
        return 'illustration'
    return d or 'general'


def _patch_asset_routes():
    # Patch before run_pipeline_v3 imports the route functions by value.
    import illustration_assets_v2
    import ai_video_assets_v2
    _original_active = illustration_assets_v2.active
    def _active_v342(brief):
        domain = str(brief.get('domain','')).lower().replace('-', '_')
        topic = str(brief.get('topic',''))
        return _original_active(brief) or (domain == 'design_service' and any(x in topic for x in ('插画','印花')))
    illustration_assets_v2.active = _active_v342
    from illustration_assets_v2_v342 import pack_illustration
    from ai_video_assets_v2_v342 import stage_domain_assets
    illustration_assets_v2.pack_illustration = pack_illustration
    ai_video_assets_v2.stage_domain_assets = stage_domain_assets


def _context(run, brief):
    pack_path = run / 'asset-pack.json'
    pack = _read(pack_path) if pack_path.is_file() else {}
    registry = build_source_registry(ROOT, run, brief, pack)
    return pack, registry


def _guidance_errors(run, brief, pack):
    domain = _domain(brief)
    guidance = pack.get('must_read_guidance', {}) if isinstance(pack, dict) else {}
    errors = []
    if domain == 'illustration':
        required = {'ILLUSTRATION-GUIDANCE-V2.0','COVER-TITLE-GUIDE-V4'}
        loaded = {v.get('source_asset_id') for v in guidance.values() if isinstance(v, dict) and v.get('text')}
        if not required.issubset(loaded):
            errors.append('ILLUSTRATION_CURRENT_GUIDANCE_OR_TITLE_V4_NOT_LOADED')
        dm = pack.get('domain_asset_manifest', {})
        if dm.get('legacy_platform_examples_loaded') != 0:
            errors.append('ILLUSTRATION_LEGACY_PLATFORM_EXAMPLES_NOT_EXCLUDED')
    elif domain == 'ai_video':
        required = {'AI-VIDEO-BUSINESS-GUIDE-V4.1','AI-VIDEO-TEAM-GUIDE-20261123'}
        loaded = {v.get('source_asset_id') for v in guidance.values() if isinstance(v, dict) and v.get('text')}
        if not required.issubset(loaded):
            errors.append('AI_VIDEO_V4_1_BUSINESS_GUIDE_OR_CURRENT_TEAM_GUIDE_NOT_LOADED')
        dm_path = run / 'domain-asset-manifest.json'
        if not dm_path.is_file():
            errors.append('AI_VIDEO_DOMAIN_ASSET_MANIFEST_MISSING')
        else:
            dm = _read(dm_path)
            ids = set(dm.get('must_read_source_asset_ids', []))
            if not required.issubset(ids):
                errors.append('AI_VIDEO_CURRENT_GUIDANCE_NOT_IN_MUST_READ_ROUTE')
    return errors


def _preflight(a):
    run = Path(a.run).resolve()
    brief_path = run / 'brief.json'
    brief = _read(brief_path) if brief_path.is_file() else {}
    if not brief and a.request and Path(a.request).is_file():
        req = _read(a.request)
        brief = req.get('brief', req) if isinstance(req, dict) else {}
    domain = _domain(brief)
    ensure_asset_aliases(ROOT, run, domain=domain)
    if a.stage == 'intake':
        return
    pack, registry = _context(run, brief)
    guidance_errors = _guidance_errors(run, brief, pack)
    if guidance_errors:
        raise SystemExit('v3.4.2 source-loading preflight blocked:\n- ' + '\n- '.join(guidance_errors))
    decision_path = run / 'decision.json'
    decision = _read(decision_path) if decision_path.is_file() else {}
    if a.stage == 'plan':
        if not a.input:
            raise ValueError('plan requires --input decision JSON')
        errors = validate_plan(_read(a.input), brief, registry)
        if errors:
            raise SystemExit('v3.4.2 plan source-binding blocked:\n- ' + '\n- '.join(errors))
        return
    if a.stage == 'draft':
        errors = validate_plan(decision, brief, registry)
        if errors:
            raise SystemExit('v3.4.2 sealed plan source-binding blocked:\n- ' + '\n- '.join(errors))
        return
    if a.stage not in ('validate','export'):
        return
    if not a.input:
        raise ValueError('validate/export requires --input batch JSON')
    batch = _read(a.input)
    source_manifest = _read(run / 'source-manifest.json') if (run / 'source-manifest.json').is_file() else {}
    errors = validate_batch(batch, brief, pack, decision, registry, source_manifest)
    if domain == 'ai_video':
        if not a.v41_review:
            errors.append('AI_VIDEO_V4_1_REVIEW_REQUIRED')
        else:
            v41 = _read(a.v41_review)
            errors.extend(validate_ai_video_review(batch, v41))
            errors.extend(verify_external_evidence(v41, run))
    elif domain == 'illustration':
        score_path = run / 'illustration-review.json'
        if not score_path.is_file():
            errors.append('ILLUSTRATION_SCORECARD_MISSING')
        else:
            review = _read(score_path)
            errors.extend(validate_illustration_review(batch, review, Path(a.input)))
            errors.extend(verify_external_evidence(review, run))
    if errors:
        raise SystemExit('v3.4.2 content-quality preflight blocked:\n- ' + '\n- '.join(errors))


def _postflight(a):
    run = Path(a.run).resolve()
    if a.stage == 'intake':
        brief = _read(run / 'brief.json')
        pack = _read(run / 'asset-pack.json')
        errors = _guidance_errors(run, brief, pack)
        if errors:
            raise SystemExit('v3.4.2 intake did not load current guidance:\n- ' + '\n- '.join(errors))
    elif a.stage == 'plan':
        brief = _read(run / 'brief.json'); pack, registry = _context(run, brief)
        errors = validate_plan(_read(run / 'decision.json'), brief, registry)
        if errors:
            raise SystemExit('v3.4.2 sealed plan failed source binding:\n- ' + '\n- '.join(errors))
    elif a.stage == 'draft':
        brief = _read(run / 'brief.json'); pack, registry = _context(run, brief)
        batches = sorted(run.glob('batch-v*.json'), key=lambda p: int(__import__('re').search(r'v(\d+)', p.stem).group(1)) if __import__('re').search(r'v(\d+)', p.stem) else -1)
        if not batches:
            raise ValueError('draft stage did not create a versioned batch')
        decision = _read(run / 'decision.json')
        source_manifest = _read(run / 'source-manifest.json') if (run / 'source-manifest.json').is_file() else {}
        errors = validate_batch(_read(batches[-1]), brief, pack, decision, registry, source_manifest)
        if errors:
            raise SystemExit('v3.4.2 draft failed source/decision gate; revise before review:\n- ' + '\n- '.join(errors))


def main():
    a = _args()
    _patch_asset_routes()
    _preflight(a)
    import run_pipeline_v3
    run_pipeline_v3.main()
    _postflight(a)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
