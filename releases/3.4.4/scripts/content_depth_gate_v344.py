#!/usr/bin/env python3
"""v3.4.4 content-depth gate: verifies that professional decisions are spoken and reviewed."""
from __future__ import annotations
AI_CORE={"audience_need","cover_click_reason","opening_bridge","body_payoff"}
ILL_CORE={"audience_and_task","entry_and_click_reason","first_8_seconds","professional_judgment_and_payoff"}
BODY_ROLES={"context","judgment","value","proof","evidence","material","decision"}
REQUIRED_ANCHORS={
 "concrete_input":(18,BODY_ROLES),"constraints":(16,BODY_ROLES),"chosen_option":(8,BODY_ROLES),
 "rejected_option":(8,BODY_ROLES),"option_tradeoff":(20,BODY_ROLES),"decision_reason":(20,BODY_ROLES),
 "observable_payoff":(16,BODY_ROLES),"applicability_boundary":(16,BODY_ROLES),"viewer_action":(12,{"calling","cta"})}
REVIEW_FIELDS=("need_is_specific","click_value_is_user_centered","opening_adds_new_information",
 "body_demonstrates_a_concrete_case","tradeoff_is_explained_in_spoken_words",
 "viewer_can_transfer_the_judgment","calling_has_a_user_value_exchange")
def _s(v): return str(v or "").strip()
def _segments(s): return s.get("segments",[]) if isinstance(s.get("segments"),list) else []
def _find(s,sid): return next((x for x in _segments(s) if _s(x.get("id"))==_s(sid)),None)
def _weighted(scores,weights):
 if not isinstance(scores,dict): return 0.0
 total=0.0
 for k,w in weights.items():
  e=scores.get(k,{}); v=e.get("score") if isinstance(e,dict) else None
  if type(v) is not int or not 0<=v<=5: return 0.0
  total += v*w/5
 return round(total,1)
def validate_content_depth(batch,review,domain):
 errors=[]; diagnostics=[]
 scripts=batch.get("scripts",[]) if isinstance(batch,dict) else []
 items=review.get("items",[]) if isinstance(review,dict) else []
 byid={_s(x.get("script_id")):x for x in items if isinstance(x,dict)}
 if not scripts: return ["CONTENT_DEPTH_BATCH_EMPTY"],diagnostics
 if domain=="ai_video":
  weights={"audience_need":15,"cover_click_reason":15,"opening_bridge":15,"body_payoff":20,"evidence_credibility":10,"platform_native":10,"cta_comment":10,"human_voice_originality":5}; core=AI_CORE
 else:
  weights={"audience_and_task":15,"entry_and_click_reason":15,"first_8_seconds":15,"professional_judgment_and_payoff":20,"facts_evidence_and_rights":15,"platform_native_expression":10,"calling_and_action":5,"spoken_naturalness":5}; core=ILL_CORE
 for script in scripts:
  sid=_s(script.get("script_id") or script.get("id")); pd=script.get("professional_decision") if isinstance(script.get("professional_decision"),dict) else {}
  anchors=pd.get("spoken_anchors") if isinstance(pd.get("spoken_anchors"),dict) else {}
  for key,(minlen,roles) in REQUIRED_ANCHORS.items():
   a=anchors.get(key)
   if not isinstance(a,dict): errors.append(f"{sid}:SPOKEN_DEPTH_ANCHOR_MISSING:{key}"); continue
   seg=_find(script,a.get("segment_id")); quote=_s(a.get("quote"))
   if not seg or len(quote)<minlen or quote not in _s(seg.get("text")): errors.append(f"{sid}:SPOKEN_DEPTH_ANCHOR_NOT_VERBATIM_OR_TOO_THIN:{key}"); continue
   if _s(seg.get("role")).lower() not in roles: errors.append(f"{sid}:SPOKEN_DEPTH_ANCHOR_WRONG_ROLE:{key}")
  body="\n".join(_s(x.get("text")) for x in _segments(script) if _s(x.get("role")).lower() in BODY_ROLES)
  if len(body)<120: errors.append(f"{sid}:BODY_TOO_THIN_FOR_A_CONCRETE_DEMONSTRATION")
  options=pd.get("options_considered",[])
  labels={_s(x.get("option")) for x in options if isinstance(x,dict)}
  if len(options)<2 or len(labels)<2: errors.append(f"{sid}:TWO_MATERIAL_OPTIONS_NOT_PRESENT")
  tradeoffs=[_s(x.get("tradeoff")) for x in options if isinstance(x,dict)]
  if len(tradeoffs)<2 or any(len(x)<18 for x in tradeoffs): errors.append(f"{sid}:OPTION_TRADEOFFS_NOT_EXPLAINED")
  item=byid.get(sid)
  if not item: errors.append(f"{sid}:CONTENT_VALUE_REVIEW_MISSING"); continue
  cvr=item.get("content_value_review")
  if not isinstance(cvr,dict): errors.append(f"{sid}:CONTENT_VALUE_REVIEW_MISSING")
  else:
   speech="\n".join(_s(x.get("text")) for x in _segments(script))
   for field in REVIEW_FIELDS:
    e=cvr.get(field)
    if not isinstance(e,dict) or e.get("passed") is not True: errors.append(f"{sid}:CONTENT_VALUE_REVIEW_FAILED:{field}"); continue
    if len(_s(e.get("reason")))<25 or not _s(e.get("quote")): errors.append(f"{sid}:CONTENT_VALUE_REVIEW_EVIDENCE_TOO_THIN:{field}")
    if _s(e.get("quote")) not in speech: errors.append(f"{sid}:CONTENT_VALUE_REVIEW_QUOTE_NOT_IN_SCRIPT:{field}")
  scores=item.get("scorecard",{}) if domain=="ai_video" else item.get("scores",{})
  if set(scores)!=set(weights): errors.append(f"{sid}:CONTENT_DEPTH_SCORE_DIMENSIONS_MISMATCH"); continue
  for dim in weights:
   e=scores.get(dim,{}); score=e.get("score") if isinstance(e,dict) else None
   if type(score) is not int or score<3 or score>5: errors.append(f"{sid}:CONTENT_DEPTH_DIMENSION_BELOW_3:{dim}")
   if dim in core and (type(score) is not int or score<4): errors.append(f"{sid}:CORE_DIMENSION_BELOW_4:{dim}")
  total=_weighted(scores,weights); diagnostics.append({"script_id":sid,"weighted_score":total,"minimum_total":80})
  if total<80: errors.append(f"{sid}:EDITORIAL_CANDIDATE_BELOW_80:{total}")
 return errors,diagnostics
