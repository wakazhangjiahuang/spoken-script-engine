#!/usr/bin/env python3
"""Validate the v1.3 repository's runtime assets. Uses Python standard library only."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import sys

def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'KB-MANIFEST.json').read_text(encoding='utf-8'))
    paths = set()
    assets = {}
    for item in manifest['assets']:
        rel = item['path']
        pure = PurePosixPath(rel)
        if pure.is_absolute() or '..' in pure.parts or '\\' in rel or rel in paths:
            raise ValueError('Unsafe or duplicate manifest path: ' + rel)
        file = (root / rel).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise ValueError('Missing or unsafe asset: ' + rel)
        if not re.fullmatch(r'[0-9a-f]{64}', item['sha256']):
            raise ValueError('Invalid SHA256: ' + rel)
        if hashlib.sha256(file.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('SHA256 mismatch: ' + rel)
        paths.add(rel)
        assets[rel] = item
    entries = [json.loads(line) for line in (root / 'asset-index.jsonl').read_text(encoding='utf-8').splitlines() if line]
    indexed = {}
    for item in entries:
        rel = item['path']
        if rel in indexed or assets.get(rel) != item:
            raise ValueError('Index entry mismatch: ' + rel)
        indexed[rel] = item
    if set(indexed) != paths - {'asset-index.jsonl'}:
        raise ValueError('Index coverage mismatch')
    registry = json.loads((root / 'REPO-REGISTRY.json').read_text(encoding='utf-8'))
    if registry['resources']['spoken']['repository'] != manifest['repository']:
        raise ValueError('Repository name mismatch')
    parsed = 0
    for file in sorted(root.rglob('*')):
        if file.suffix == '.json':
            json.loads(file.read_text(encoding='utf-8'))
        elif file.suffix == '.jsonl':
            for line_no, line in enumerate(file.read_text(encoding='utf-8').splitlines(), 1):
                if line:
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(str(file.relative_to(root)) + ':' + str(line_no)) from exc
                    parsed += 1
    print(json.dumps({'status': 'passed', 'version': manifest['version'], 'hashed_assets': len(paths), 'indexed_assets': len(indexed), 'parsed_jsonl_records': parsed, 'repository': manifest['repository'], 'quality_or_github_sync_certified': False}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
