#!/usr/bin/env python3
"""Prepare only actual first-screen surfaces, before the full script is written."""
import argparse,json
from pathlib import Path
from surface_contract import first8_packet,canonical
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--brief',required=True);p.add_argument('--candidates',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 brief=json.loads(Path(a.brief).read_text());data=json.loads(Path(a.candidates).read_text());packet=first8_packet(data['opening_candidates'],brief)
 out={'panel':packet,'panel_sha256':canonical(packet),'instructions':'先独立复述从实际首屏听到的机会和继续看的理由；不要替作者从备稿补利益。RECOMMEND_FOR_DRAFT只表示可进入写作，不证明点击效果。'}
 Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'output':a.output,'panel_sha256':out['panel_sha256']}))
