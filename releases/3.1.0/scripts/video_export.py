#!/usr/bin/env python3
"""Append the 37-column H3 card and enforce mode-specific workbook sheets."""
import argparse,json,math,os,tempfile
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
from video_execution_contract import validate_video_production
H3_COLUMNS=[("video_id","视频ID"),("platform","平台"),("h3_shot_id","H3镜头ID"),("segment_id","对应04执行卡ID"),("timecode","成片时间码（与04时间轴对齐）"),("generation_seconds","H3单次生成时长(s)"),("purpose","本镜任务/叙事功能"),("dialogue","本镜台词（逐字；D02的A/B标签不朗读）"),("visual_type","画面类型"),("generation_method","生成/合成方式"),("input_mode","H3输入模式"),("speaker_id","出镜主体/Speaker ID"),("identity_lock","人物身份锁定"),("emotion","表情/情绪"),("voice_requirements","口播/声音要求"),("main_action","主体动作/手势（单一主动作）"),("framing_composition","景别/构图"),("camera_angle","机位/角度"),("movement","主运镜类型"),("movement_spec","运镜幅度/速度/终点"),("scene_light","场景/背景/光线"),("action_timeline","镜头内动作时间线"),("reference_selection","参考素材选择（Reference Selection）"),("reference_role_mapping","参考标签映射（Reference Role Mapping）"),("reshoot_asset_ids","本镜需补拍素材ID"),("reshoot_type","补拍素材类型"),("reshoot_content","补拍内容/画面要求"),("reshoot_shooting","补拍具体拍法（机位/构图/动作）"),("asset_acceptance","素材验收/命名"),("post_insert","后期插入位置/用途"),("subtitle","重点字幕（后期叠加）"),("sound_design","声音设计"),("continuity","前后镜头连续性"),("negative_constraints","H3负面约束"),("prompt","H3单镜头Prompt（可复制）"),("post_generation_qa","生成后验收点"),("status_path","生成状态/文件路径")]
WIDTHS=[12,12,16,18,22,14,22,58,32,38,22,22,42,24,36,32,42,30,18,30,42,58,58,58,24,22,58,58,42,42,32,36,42,48,100,60,40]
def cell_text(c,v):c.value="" if v is None else str(v);c.data_type="s";c.alignment=Alignment(wrap_text=True,vertical="top");c.font=Font(name="Arial",size=10,color="24332C")
def main():
 p=argparse.ArgumentParser();p.add_argument("--batch",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 batch=json.loads(Path(a.batch).read_text(encoding="utf-8"));report=validate_video_production(batch)
 if report["errors"]:raise ValueError("; ".join(report["errors"]))
 mode=report["mode"];vp=batch.get("video_production",{});out=Path(a.output);wb=load_workbook(out)
 if mode=="h3":
  for n in list(wb.sheetnames):
   if "拍摄执行卡" in n:del wb[n]
 if mode in {"h3","combined"}:
  name="05_AI数字人口播执行卡"
  if name in wb.sheetnames:del wb[name]
  ws=wb.create_sheet(name);ws.sheet_view.showGridLines=False
  ws.append(["05｜AI数字人口播执行卡（H3视频创作分镜表）"]+[""]*(len(H3_COLUMNS)-1));ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(H3_COLUMNS))
  ws.append(["使用方式：每行是一条独立H3镜头或一条必须使用真人实拍的插入镜头。H3只生成数字人口播主画面；真实UI、采访、测试、产品/项目证据由团队实拍并在后期插入。时间码与脚本/04一致；单次生成时长按当前核验模型配置填写（本轮样例为4–15秒）。"]+[""]*(len(H3_COLUMNS)-1));ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=len(H3_COLUMNS))
  ws.append(["共享素材：P01身份；P02场景；A01授权声音（可选）；P03+镜头专用；R素材真实补拍，默认不传H3只后期插入。未选A01必须删除Audio 1；真人采访者默认本人实拍。模型参数按当前版本核验。"]+[""]*(len(H3_COLUMNS)-1));ws.merge_cells(start_row=3,start_column=1,end_row=3,end_column=len(H3_COLUMNS))
  ws.append([label for _,label in H3_COLUMNS]);ws.freeze_panes="E5";ws.auto_filter.ref=f"A4:{get_column_letter(37)}{4+len(vp['h3_cards'])}"
  for i,width in enumerate(WIDTHS,1):ws.column_dimensions[get_column_letter(i)].width=width
  for c in ws[1]:c.fill=PatternFill("solid",fgColor="355344");c.font=Font(name="Arial",size=12,bold=True,color="FFFFFF");c.alignment=Alignment(wrap_text=True,vertical="center")
  for rn in (2,3):
   c=ws.cell(rn,1);c.fill=PatternFill("solid",fgColor="EAF0EB" if rn==2 else "F4F0E7");c.font=Font(name="Arial",size=10,color="24332C");c.alignment=Alignment(wrap_text=True,vertical="center")
  for c in ws[4]:c.fill=PatternFill("solid",fgColor="355344");c.font=Font(name="Arial",size=10,bold=True,color="FFFFFF");c.alignment=Alignment(wrap_text=True,vertical="center")
  ws.row_dimensions[1].height=34;ws.row_dimensions[2].height=68;ws.row_dimensions[3].height=92;ws.row_dimensions[4].height=66
  for i,card in enumerate(vp["h3_cards"]):
   r=i+5
   for j,(k,_) in enumerate(H3_COLUMNS,1):cell_text(ws.cell(r,j),card.get(k,""))
   m=max(len(str(card.get(k,"") or "")) for k,_ in H3_COLUMNS);ws.row_dimensions[r].height=min(409,max(48,math.ceil(m/90)*22))
  ovname=next((n for n in wb.sheetnames if n.startswith("00") and "使用总览" in n),None)
  if ovname:wb[ovname].append(["视频制作模式",mode,"05 H3数字人口播执行卡","模型参数按本次核验执行",str(vp.get("model_profile",{}).get("verification_status","NOT_VERIFIED"))])
 elif mode=="recording":
  ovname=next((n for n in wb.sheetnames if n.startswith("00") and "使用总览" in n),None)
  if ovname:wb[ovname].append(["视频制作模式","recording","04真人拍摄执行卡","不生成H3逐镜Prompt","按真实拍摄/录屏执行"])
 fd,tmp=tempfile.mkstemp(suffix=".xlsx",dir=out.parent);os.close(fd);wb.save(tmp);wb.close()
 check=load_workbook(tmp,data_only=False)
 if mode=="h3" and any("拍摄执行卡" in n for n in check.sheetnames):raise ValueError("H3-only mode must not export full 04 card")
 if mode in {"h3","combined"}:
  ws=check["05_AI数字人口播执行卡"]
  if ws.max_column!=37 or ws.max_row!=4+len(vp["h3_cards"]):raise ValueError("05 sheet shape/row count mismatch")
  if [ws.cell(4,j).value for j in range(1,38)] != [label for _,label in H3_COLUMNS]:raise ValueError("05 header row mismatch")
  for i,card in enumerate(vp["h3_cards"],5):
   for j,(k,_) in enumerate(H3_COLUMNS,1):
    if ws.cell(i,j).value!=("" if card.get(k) is None else str(card.get(k))):raise ValueError(f"05 roundtrip mismatch row {i} field {k}")
  if any(c.data_type=="f" for sh in check for row in sh for c in row):raise ValueError("unexpected spreadsheet formula")
 check.close();os.replace(tmp,out)
 from openpyxl import load_workbook as lw
 verify=lw(out,read_only=True);names=verify.sheetnames;verify.close()
 print(json.dumps({"mode":mode,"h3_rows":len(vp.get("h3_cards",[])),"sheet_names":names,"roundtrip":"PASS","warnings":report["warnings"]},ensure_ascii=False))
if __name__=="__main__":main()
