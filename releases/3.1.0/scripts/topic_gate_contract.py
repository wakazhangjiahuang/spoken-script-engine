#!/usr/bin/env python3
"""Explicit user-approved topic gate. Checks traceable fields, not hidden reasoning."""
PLATFORMS={"douyin","channels","xiaohongshu"}
CANDIDATE_FIELDS=("candidate_id","platform","topic_title","core_question","target_audience","audience_job","audience_pain_or_desire","why_care","viewer_payoff","story_mechanism","proof_basis","proof_status","calling_reason","platform_expression","differentiation","self_audit")
AUDIT_TEXT_FIELDS=("creator_case","audience_counterargument","evidence_check","revision_decision","public_summary")
AUDIT_DIMENSIONS=("audience_specificity","viewer_relevance","benefit_clarity","evidence_sufficiency","story_progression","platform_fit","originality","claim_safety")
def validate_topic_gate(decision,brief):
 if not brief.get("topic_gate_required",False):return []
 errors=[];gate=decision.get("topic_gate")
 if not isinstance(gate,dict):return ["topic confirmation gate missing; do not draft before user approval"]
 if gate.get("status") not in {"USER_APPROVED","USER_LOCKED"}:errors.append("topic gate has no explicit user approval")
 if gate.get("confirmation_source") not in {"current_user_turn","explicit_user_request"}:errors.append("confirmation source must be the user's own message")
 if not isinstance(gate.get("confirmation_text"),str) or not gate["confirmation_text"].strip():errors.append("exact user confirmation text missing")
 candidates=gate.get("candidates")
 if not isinstance(candidates,list) or not candidates:return errors+["topic gate candidates missing"]
 by_id={}
 for i,c in enumerate(candidates):
  prefix=f"topic candidate[{i}]"
  if not isinstance(c,dict):errors.append(prefix+" must be an object");continue
  for f in CANDIDATE_FIELDS:
   if f not in c or c[f] in (None,"",[],{}):errors.append(prefix+" missing "+f)
  cid=c.get("candidate_id")
  if not isinstance(cid,str) or not cid.strip():continue
  if cid in by_id:errors.append("duplicate topic candidate id "+cid)
  by_id[cid]=c
  if c.get("platform") not in PLATFORMS or c.get("platform") not in brief.get("platforms",[]):errors.append(cid+" has unrequested/unknown platform")
  if c.get("proof_status") not in {"available","planned","not_required","missing"}:errors.append(cid+" invalid proof_status")
  audit=c.get("self_audit")
  if not isinstance(audit,dict):errors.append(cid+" self_audit missing");continue
  for f in AUDIT_TEXT_FIELDS:
   if not isinstance(audit.get(f),str) or not audit[f].strip():errors.append(cid+" self_audit missing "+f)
  dims=audit.get("dimensions",{})
  for d in AUDIT_DIMENSIONS:
   if dims.get(d) not in {"PASS","CONDITIONAL","FAIL"}:errors.append(cid+" self_audit dimension missing/invalid "+d)
  verdict=audit.get("verdict")
  if verdict not in {"PASS","CONDITIONAL","REJECT"}:errors.append(cid+" invalid self_audit verdict")
  if verdict=="CONDITIONAL" and not audit.get("condition"):errors.append(cid+" conditional topic must state its condition")
  if c.get("proof_status")=="missing" and verdict!="REJECT":errors.append(cid+" unsupported proof cannot pass topic gate")
  if verdict in {"PASS","CONDITIONAL"} and any(dims.get(k)=="FAIL" for k in AUDIT_DIMENSIONS):errors.append(cid+" failed audit dimension cannot pass")
  if c.get("proof_status")=="planned" and verdict=="PASS":errors.append(cid+" planned evidence must be marked CONDITIONAL")
 approved=gate.get("approved_topic_ids")
 if not isinstance(approved,list) or not approved or len(approved)!=len(set(approved)):errors.append("approved_topic_ids must be a non-empty unique list");approved=[]
 for cid in approved:
  c=by_id.get(cid)
  if not c:errors.append("approved topic does not exist: "+str(cid));continue
  audit=c.get("self_audit",{})
  if audit.get("verdict") not in {"PASS","CONDITIONAL"}:errors.append("rejected topic cannot be approved: "+cid)
  if any(audit.get("dimensions",{}).get(k)=="FAIL" for k in AUDIT_DIMENSIONS):errors.append("topic with failed audit cannot be approved: "+cid)
 used={}
 for row in decision.get("selected",[]):
  cid=row.get("topic_candidate_id")
  if cid not in approved:errors.append(str(row.get("id"))+" is not bound to a user-approved topic_candidate_id");continue
  if by_id.get(cid,{}).get("platform")!=row.get("platform"):errors.append(str(row.get("id"))+" topic candidate platform mismatch")
  used.setdefault(row.get("platform"),[]).append(cid)
 counts=brief.get("count_per_platform",{})
 for platform in brief.get("platforms",[]):
  n=counts.get(platform,3);approved_n=sum(1 for cid in approved if by_id.get(cid,{}).get("platform")==platform);selected=used.get(platform,[])
  if approved_n<n:errors.append(f"{platform} approved topics {approved_n} below requested script count {n}")
  if len(selected)!=len(set(selected)):errors.append(platform+" reuses topic candidate for multiple scripts")
  if len(selected)!=n:errors.append(f"{platform} selected scripts must map one-to-one to {n} approved topics")
 return errors
