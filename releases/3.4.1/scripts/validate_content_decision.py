#!/usr/bin/env python3
"""Validate source-bound professional decisions and anchored review evidence."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

MIN_DIMENSION_SCORE = 3
ALLOWED_SOURCE_STATUS = {"USER_PROVIDED", "VERIFIED", "PUBLIC_SOURCE", "INFERENCE", "SIMULATED", "UNKNOWN"}

def text(v):
    return str(v or "").strip()

def script_id(s):
    return text(s.get("script_id") or s.get("id") or "UNKNOWN")

def segments(s):
    return s.get("segments", []) if isinstance(s.get("segments"), list) else []

def validate_script(s):
    sid = script_id(s); errors = []; pd = s.get("professional_decision")
    if not isinstance(pd, dict):
        return [f"{sid}:PROFESSIONAL_DECISION_MISSING"]
    need = pd.get("audience_need_ref")
    if not isinstance(need, dict) or any(len(text(need.get(k))) < 4 for k in ("source_asset_id", "source_locator", "source_quote")):
        errors.append(f"{sid}:AUDIENCE_NEED_REF_MISSING")
    required = ("viewer_task", "case_mode", "concrete_input", "constraints", "options_considered", "chosen_option", "rejected_option", "decision_reason", "source_status", "evidence_refs", "applicability_boundary", "viewer_action", "spoken_anchor")
    for k in required:
        if not pd.get(k):
            errors.append(f"{sid}:PROFESSIONAL_DECISION_{k.upper()}_MISSING")
    if pd.get("case_mode") not in ("real", "simulated", "method"):
        errors.append(f"{sid}:CASE_MODE_INVALID")
    if pd.get("source_status") not in ALLOWED_SOURCE_STATUS:
        errors.append(f"{sid}:SOURCE_STATUS_INVALID")
    if len(text(pd.get("concrete_input"))) < 10:
        errors.append(f"{sid}:CONCRETE_INPUT_TOO_GENERIC")
    opts = pd.get("options_considered") if isinstance(pd.get("options_considered"), list) else []
    labels = [text(x.get("option")) for x in opts if isinstance(x, dict)]
    if len(opts) < 2 or len(set(labels)) < 2 or any(not text(x.get("tradeoff")) for x in opts if isinstance(x, dict)):
        errors.append(f"{sid}:OPTIONS_NOT_COMPARABLE")
    if text(pd.get("chosen_option")) not in labels or text(pd.get("rejected_option")) not in labels or text(pd.get("chosen_option")) == text(pd.get("rejected_option")):
        errors.append(f"{sid}:DECISION_CHOICE_NOT_TRACEABLE")
    anchor = pd.get("spoken_anchor") if isinstance(pd.get("spoken_anchor"), dict) else {}
    seg = next((x for x in segments(s) if text(x.get("id")) == text(anchor.get("segment_id"))), None)
    quote = text(anchor.get("quote"))
    if not seg or len(quote) < 8 or quote not in text(seg.get("text")) or text(seg.get("role")).lower() in ("hook", "calling", "cta"):
        errors.append(f"{sid}:DECISION_NOT_ANCHORED_IN_SPOKEN_BODY")
    if pd.get("case_mode") == "simulated" or pd.get("source_status") == "SIMULATED":
        d = pd.get("simulation_disclosure") if isinstance(pd.get("simulation_disclosure"), dict) else {}
        dseg = next((x for x in segments(s) if text(x.get("id")) == text(d.get("segment_id"))), None)
        dq = text(d.get("quote"))
        if not dseg or not dq or dq not in text(dseg.get("text")) or not re.search(r"示意|模拟|假设情境|虚构情境", dq):
            errors.append(f"{sid}:SIMULATION_DISCLOSURE_NOT_SPOKEN")
    return errors

def validate_batch(batch):
    scripts = batch.get("scripts", []) if isinstance(batch, dict) else []
    if not isinstance(scripts, list) or not scripts:
        return ["BATCH_SCRIPTS_MISSING"]
    errors = []; ids = [script_id(s) for s in scripts]
    if len(ids) != len(set(ids)):
        errors.append("BATCH_SCRIPT_IDS_DUPLICATED")
    for s in scripts:
        errors.extend(validate_script(s))
    return errors

def validate_review(batch, review, dimensions):
    errors = []; by_id = {script_id(s): s for s in batch.get("scripts", [])}
    items = review.get("items", [])
    if {text(x.get("script_id")) for x in items} != set(by_id):
        return ["REVIEW_ITEMS_DO_NOT_MATCH_BATCH"]
    for item in items:
        sid = text(item.get("script_id")); s = by_id[sid]; body = "\n".join(text(x.get("text")) for x in segments(s))
        scorecard = item.get("scorecard", {})
        if set(scorecard) != set(dimensions):
            errors.append(f"{sid}:SCORECARD_DIMENSIONS_MISMATCH"); continue
        for dim, entry in scorecard.items():
            score = entry.get("score") if isinstance(entry, dict) else None
            quote = text(entry.get("quote")) if isinstance(entry, dict) else ""
            if type(score) is not int or score < MIN_DIMENSION_SCORE:
                errors.append(f"{sid}:DIMENSION_BELOW_3:{dim}")
            if not quote or quote not in body:
                errors.append(f"{sid}:SCORE_QUOTE_NOT_IN_SCRIPT:{dim}")
        pd = s.get("professional_decision", {})
        dr = item.get("professional_decision_review", {})
        expected = text(pd.get("spoken_anchor", {}).get("quote")) if isinstance(pd, dict) else ""
        if dr.get("passed") is not True or text(dr.get("quote")) != expected or expected not in body or len(text(dr.get("reason"))) < 12:
            errors.append(f"{sid}:PROFESSIONAL_DECISION_NOT_REVIEWED")
    return errors

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batch", required=True, type=Path)
    p.add_argument("--review", type=Path)
    p.add_argument("--domain", choices=["ai_video", "illustration"], default="ai_video")
    a = p.parse_args()
    batch = json.loads(a.batch.read_text(encoding="utf-8"))
    errors = validate_batch(batch)
    if a.review:
        review = json.loads(a.review.read_text(encoding="utf-8"))
        dims = ({"audience_need", "cover_click_reason", "opening_bridge", "body_payoff", "evidence_credibility", "platform_native", "cta_comment", "human_voice_originality"} if a.domain == "ai_video" else {"audience_and_task", "entry_and_click_reason", "first_8_seconds", "professional_judgment_and_payoff", "facts_evidence_and_rights", "platform_native_expression", "calling_and_action", "spoken_naturalness"})
        errors.extend(validate_review(batch, review, dims))
    result = {"status": "PASS" if not errors else "BLOCKED", "errors": errors, "script_count": len(batch.get("scripts", [])), "minimum_dimension_score": MIN_DIMENSION_SCORE}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2

if __name__ == "__main__":
    raise SystemExit(main())
