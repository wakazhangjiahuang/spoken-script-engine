#!/usr/bin/env python3
"""Static workbook lint for title/opening/CTA wording. Human semantic review remains mandatory."""
import argparse, json, re, sys
from openpyxl import load_workbook
BAD = ["评论区calling","AI真实现","成片如牛来","牛来","AI剪辑密码","剪辑师天塌了","邪修","老奶奶都会","秒变大神","喝杯咖啡的时间","零门槛"]
FIELDS = ["封面主标题（原文锁定）","封面副标题（原文锁定）","0–3秒｜开场首句","3–8秒｜承接次句","正文（分段直接朗读）","Calling（单一主动作）","评论钩子（与Calling同一目的）"]
def norm(x): return re.sub(r"[^\w\u4e00-\u9fff]+","",str(x or ""))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("workbook")
    a=ap.parse_args()
    wb=load_workbook(a.workbook,data_only=True)
    issues=[]
    for ws in wb.worksheets:
        if not ws.title.startswith(("01_","02_","03_")): continue
        headers=[ws.cell(1,c).value for c in range(1,ws.max_column+1)]
        if not all(f in headers for f in FIELDS): continue
        ix={h:i+1 for i,h in enumerate(headers)}
        for r in range(2,ws.max_row+1):
            sid=ws.cell(r,1).value
            vals={f:ws.cell(r,ix[f]).value for f in FIELDS}
            joined=" ".join(norm(v) for v in vals.values())
            for bad in BAD:
                if bad in joined:
                    issues.append({"sheet":ws.title,"id":sid,"type":"phrase_review","phrase":bad})
            title=norm(vals[FIELDS[0]])
            opening=norm(vals[FIELDS[2]])
            suspense=norm(vals[FIELDS[3]])
            if title and opening and (title in opening or opening in title):
                issues.append({"sheet":ws.title,"id":sid,"type":"cover_opening_echo"})
            if suspense and opening and suspense==opening:
                issues.append({"sheet":ws.title,"id":sid,"type":"opening_suspense_duplicate"})
            if "评论区" in norm(vals[FIELDS[5]]) and "评论区" in norm(vals[FIELDS[6]]):
                issues.append({"sheet":ws.title,"id":sid,"type":"cta_comment_mechanical_overlap"})
    print(json.dumps({"ok":not issues,"issues":issues,"note":"Static lint only; semantic promise-chain review is still required."},ensure_ascii=False,indent=2))
    return 1 if issues else 0
if __name__=="__main__": sys.exit(main())
