#!/usr/bin/env python3
"""v3.4.2 illustration source loader: read current V2.0 guidance; exclude stale examples."""
from __future__ import annotations
import hashlib
from pathlib import Path
import illustration_assets_v2 as base
from content_decision_gate_v342 import extract_text

ROOT = base.ROOT
_ORIGINAL_PACK_ILLUSTRATION = base.pack_illustration

def pack_illustration(base_pack: dict, brief: dict) -> dict:
    if not base.active(brief):
        return base_pack
    pack = _ORIGINAL_PACK_ILLUSTRATION(base_pack, brief)
    # The 2026-11-18 snapshot and generic platform current-examples are historical,
    # not current illustration positive samples. Keep generic methods, drop stale examples.
    kept = []
    for item in pack.get('assets', []):
        path = str(item.get('source_path') or item.get('path') or '')
        if ('20261118' in path or path.endswith('/current-examples.jsonl') or
            path.startswith('domains/illustration/') or 'samples/illustration' in path or
            'current-title-map' in path or 'current-cover-lines' in path):
            continue
        kept.append(item)
    pack['assets'] = kept
    manifest = base.load_manifest()
    required = ('ILLUSTRATION-GUIDANCE-V2.0', 'COVER-TITLE-GUIDE-V4')
    loaded = []
    for aid in required:
        asset = next((x for x in manifest['current_assets'] if x['asset_id'] == aid), None)
        if not asset:
            raise ValueError('required current illustration source missing: ' + aid)
        path = (ROOT / asset['path']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError('required illustration source path missing: ' + aid)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != asset.get('sha256'):
            raise ValueError('current illustration source SHA mismatch: ' + aid)
        text = extract_text(path)
        if len(text) < 200:
            raise ValueError('current illustration source text extraction incomplete: ' + aid)
        pack.setdefault('must_read_guidance', {})[asset['path']] = {
            'source_asset_id': aid, 'source_path': asset['path'], 'sha256': digest,
            'text': text, 'role': asset.get('role'), 'authority': 'CURRENT_PRIVATE_SOURCE'
        }
        loaded.append({'asset_id': aid, 'source_path': asset['path'], 'sha256': digest, 'role': asset.get('role')})
    dm = pack.setdefault('domain_asset_manifest', {})
    dm['source_assets'] = loaded
    dm['required_source_asset_ids'] = list(required)
    dm['current_guidance_text_loaded'] = True
    dm['legacy_platform_examples_loaded'] = 0
    dm['legacy_snapshot_status'] = 'HISTORICAL_ONLY_NOT_USED_AS_ILLUSTRATION_POSITIVE_EXAMPLES'
    pack['retrieval_policy'] = 'ILLUSTRATION_V2.0_GUIDANCE_AND_TITLE_V4_ARE_AUTHORITATIVE; old 20261118 platform examples are excluded; V4.0 workbook remains structural-only; immutable 72-cell lock baseline remains read-only.'
    pack['source_need_policy'] = {'required_source_asset_id': 'ILLUSTRATION-GUIDANCE-V2.0', 'quote_must_be_verbatim': True, 'locator_must_exist_in_source': True}
    return pack
