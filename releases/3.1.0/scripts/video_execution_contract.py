#!/usr/bin/env python3
"""Deterministic video-card checks; does not certify visual quality or model output."""
import re
H3_REQUIRED=("video_id","platform","h3_shot_id","segment_id","timecode","generation_seconds","purpose","dialogue","visual_type","generation_method","input_mode","speaker_id","identity_lock","emotion","voice_requirements","main_action","framing_composition","camera_angle","movement","movement_spec","scene_light","action_timeline","reference_selection","reference_role_mapping","reshoot_asset_ids","reshoot_type","reshoot_content","reshoot_shooting","asset_acceptance","post_insert","subtitle","sound_design","continuity","negative_constraints","prompt","post_generation_qa","status_path")
PROMPT_SECTIONS=("subject_definitions:","summary:","retention_analysis:","detailed_description:","overall_soundscape:","non_diegetic_music:")
PLATFORM_ALIASES={"douyin":{"douyin","抖音"},"channels":{"channels","视频号","微信视频号"},"xiaohongshu":{"xiaohongshu","小红书"}}
def _clock(v):
 p=v.strip().split(":")
 try:
  if len(p)==3:return int(p[0])*3600+int(p[1])*60+float(p[2])
  if len(p)==2:return int(p[0])*60+float(p[1])
  return float(v)
 except (ValueError,TypeError):return None
def _range(v):
 if not isinstance(v,str):return None
 b=re.split(r"\s*[–—-]\s*",v.strip(),maxsplit=1)
 if len(b)!=2:return None
 s,e=_clock(b[0]),_clock(b[1])
 return (s,e) if s is not None and e is not None and e>s else None
def validate_video_production(batch):
 errors=[];warnings=[];brief=batch.get("brief",{});vp=batch.get("video_production",{});mode=vp.get("mode") or brief.get("production_mode") or "recording"
 if mode not in {"recording","h3","combined"}:return {"mode":mode,"errors":["production mode must be recording, h3 or combined"],"warnings":[]}
 if brief.get("production_mode") and brief["production_mode"]!=mode:errors.append("brief.production_mode and video_production.mode mismatch")
 scripts={s.get("id"):s for s in batch.get("scripts",[])}
 if mode in {"h3","combined"}:
  cards=vp.get("h3_cards")
  if not isinstance(cards,list) or not cards:errors.append("H3/combined mode requires video_production.h3_cards");return {"mode":mode,"errors":errors,"warnings":warnings}
  profile=vp.get("model_profile",{});profile=profile if isinstance(profile,dict) else {};mn=profile.get("min_seconds",4);mx=profile.get("max_seconds",15)
  if type(mn) not in (int,float) or type(mx) not in (int,float) or mn<=0 or mx<mn:errors.append("invalid H3 model_profile min_seconds/max_seconds");mn,mx=4,15
  if profile.get("verification_status")!="VERIFIED":warnings.append("H3 model limits are not independently verified against current official documentation; sample profile is a reference only")
  if not profile.get("model_name") or not profile.get("checked_at") or not profile.get("source_basis"):errors.append("H3 model_profile must record model_name, checked_at and source_basis")
  seen=set();timelines={}
  for i,c in enumerate(cards):
   label=f"H3 card[{i}]"
   if not isinstance(c,dict):errors.append(label+" must be an object");continue
   for f in H3_REQUIRED:
    if f not in c or c[f] is None or c[f]=="":errors.append(label+" missing "+f)
   vid=c.get("video_id");script=scripts.get(vid)
   if not script:errors.append(label+" unknown video_id/script_id");continue
   if c.get("platform") not in PLATFORM_ALIASES.get(script.get("platform"),set()):errors.append(label+" platform does not match script")
   sid=c.get("h3_shot_id")
   if sid in seen:errors.append("duplicate h3_shot_id "+str(sid))
   seen.add(sid)
   seg=next((g for g in script.get("segments",[]) if g.get("id")==c.get("segment_id")),None)
   if not seg:errors.append(label+" segment_id does not exist in script")
   elif c.get("dialogue") and c["dialogue"] not in seg.get("text",""):errors.append(label+" dialogue is not a verbatim substring of the source segment")
   tr=_range(c.get("timecode",""))
   if not tr:errors.append(label+" invalid timecode range")
   else:timelines.setdefault(vid,[]).append((tr[0],tr[1],sid))
   im=str(c.get("input_mode",""));gm=str(c.get("generation_method",""));live=("不调用H3" in im) or ("真人采访" in gm);prompt=str(c.get("prompt",""))
   if live:
    if prompt.strip() and "不调用H3" not in prompt:errors.append(label+" live interview row must not contain an H3 generation prompt")
    duration=str(c.get("generation_seconds","")).strip()
    if duration not in {"","0","—","不适用"} and not duration.startswith("—（真人"):errors.append(label+" live interview row must not claim H3 generation seconds")
   else:
    seconds=c.get("generation_seconds")
    if type(seconds) not in (int,float) or not mn<=seconds<=mx:errors.append(label+f" H3 generation_seconds must be within current profile {mn}–{mx}")
    missing=[x for x in PROMPT_SECTIONS if x not in prompt]
    if missing:errors.append(label+" prompt missing sections: "+", ".join(missing))
    refs=str(c.get("reference_selection",""));mapping=str(c.get("reference_role_mapping",""))
    if "P01" not in refs or "P02" not in refs:errors.append(label+" reference_selection must bind P01 identity and P02 scene")
    if not all(t in mapping for t in ("<Picture 1>","<Picture 2>","<Subject 1>","<Subject 2>")) or "身份" not in mapping or "场景" not in mapping:errors.append(label+" reference_role_mapping must distinguish Picture 1 identity from Picture 2 scene")
    audio=c.get("audio_reference_selected") is True
    if audio:
     if "A01" not in refs or c.get("audio_authorization_status")!="authorized":errors.append(label+" selected A01 requires explicit audio authorization")
     if "Audio 1" not in prompt:errors.append(label+" A01 selected but Audio 1 mapping missing")
    elif "Audio 1" in prompt or "<Audio 1>" in prompt:errors.append(label+" Audio 1 remains although A01 was not selected")
    rids=c.get("reshoot_asset_ids",[])
    if isinstance(rids,str):rids=[x.strip() for x in re.split(r"[,，;；\s]+",rids) if x.strip()]
    if rids and ("不传" not in mapping and "后期" not in mapping):errors.append(label+" R assets must be marked post-only, not H3 inputs")
    if not c.get("negative_constraints") or not c.get("post_generation_qa"):errors.append(label+" negative constraints and post-generation QA are required")
    if not c.get("movement_spec") or not c.get("action_timeline"):errors.append(label+" movement specification and action timeline are required")
    speaker=str(c.get("speaker_id",""))
    if ("S2" in speaker or "真人" in speaker) and c.get("identity_authorization")!="authorized":errors.append(label+" real-person digital replication requires explicit identity authorization")
  for vid,spans in timelines.items():
   spans.sort()
   for prev,cur in zip(spans,spans[1:]):
    if cur[0]<prev[1]-0.02:errors.append(vid+" H3 timecodes overlap: "+str(prev[2])+"/"+str(cur[2]))
 return {"mode":mode,"errors":errors,"warnings":warnings}
