#!/usr/bin/env python3
"""Validate Topic Gate decision JSON. Does not evaluate hidden reasoning."""
import argparse, json, sys
REQ = ["audience","current_situation","user_question","why_me","benefit","story_engine","proof_plan","platform_reason","action_reason","non_overlap"]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("decision")
    ap.add_argument("--allow-locked",action="store_true")
    a=ap.parse_args()
    d=json.load(open(a.decision,encoding="utf-8"))
    gate=d.get("topic_gate",{})
    errors=[]
    if not gate.get("confirmation_text") and not (a.allow_locked and gate.get("status")=="USER_LOCKED"):
        errors.append("TOPIC_NOT_CONFIRMED")
    candidates=gate.get("candidates",[])
    if not candidates: errors.append("NO_TOPIC_CANDIDATES")
    for i,c in enumerate(candidates,1):
        for k in REQ:
            if not str(c.get(k,"")).strip(): errors.append(f"CANDIDATE_{i}_MISSING_{k}")
        if c.get("proof_status") in ("unknown","missing") and c.get("claim_level")=="verified":
            errors.append(f"CANDIDATE_{i}_UNSUPPORTED_VERIFIED_CLAIM")
    selected=d.get("selected",[])
    if gate.get("confirmation_text") and not selected:
        errors.append("NO_SELECTED_TOPICS")
    for i,s in enumerate(selected,1):
        if not s.get("topic_candidate_id"): errors.append(f"SELECTED_{i}_MISSING_TOPIC_ID")
    print(json.dumps({"ok":not errors,"errors":errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
