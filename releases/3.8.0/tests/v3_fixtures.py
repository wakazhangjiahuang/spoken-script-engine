"""Synthetic inputs for deterministic regression, never marketing evidence."""
from decision_v3 import DIMENSIONS
from execution_contract import canonical


def context(adapter="shared"):
    return {"run_id": "regression", "execution_mode": "proposal", "offer": "Synthetic design task",
            "commercial_goal": "education",
            "route": {"primary_adapter_id": adapter, "adapter_version": "1.0.0",
                      "business_model": "B2B", "route_reason": "Scope of this synthetic fixture",
                      "overlay_adapter_ids": [], "route_confidence": "verified"},
            "knowledge": {"status": "KB_NOT_CONFIGURED", "reason": "Synthetic fixture without remote credentials"}}


def populate(topic, source):
    body = topic["copy"]["body"]
    ref = ["E01"]
    benefit = topic["payoff"]
    topic["decision_v3"] = {
        "as_of": "2026-11-27",
        "customer": {"audience_id": "buyers", "decision_id": "decide-" + topic["id"],
                     "buyer_role": "Product approver", "context": "Before sample approval",
                     "current_task": topic["buyer_decision"], "root_need": "Avoid printing the wrong size",
                     "trigger": "Artwork ready for sample production", "alternative": "Use prior artwork",
                     "barrier": "A single mock-up hides scale differences", "decision_criterion": "Scale",
                     "benefit": benefit, "evidence_refs": ref},
        "evidence": [{"id": "E01", "source_id": source["asset_id"], "locator": source["locator"],
                      "sha256": source["source_sha256"], "scope": "This program fixture",
                      "rights": "authorized", "status": "USER_PROVIDED", "kind": "attribute",
                      "supported_statement": body, "claim_limit": "No real client or outcome",
                      "source_date": "2026-11-27"}],
        "category": {"option": "Two artwork treatments", "alternative": "Repeat previous season",
                     "reason": "Allows a scale check", "tradeoff": "Work for two treatments"},
        "purchase": {"id": "P01", "status": "INFO_ONLY", "reason": "Teach a method from the fixture",
                     "content_type": "education", "proof_refs": ref, "claim_limit": "Demonstration",
                     "counter_evidence": "No supplier comparison"},
        "value_map": {"feature": "Two scale treatments", "capability": "Compare scale",
                      "capability_scope": "On this sample", "difference_or_fit": "Same artwork at two scales",
                      "benefit": benefit, "purchase_reason_id": "P01", "entry_id": "1",
                      "platform_task": "Choose what to review before approving a sample",
                      "expression": topic["copy"]["cover_main"], "claim_limit": "No sales claim", "proof_refs": ref},
        "claims": [{"id": "C01", "text": body, "type": "fact", "scope": "Sample only", "proof_refs": ref}],
        "entries": [
            {"id": id_, "angle": angle, "question": q, "benefit": b, "payoff": pay,
             "candidate_copy": copy, "rationale": reason, "proof_refs": proofs,
             "scores": {key: score for key in DIMENSIONS}}
            for id_, angle, q, b, pay, copy, reason, score, proofs in [
                ("1", "decision", topic["buyer_decision"], benefit, benefit, topic["copy"]["cover_main"],
                 "Tied to sample approval and shown on the artwork", 4, ref),
                ("2", "risk", "What happens after cutting?", "Spot clipping", "Inspect seam overlay",
                 "The motif may vanish at the seam", "No cut sample supplied", 2, []),
                ("3", "efficiency", "Can the existing SKU transfer?", "Reuse an approved motif",
                 "Check old product sizes", "Reuse test for an old motif", "Old SKU measurements absent", 1, []),
            ]],
        "promise": benefit, "content_goal": "education", "calling_action": topic["next_step"],
        "calling_reason": "Use your real sample brief", "calling_reward": "Identify what to compare",
        "comment_task": "Identify the next sample to approve", "risk": "No actual outcomes supplied",
        "platform_difference": "Search-friendly question for product approvers", "series_id": "S1",
        "topic_type": "worked_comparison", "presentation_form": "talking_head",
        "narrative_mode": "design_decision_analysis", "funnel_stage": "discovery", "unique_payoff": benefit,
    }
    return topic


def script_for(topic):
    copy, record = topic["copy"], topic["decision_v3"]
    return {"id": "S" + topic["id"], "plan_id": topic["id"], "platform": topic["platform"],
            "audience": topic["audience"], "cover_main": copy["cover_main"], "cover_sub": copy["cover_sub"],
            "v3_handoff_sha256": canonical(record), "v3_content_entry": topic["buyer_decision"],
            "content_mode": record["narrative_mode"], "selected_entry_candidate_id": record["value_map"]["entry_id"],
            "segments": [{"role": role, "text": copy[col]} for role, col in
                         (("hook", "hook"), ("suspense", "suspense"), ("value", "body"), ("calling", "calling"))],
            "comment_hook": {"line": copy["comment"]},
            "v3_claims": [{"claim_id": "C01", "field": "body", "quote": copy["body"]}]}
