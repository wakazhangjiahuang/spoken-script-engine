"""Rebuild inventory after authorized KB edits; not a trust bypass in production."""
import json,hashlib
from pathlib import Path
K=Path(__file__).resolve().parents[1]/'assets/kb-snapshot'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 entries=[]
 for p in sorted(K.rglob('*')):
  if not p.is_file() or p.name in ('KB-MANIFEST.json','asset-index.jsonl') or '__pycache__' in p.parts:continue
  rel=p.relative_to(K).as_posix();entries.append({'id':rel,'path':rel,'sha256':h(p),'platform':next((x for x in ('xiaohongshu','douyin','channels') if x in p.parts),'shared')})
 (K/'asset-index.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in entries))
 entries.append({'id':'asset-index.jsonl','path':'asset-index.jsonl','sha256':h(K/'asset-index.jsonl'),'platform':'shared'})
 old=json.loads((K/'KB-MANIFEST.json').read_text());old.update(version='2.1.0',release_status='versioned_release_candidate',checked_at='2026-11-17',assets=entries);old['source']['approved_guidance']='sources/approved/provenance.json';old['source']['overlay_version']='2.1.0'
 (K/'KB-MANIFEST.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
 print('manifest files:',len(entries))
if __name__=='__main__':main()
