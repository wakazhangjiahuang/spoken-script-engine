#!/usr/bin/env python3
"""P+2-table contract; deterministic text roundtrip, not editorial assessment."""
import argparse,json,math,os,tempfile
from pathlib import Path
from openpyxl import Workbook,load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
from validate_batch import validate,units
from surface_contract import output_errors
from execution_contract import read,digest
NAMES={'xiaohongshu':'小红书','douyin':'抖音','channels':'视频号'}
COLORS=['EAF2E7','FFF3D9','F8E9EC','EEE8F4','E6F1EF','F6EADC']
HEADERS=['脚本ID','内容任务','主要受众','封面主标题','封面副标题','0–3秒｜黄金三秒','3–8秒｜推进与继续理由','正文｜判断与证据','Calling｜单一主动作','评论钩子｜同一目的','分镜画面提要｜详见执行卡','发布文案','关键词','时长与试读状态','口播字数','编辑诊断｜非效果评分','完整可朗读稿']
SHOT_HEADERS=['脚本ID','平台','时间建议','段落功能','对应口播台词','画面／镜头动作','屏幕重点字','素材状态／真实性／拍摄提示']
def display_note(value):
 return str(value).replace('director_plan.fallback','总览中的替代拍法').replace('NOT_RUN','尚未实测').replace('available','现有')
def cell_text(ws,row,col,value):
 c=ws.cell(row,col,value)
 if isinstance(value,str):c.data_type='s' # Never interpret user content as a formula.
 return c
def make_sheet(wb,name,title,headers,widths):
 ws=wb.create_sheet(name);ws.sheet_view.showGridLines=False
 ws.append([title]);ws.merge_cells(start_row=1,start_column=1,end_row=1,end_column=len(headers));ws.row_dimensions[1].height=34
 ws.append(headers);ws.freeze_panes='F3' if len(headers)==17 else 'E3'
 for i,w in enumerate(widths,1):ws.column_dimensions[get_column_letter(i)].width=w
 for c in ws[1]+ws[2]:c.fill=PatternFill('solid',fgColor='355344');c.font=Font(name='Arial',size=12,bold=True,color='FFFFFF');c.alignment=Alignment(wrap_text=True,vertical='center')
 ws.row_dimensions[2].height=42
 ws.sheet_properties.pageSetUpPr.fitToPage=True;ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0;ws.print_title_rows='1:2'
 return ws
def add_row(ws,values,color):
 row=ws.max_row+1
 for j,value in enumerate(values,1):
  c=cell_text(ws,row,j,value);c.fill=PatternFill('solid',fgColor=color);c.font=Font(name='Arial',size=11,color='24332C');c.alignment=Alignment(wrap_text=True,vertical='top')
 # Wide readable cells plus ample row height; reject pathological overflow rather than clipping silently.
 lines=max(sum(max(1,math.ceil(len(line)*1.7/max(ws.column_dimensions[get_column_letter(j)].width-2,8))) for line in str(v or '').split('\n')) for j,v in enumerate(values,1))
 height=max(40,lines*16+12)
 if height>409:raise ValueError('cell too long for readable worksheet row; shorten or split the script before export')
 ws.row_dimensions[row].height=height
 return row
def build(batch,review,out,kb,validation):
 errors=[e for s in batch['scripts'] for e in output_errors(s,batch['brief'])]
 if errors:raise ValueError('; '.join(errors))
 wb=Workbook();wb.remove(wb.active)
 overview=make_sheet(wb,'00使用总览','口播执行工作簿 v3.0.0｜编辑通过不等于发布或效果通过',['脚本ID／项目','平台／状态','标题／操作','检查／未完成事项','评分明细／拍摄准备'],[24,20,44,60,68])
 add_row(overview,['使用','按ID定位','平台表F–I分段朗读；Q列复制完整稿；执行卡筛选ID','只念台词，不念段落标签。时间轴为估算，拍摄后校准。','颜色区分稿件；不代表内容等级。'],'EAF2E7')
 add_row(overview,['交付状态','内容校对已记录；待用户审稿' if validation['editorial_status']=='REVIEWED' else '编辑待复审','发布条件已核验' if validation['publication_status']=='READY_FOR_USER_REVIEW' else '待真人试读、素材或发布核验','真人试读、待拍素材与账号规则逐项核验；本文件不发布。','实际留存、有效咨询和成交：尚未实测'],'FFF3D9')
 rubric=read(Path(kb)/'rubrics/quality.json');items={x['script_id']:x for x in review['items']};expected={};shot_rows={};platform_rows={}
 for pi,p in enumerate(batch['brief']['platforms'],1):
  scripts=[s for s in batch['scripts'] if s['platform']==p];name=f'{pi:02d}{NAMES[p]}{len(scripts)}篇'
  ws=make_sheet(wb,name,NAMES[p]+'｜口播、发布与完整朗读稿',HEADERS,[16,20,25,30,28,32,38,66,40,40,60,46,24,27,12,16,100]);platform_rows[p]=ws
  for i,s in enumerate(scripts):
   segs=s['segments'];speech='\n'.join(g['text'] for g in segs);expected[s['id']]=speech
   body='\n'.join(g['text'] for g in segs if g['role'] in ('context','judgment','value'))
   scores=items[s['id']].get('scores',{});score='；'.join(d['name']+':'+str(scores[d['id']]['score'])+'/4' for d in rubric['dimensions'] if d['id'] in scores) or '未使用数值评分；按实际成品复核'
   total=sum(g['duration_seconds'] for g in segs);rt=s.get('read_test',{});time=f'预计 {total:g} 秒；'+(f"实读 {rt['seconds']:g} 秒" if rt.get('status')=='MEASURED' else '真人试读待完成')
   vals=[s['id'],s['positioning'],s['audience'],s['cover_main'],s['cover_sub'],segs[0]['text'],segs[1]['text'],body,segs[-1]['text'],(s['comment_hook']['line'] if s['comment_hook']['placement'] not in ('disabled','alternative') else '不并行启用：'+s['comment_hook']['line']),' → '.join(g['id']+'：'+g['visual'][:28] for g in segs),s['publish_description'],'；'.join(s['keywords']),time,units(speech),score,speech]
   rn=add_row(ws,vals,COLORS[i%6]);shot_rows[s['id']]=[]
   dims=score+'（仅诊断，不作达标依据）'
   d=s['director_plan'];pc=next(x for x in review['platform_checks'] if x['platform']==p)
   missing=[x['id']+'待拍' for x in batch['brief']['production_resources'] if x['status']=='planned' and x['id'] in {g['shot']['material_id'] for g in segs}]
   info='；'.join(([time] if rt.get('status')!='MEASURED' else [])+missing+[{'PARTIAL':'规则待核验','VERIFIED':'规则已核验','UNVERIFIED':'规则未核验'}.get(pc['status'],'规则待核验')+'：'+pc['scope']]+pc['restrictions'])
   rr=add_row(overview,[s['id'],NAMES[p],s['title'],info,dims+'\n表演：'+display_note(d['performance_note'])+'\n顺序：'+'→'.join(d['shoot_order'])+'\n连续性：'+d['continuity']+'\n替代：'+d['fallback']],COLORS[i%6]);overview.cell(rr,1).hyperlink=f"#'{name}'!A{rn}"
   add_row(overview,[s['id']+'/封面',NAMES[p],s['cover_main']+'｜'+s['cover_sub'],s['cover']+'\n全片视觉与封面安排：'+d['visual_premise'],'形制：'+d['format']+'\n剪辑：'+d['editing_rule']+'\n完整封面、缩略图和分享裁切须实物预览；文案锁定例外不代表排版已通过'],COLORS[i%6])
  ws.auto_filter.ref=f'A2:Q{ws.max_row}'
 shotname=f"{len(batch['brief']['platforms'])+1:02d}拍摄执行卡";ws=make_sheet(wb,shotname,'逐段台词与画面对应｜筛选脚本ID',SHOT_HEADERS,[16,14,20,20,70,70,30,70]);resources={x['id']:x for x in batch['brief']['production_resources']}
 for i,s in enumerate(batch['scripts']):
  t=0
  for g in s['segments']:
   end=t+g['duration_seconds'];sh=g['shot'];resource=resources.get(sh['material_id']);state='无专用素材；按替代方案明确示意' if not resource else {'available':'现有','planned':'待拍／待制作','unavailable':'不可用'}[resource['status']]+'｜'+display_note(resource['description'])
   row=[s['id'],NAMES[s['platform']],f'预计{t:g}–{end:g}秒｜待镜头实测',g['id']+'｜'+g['purpose'],g['text'],'\n'.join(dict.fromkeys([sh['framing']+'｜'+sh['camera'],g['visual'],sh['action'],'剪辑：'+sh['edit_cue']])),g['subtitle'],'素材ID：'+sh['material_id']+'｜'+state+'\n声音：'+sh['sound']+f"；静默留时 {sh['silent_hold_seconds']:g} 秒\n"+display_note(g.get('notes',''))]
   shot_rows[s['id']].append(add_row(ws,row,COLORS[i%6]));t=end
 ws.auto_filter.ref=f'A2:H{ws.max_row}';overview.freeze_panes='A3'
 out=Path(out);fd,tmp=tempfile.mkstemp(suffix='.xlsx',dir=out.parent);os.close(fd)
 wb.save(tmp);wb.close()
 reopened=load_workbook(tmp,data_only=False)
 if len(reopened.sheetnames)!=len(batch['brief']['platforms'])+2:raise ValueError('sheet contract mismatch')
 observed={}
 for ws in list(reopened)[1:-1]:
  for row in ws.iter_rows(min_row=3,values_only=True):
   sid=row[0];joined='\n'.join(row[k] for k in [5,6,7,8]);observed[sid]=row[16]
   source=next(s for s in batch['scripts'] if s['id']==sid)
   if row[3]!=source['cover_main'] or row[4]!=source['cover_sub'] or row[9]!=(source['comment_hook']['line'] if source['comment_hook']['placement'] not in ('disabled','alternative') else '不并行启用：'+source['comment_hook']['line']):raise ValueError('cover/comment field roundtrip mismatch '+sid)
   if joined!=expected[sid] or row[16]!=expected[sid]:raise ValueError('spoken text roundtrip mismatch '+sid)
 if observed!=expected:raise ValueError('missing or duplicate script rows')
 actual={sid:[] for sid in expected}
 for row in reopened[shotname].iter_rows(min_row=3,values_only=True):
  sid=row[0];index=len(actual[sid]);source=next(s for s in batch['scripts'] if s['id']==sid)['segments'][index]
  if not str(row[3]).startswith(source['id']+'｜') or not str(row[7]).startswith('素材ID：'+source['shot']['material_id']+'｜'):raise ValueError('shot identity/material roundtrip mismatch '+sid)
  actual[sid].append(row[4])
 for source in batch['scripts']:
  matches=[row for row in reopened['00使用总览'].iter_rows(values_only=True) if row[0]==source['id']+'/封面']
  if len(matches)!=1 or matches[0][3]!=source['cover']+'\n全片视觉与封面安排：'+source['director_plan']['visual_premise']:raise ValueError('cover execution roundtrip mismatch '+source['id'])
 if {k:'\n'.join(v) for k,v in actual.items()}!=expected:raise ValueError('shot transcript mismatch')
 if any(c.data_type=='f' for ws in reopened for row in ws for c in row):raise ValueError('unexpected spreadsheet formula')
 reopened.close();os.replace(tmp,out);return {'sheets':len(wb.sheetnames),'scripts':len(expected),'shot_rows':sum(len(x) for x in shot_rows.values()),'exact_text_roundtrip':True,'visual_preview':'NOT_RUN'}
def main():
 p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('review');p.add_argument('output');p.add_argument('kb');p.add_argument('run');a=p.parse_args();b=read(a.batch);r=read(a.review);v=validate(b,r,digest(a.batch),kb=a.kb,run_dir=a.run)
 if not v['passed']:raise ValueError(json.dumps(v,ensure_ascii=False))
 print(json.dumps(build(b,r,a.output,a.kb,v),ensure_ascii=False))
if __name__=='__main__':main()
