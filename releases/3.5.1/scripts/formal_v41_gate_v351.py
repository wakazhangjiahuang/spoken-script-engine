#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
def validate_formal_v41(batch,review,batch_path,validator,require_full=False):
 errors=[]
 raw_sha=hashlib.sha256(Path(batch_path).read_bytes()).hexdigest()
 payload_sha=hashlib.sha256(json.dumps(batch,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
 if review.get("batch_sha256") not in (raw_sha,payload_sha):
  return ["AI_VIDEO_V4_1_REVIEW_NOT_BOUND_TO_BATCH_BYTES"],{"status":"INVALID_INPUT","items":[]}
 bound=dict(review);bound["batch_sha256_payload"]=payload_sha
 result=validator(batch,bound);status=result.get("status")
 if status in ("NEEDS_REVISION","INVALID_INPUT"):
  errors.extend(["AI_VIDEO_V4_1_FORMAL_VALIDATOR:"+str(x) for x in result.get("errors",[])])
  if not result.get("errors"):errors.append("AI_VIDEO_V4_1_FORMAL_VALIDATOR_STATUS:"+str(status))
 for item in result.get("items",[]):
  pending=item.get("validation_pending",[]) if isinstance(item,dict) else []
  sid=str(item.get("script_id","UNKNOWN"))
  if "independent_review" in pending:errors.append("AI_VIDEO_INDEPENDENT_REVIEW_MISSING:"+sid)
  roles=[x for x in pending if str(x).startswith("review_role:")]
  if roles:errors.append("AI_VIDEO_REVIEW_ROUTING_INCOMPLETE:"+sid+":"+",".join(roles))
 if require_full and status!="PASS":errors.append("AI_VIDEO_FULL_VALIDATION_REQUIRED:"+str(status))
 return errors,result
