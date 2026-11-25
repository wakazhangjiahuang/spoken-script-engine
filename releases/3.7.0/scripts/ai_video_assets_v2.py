#!/usr/bin/env python3
"""Adds the current 2026-11-23 AI-video production guide and workbook to the existing isolated V4.1 overlay."""
from __future__ import annotations
import json, shutil, hashlib
from openpyxl import load_workbook
from pathlib import Path
import ai_video_assets as legacy
from v41_routing import is_ai_video_brief
ROOT=legacy.ROOT
# The routing layer replaces legacy.stage_domain_assets later. Capture the
# original callable now so delegation cannot recurse into its own wrapper.
_LEGACY_STAGE_DOMAIN_ASSETS=legacy.stage_domain_assets
CURRENT_FILES=[
 'assets/ai-video/current/AI视频制作标准指导手册_团队执行版_20261123.docx',
 'assets/ai-video/current/AI视频_三平台口播稿_样例_20261123.xlsx'
]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify_current_assets():
    manifest_path=ROOT/'assets/ai-video/manifest.json'
    m=json.loads(manifest_path.read_text(encoding='utf-8'))
    for rel in CURRENT_FILES:
        item=next((x for x in m.get('current_assets',[]) if x.get('path')==rel),None)
        src=ROOT/rel
        if not item or not src.is_file() or sha(src)!=item.get('sha256'):
            raise ValueError('current AI-video private asset manifest/hash mismatch: '+rel)
    sample=ROOT/CURRENT_FILES[1]
    wb=load_workbook(sample,data_only=True,read_only=True)
    expected=['00_使用总览','01_抖音','02_视频号','03_小红书','04_拍摄执行卡','05_AI数字人口播执行卡']
    if wb.sheetnames!=expected: raise ValueError('AI-video sample workbook sheet structure mismatch')
    scripts=sum(sum(1 for r in range(2,wb[s].max_row+1) if wb[s].cell(r,1).value) for s in expected[1:4])
    if scripts!=9 or wb['04_拍摄执行卡'].max_row-1!=72 or wb['05_AI数字人口播执行卡'].max_row-4!=101 or wb['05_AI数字人口播执行卡'].max_column!=37:
        raise ValueError('AI-video sample workbook structural baseline changed; re-audit before routing')
    wb.close()
    return m

def stage_domain_assets(run_dir,brief):
    result=_LEGACY_STAGE_DOMAIN_ASSETS(run_dir,brief)
    if not is_ai_video_brief(brief) or not result: return result
    current_manifest=verify_current_assets()
    run_dir=Path(run_dir); manifest_path=Path(result['manifest_path'])
    m=json.loads(manifest_path.read_text(encoding='utf-8'))
    for rel in CURRENT_FILES:
        src=ROOT/rel
        if not src.is_file(): raise ValueError('current AI-video asset missing: '+rel)
        dest_rel=Path('domain-assets')/'ai-video'/rel
        dest=run_dir/dest_rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
        m.setdefault('assets',[]).append({'source_path':rel,'run_path':dest_rel.as_posix(),'sha256':sha(dest),'role':'must_read_production_standard' if rel.endswith('.docx') else 'must_read_structure_reference'})
        result['staged_paths'].append(dest_rel.as_posix())
        m.setdefault('must_read_before_script_generation',[]).append(dest_rel.as_posix())
    m['current_production_guide']='domain-assets/ai-video/assets/ai-video/current/AI视频制作标准指导手册_团队执行版_20261123.docx'
    m['current_workbook_sample']='domain-assets/ai-video/assets/ai-video/current/AI视频_三平台口播稿_样例_20261123.xlsx'
    m['production_guide_scope']='team production and 04/05 execution; V4.1 remains content strategy standard'
    manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result['manifest_sha256']=sha(manifest_path)
    return result
record_sample_retrieval=legacy.record_sample_retrieval
