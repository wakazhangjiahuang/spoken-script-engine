#!/usr/bin/env python3
"""v3.4.2 AI-video source loader: make V4.1 business guidance an actual must-read asset."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import ai_video_assets_v2 as base
from content_decision_gate_v342 import extract_text
from v41_routing import is_ai_video_brief

ROOT = base.ROOT
_ORIGINAL_STAGE_DOMAIN_ASSETS = base.stage_domain_assets

def stage_domain_assets(run_dir, brief):
    result = _ORIGINAL_STAGE_DOMAIN_ASSETS(run_dir, brief)
    if not result or not is_ai_video_brief(brief):
        return result
    run_dir = Path(run_dir)
    manifest_path = Path(result['manifest_path'])
    dm = json.loads(manifest_path.read_text(encoding='utf-8'))
    source_manifest = json.loads((ROOT / 'assets/ai-video/manifest.json').read_text(encoding='utf-8'))
    ids_by_path = {x.get('path'): x.get('asset_id') for x in source_manifest.get('current_assets', [])}
    roles_by_id = {x.get('asset_id'): x.get('role') for x in source_manifest.get('current_assets', [])}
    required_ids = {'AI-VIDEO-BUSINESS-GUIDE-V4.1', 'AI-VIDEO-TEAM-GUIDE-20261123', 'AI-VIDEO-SAMPLE-20261123'}
    loaded = []
    for item in dm.get('assets', []):
        aid = ids_by_path.get(item.get('source_path'))
        if aid:
            item['source_asset_id'] = aid
            item['source_role'] = roles_by_id.get(aid)
            if aid in required_ids:
                loaded.append(item)
        if item.get('source_path', '').endswith('AI视频赛道商业化与内容营销指导书_V4.1.docx'):
            item['role'] = 'must_read_business_content_standard'
        elif item.get('source_path', '').endswith('AI视频制作标准指导手册_团队执行版_20261123.docx'):
            item['role'] = 'must_read_current_production_standard'
        elif item.get('source_path', '').endswith('AI视频_三平台口播稿_样例_20261123.xlsx'):
            item['role'] = 'structure_reference_only_not_positive_few_shot'
        elif 'v1.0.docx' in item.get('source_path', '') or '最终校正版.xlsx' in item.get('source_path', ''):
            item['role'] = 'historical_only_do_not_use_as_current_standard'
    by_id = {x.get('source_asset_id'): x for x in dm.get('assets', [])}
    business = by_id.get('AI-VIDEO-BUSINESS-GUIDE-V4.1')
    team = by_id.get('AI-VIDEO-TEAM-GUIDE-20261123')
    sample = by_id.get('AI-VIDEO-SAMPLE-20261123')
    if not business or not team or not sample:
        raise ValueError('v3.4.2 current AI-video guide/team guide/workbook staging incomplete')
    must = list(dm.get('must_read_before_script_generation', []))
    for item in (business, team):
        if item['run_path'] not in must:
            must.append(item['run_path'])
    if sample['run_path'] not in must:
        must.append(sample['run_path'])
    dm['must_read_before_script_generation'] = must
    dm['must_read_source_asset_ids'] = ['AI-VIDEO-BUSINESS-GUIDE-V4.1','AI-VIDEO-TEAM-GUIDE-20261123','AI-VIDEO-SAMPLE-20261123']
    dm['sample_workbook_policy'] = 'STRUCTURE_REFERENCE_ONLY_NOT_POSITIVE_COPYWRITING_FEW_SHOT'
    dm['legacy_assets_policy'] = 'v1.0 production guide and old workbook are historical-only; current 2026-11-23 team guide/workbook override them.'
    manifest_path.write_text(json.dumps(dm, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Materialize the two authoritative Word guides into asset-pack.json so the generation
    # stage receives the actual source text, not only a filename and SHA.
    pack_path = run_dir / 'asset-pack.json'
    if pack_path.is_file():
        pack = json.loads(pack_path.read_text(encoding='utf-8'))
        mg = pack.setdefault('must_read_guidance', {})
        for item in (business, team):
            path = (run_dir / item['run_path']).resolve()
            if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
                raise ValueError('staged current AI-video source missing: ' + item['run_path'])
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != item.get('sha256'):
                raise ValueError('staged current AI-video source SHA mismatch: ' + item['source_asset_id'])
            text = extract_text(path)
            if len(text) < 200:
                raise ValueError('current AI-video guide extraction incomplete: ' + item['source_asset_id'])
            mg[item['source_path']] = {'source_asset_id': item['source_asset_id'], 'source_path': item['source_path'],
                'sha256': actual, 'text': text, 'role': item.get('role'), 'authority': 'CURRENT_PRIVATE_SOURCE'}
        pack['domain_asset_manifest'] = {'source_manifest_path': 'domain-asset-manifest.json',
            'must_read_source_asset_ids': dm['must_read_source_asset_ids'], 'current_guidance_text_loaded': True,
            'sample_workbook_policy': dm['sample_workbook_policy']}
        pack['domain_workbook_reference'] = {'source_asset_id': 'AI-VIDEO-SAMPLE-20261123',
            'role': 'STRUCTURE_REFERENCE_ONLY_NOT_POSITIVE_FEW_SHOT', 'sheet_names': ['00_使用总览','01_抖音','02_视频号','03_小红书','04_拍摄执行卡','05_AI数字人口播执行卡'],
            'content_copying_allowed': False}
        pack_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    return result
