#!/usr/bin/env python3
"""Public, source-agnostic validator for the illustration V2.0 six-sheet workbook."""
import argparse,json,re,hashlib
from pathlib import Path
from openpyxl import load_workbook
EXPECTED=['00_使用总览','01_抖音','02_视频号','03_小红书','04_拍摄执行卡','05_AI数字人口播执行卡']
PLATFORMS={'01_抖音':('02_抖音6稿',6),'02_视频号':('03_视频号6稿',6),'03_小红书':('01_小红书6稿',6)}
LOCK={'封面主标题':'封面主标题（原文锁定）','封面副标题':'封面副标题（原文锁定）','0–3秒｜黄金三秒（原文锁定）':'0–3秒｜黄金三秒（原文锁定）','3–8秒（原文锁定）':'3–8秒（原文锁定）'}
def norm(x): return re.sub(r'\s+','',str(x or ''))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def validate(workbook,baseline):
    errors=[]; out=load_workbook(workbook,data_only=True); src=load_workbook(baseline,data_only=True,read_only=True)
    if out.sheetnames!=EXPECTED: errors.append('six-sheet order/name mismatch')
    ids=[]
    for on,(sn,count) in PLATFORMS.items():
        if on not in out.sheetnames or sn not in src.sheetnames: errors.append('missing platform sheet '+on); continue
        ow=out[on]; sw=src[sn]
        oh={ow.cell(1,c).value:c for c in range(1,ow.max_column+1)}; sh={sw.cell(1,c).value:c for c in range(1,sw.max_column+1)}
        rows=[r for r in range(2,ow.max_row+1) if ow.cell(r,oh.get('脚本ID',1)).value]
        if len(rows)!=count: errors.append(on+' script count mismatch')
        baseline_rows={str(sw.cell(r,sh['ID']).value):r for r in range(2,sw.max_row+1) if sw.cell(r,sh['ID']).value}
        for r in rows:
            sid=str(ow.cell(r,oh['脚本ID']).value); ids.append(sid); br=baseline_rows.get(sid)
            if br is None: errors.append(sid+' missing from lock baseline'); continue
            for sf,of in LOCK.items():
                if sw.cell(br,sh[sf]).value!=ow.cell(r,oh[of]).value: errors.append(sid+' locked field changed: '+sf)
            pieces=[ow.cell(r,oh['0–3秒｜黄金三秒（原文锁定）']).value,ow.cell(r,oh['3–8秒（原文锁定）']).value,ow.cell(r,oh['正文（分段直接朗读）']).value,ow.cell(r,oh['Calling（单一主动作）']).value]
            if norm('\n'.join(str(x or '') for x in pieces))!=norm(ow.cell(r,oh['完整可朗读稿（同源拼接）']).value): errors.append(sid+' full speech reconstruction mismatch')
    if len(ids)!=18 or len(set(ids))!=18: errors.append('expected 18 unique derived scripts')
    ws=out['04_拍摄执行卡']; h={ws.cell(1,c).value:c for c in range(1,ws.max_column+1)}
    rows=[r for r in range(2,ws.max_row+1) if ws.cell(r,h['执行段ID']).value]
    if len(rows)!=108: errors.append('04 must contain 108 segments')
    seg={}
    for r in rows:
        eid=str(ws.cell(r,h['执行段ID']).value); seg[eid]=str(ws.cell(r,h['对应台词（逐字同全文）']).value or '')
    if any(sum(1 for k in seg if k.startswith(sid+'-S'))!=6 for sid in ids): errors.append('04 must map six segments per script')
    ws=out['05_AI数字人口播执行卡']; h={ws.cell(4,c).value:c for c in range(1,ws.max_column+1)}
    rows=[r for r in range(5,ws.max_row+1) if ws.cell(r,h['H3镜头ID']).value]
    if not rows: errors.append('05 has no H3 shots')
    mapped={k:[] for k in seg}
    for r in rows:
        hid=str(ws.cell(r,h['H3镜头ID']).value); eid=str(ws.cell(r,h['对应04执行卡ID']).value)
        dur=ws.cell(r,h['H3单次生成时长(s)']).value; line=str(ws.cell(r,h['本镜台词（逐字）']).value or '')
        prompt=str(ws.cell(r,h['H3单镜头Prompt（可复制）']).value or '')
        if not isinstance(dur,(int,float)) or not 4<=dur<=15: errors.append(hid+' duration outside 4–15s')
        if eid not in mapped: errors.append(hid+' unknown 04 segment')
        else: mapped[eid].append(line)
        if not line or norm(line) not in norm(prompt): errors.append(hid+' prompt does not preserve exact line')
    for eid,line in seg.items():
        if norm(''.join(mapped.get(eid,[])))!=norm(line): errors.append(eid+' 04/05 speech mapping mismatch')
    result={'passed':not errors,'errors':errors,'script_count':len(ids),'lock_cells_checked':72,'shooting_segments':len(rows),'workbook_sha256':sha(workbook),'baseline_sha256':sha(baseline)}
    out.close(); src.close(); return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--workbook',required=True);p.add_argument('--baseline',required=True);p.add_argument('--report');a=p.parse_args()
    r=validate(a.workbook,a.baseline); print(json.dumps(r,ensure_ascii=False,indent=2))
    if a.report: Path(a.report).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not r['passed']: raise SystemExit(2)
if __name__=='__main__': main()
