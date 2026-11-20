#!/usr/bin/env python3
"""Validate 04/05 video execution workbook structure and cross-sheet references."""
import argparse, json, re, sys
from openpyxl import load_workbook
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("workbook"); ap.add_argument("--mode",choices=["recording","h3","combined"],default="combined"); a=ap.parse_args()
    wb=load_workbook(a.workbook,data_only=True); errs=[]; warnings=[]
    if a.mode in ("recording","combined") and "04_拍摄执行卡" not in wb.sheetnames: errs.append("MISSING_04")
    if a.mode in ("h3","combined") and "05_AI数字人口播执行卡" not in wb.sheetnames: errs.append("MISSING_05")
    if "04_拍摄执行卡" in wb.sheetnames:
        ws=wb["04_拍摄执行卡"]; hdr=[ws.cell(1,c).value for c in range(1,ws.max_column+1)]
        required=["执行段ID","平台","对应台词（逐字同全文）","具体画面、机位、动作与切点","素材、真实性与拍摄注意"]
        for x in required:
            if x not in hdr: errs.append("04_MISSING_COLUMN:"+x)
    if "05_AI数字人口播执行卡" in wb.sheetnames:
        ws=wb["05_AI数字人口播执行卡"]; hdr=[ws.cell(4,c).value for c in range(1,ws.max_column+1)]
        required=["视频ID","平台","H3镜头ID","对应04执行卡ID","成片时间码（与04时间轴对齐）","本镜台词（逐字；D02的A/B标签不朗读）","参考素材选择（Reference Selection）","参考标签映射（Reference Role Mapping）","H3单镜头Prompt（可复制）"]
        for x in required:
            if x not in hdr: errs.append("05_MISSING_COLUMN:"+x)
        ix={h:i+1 for i,h in enumerate(hdr)}
        for r in range(5,ws.max_row+1):
            row={h:ws.cell(r,c).value for h,c in ix.items()}
            if not row.get("H3镜头ID"): continue
            sel=str(row.get("参考素材选择（Reference Selection）") or "")
            prompt=str(row.get("H3单镜头Prompt（可复制）") or "")
            if "A01" not in sel and "Audio 1" in prompt: errs.append(f"OPTIONAL_AUDIO_REFERENCE_LEFT_IN_PROMPT:{row.get('H3镜头ID')}")
            if "R-" in sel and ("not upload" not in sel.lower() and "不传" not in sel): warnings.append(f"CHECK_R_AS_POST_INSERT:{row.get('H3镜头ID')}")
            if not row.get("生成后验收点"): errs.append(f"MISSING_QA:{row.get('H3镜头ID')}")
    print(json.dumps({"ok":not errs,"errors":errs,"warnings":warnings},ensure_ascii=False,indent=2))
    return 1 if errs else 0
if __name__=="__main__": sys.exit(main())
