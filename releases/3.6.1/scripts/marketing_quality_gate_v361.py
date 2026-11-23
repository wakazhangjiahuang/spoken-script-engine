#!/usr/bin/env python3
"""v3.6.1 targeted marketing/source-fidelity gate.
Deterministic checks bind source selection, story mode, benchmark transfer and
independent marketing review to actual script text. This gate does not claim to
measure real click-through or conversion; those require external validation.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Any

CONTENT_MODES = {"real_commercial_case", "ai_workflow_tutorial", "design_decision_analysis", "business_opportunity_analysis", "hypothetical_scenario"}
REVIEW_MODES = {"human", "separate_model"}
HOOK_ROLES = {"hook", "opening", "opening_0_3", "0_3", "0–3"}
BRIDGE_ROLES = {"bridge", "suspense", "opening_bridge", "3_8", "3–8"}
BODY_ROLES = {"context", "judgment", "value", "proof", "evidence", "material", "decision", "body"}
CTA_ROLES = {"calling", "cta"}
CAPABILITY_CLAIMS = ("一个人", "个人也能", "小团队", "小白也能", "不用团队", "不需要团队", "替代团队", "节省人力", "省人", "降本", "以前需要多人", "过去需要多人")

def _s(value: Any) -> str:
    return str(value or "").strip()

def _norm(value: Any) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", _s(value)).casefold()

def _similarity(a: Any, b: Any) -> float:
    aa, bb = _norm(a), _norm(b)
    if not aa or not bb:
        return 0.0
    return SequenceMatcher(None, aa, bb, autojunk=False).ratio()

def _items(value: Any) -> list:
    return value if isinstance(value, list) else []

def _plan_rows(decision: dict) -> list[dict]:
    return [x for x in _items(decision.get("selected")) if isinstance(x, dict)]

def _scripts(batch: dict) -> list[dict]:
    return [x for x in _items(batch.get("scripts")) if isinstance(x, dict)]

def _script_id(script: dict) -> str:
    return _s(script.get("script_id") or script.get("id"))

def _plan_id(row: dict) -> str:
    return _s(row.get("id") or row.get("plan_id") or row.get("topic_id"))

def _script_plan_id(script: dict) -> str:
    return _s(script.get("plan_id") or script.get("topic_id") or script.get("id") or script.get("script_id"))

def _segments(script: dict) -> list[dict]:
    return [x for x in _items(script.get("segments")) if isinstance(x, dict)]

def _quote_in_roles(script: dict, quote: Any, roles: set[str]) -> bool:
    q = _s(quote)
    return bool(q) and any(q in _s(seg.get("text")) for seg in _segments(script) if _s(seg.get("role")).lower() in roles)

def _quote_in_cover_or_hook(script: dict, quote: Any) -> bool:
    q = _s(quote)
    if not q:
        return False
    cover = script.get("cover", {}) if isinstance(script.get("cover"), dict) else {}
    cover_text = " ".join([_s(script.get("cover_main")), _s(script.get("cover_sub")), _s(script.get("cover_title")), _s(script.get("cover_subtitle")), _s(cover.get("main")), _s(cover.get("sub")), _s(cover.get("title")), _s(cover.get("subtitle"))])
    return q in cover_text or _quote_in_roles(script, q, HOOK_ROLES)

def _fact_map(brief: dict) -> dict[str, dict]:
    return {_s(x.get("id")): x for x in _items(brief.get("facts")) if isinstance(x, dict) and _s(x.get("id"))}

def _real_project_ids(brief: dict) -> set[str]:
    return {fid for fid, fact in _fact_map(brief).items() if fact.get("evidence_class") == "user_project" and fact.get("status") in {"provided", "verified"}}

def validate_benchmark_catalog(catalog: dict) -> list[str]:
    """Ensure the two positive references stay separate and are not few-shot scripts."""
    errors: list[str] = []
    rows = _items(catalog.get("benchmarks")) if isinstance(catalog, dict) else []
    by_key = {_s(x.get("benchmark_key")): x for x in rows if isinstance(x, dict)}
    expected = {
        "illustration_commercial_case": ("illustration", "commercial_illustration_case", "USER_PROVIDED"),
        "ai_video_marketing_method": ("ai_video", "ai_video_marketing_method", "calibrated_reference_not_performance_verified"),
    }
    for key, (domain, benchmark_type, status) in expected.items():
        row = by_key.get(key)
        if not row:
            errors.append(f"BENCHMARK_CATALOG_MISSING:{key}")
            continue
        bid = _s(row.get("benchmark_id")) or key
        if row.get("domain") != domain:
            errors.append(f"BENCHMARK_DOMAIN_MISMATCH:{bid}")
        if row.get("benchmark_type") != benchmark_type:
            errors.append(f"BENCHMARK_TYPE_MISMATCH:{bid}")
        if row.get("source_status") != status:
            errors.append(f"BENCHMARK_SOURCE_STATUS_MISMATCH:{bid}")
        if row.get("role") != "mechanism_reference_only":
            errors.append(f"BENCHMARK_ROLE_MUST_BE_MECHANISM_ONLY:{bid}")
        if row.get("few_shot_allowed") is not False:
            errors.append(f"BENCHMARK_FEW_SHOT_MUST_BE_DISABLED:{bid}")
        if row.get("score_as_script") is not False:
            errors.append(f"BENCHMARK_MUST_NOT_BE_SCORED_AS_SCRIPT:{bid}")
        if len(_items(row.get("transferable_mechanisms"))) < 3:
            errors.append(f"BENCHMARK_MECHANISMS_INCOMPLETE:{bid}")
        if len(_items(row.get("non_transferable"))) < 2:
            errors.append(f"BENCHMARK_NON_TRANSFERABLE_RULES_MISSING:{bid}")
    if len(by_key) != 2:
        errors.append("BENCHMARK_CATALOG_MUST_CONTAIN_EXACTLY_TWO_CANONICAL_REFERENCES")
    return errors

def validate_source_inventory(brief: dict) -> list[str]:
    """Require intake to record what was inspected before a content mode is chosen."""
    errors: list[str] = []
    inv = brief.get("source_inventory") if isinstance(brief, dict) else None
    if not isinstance(inv, dict):
        return ["SOURCE_INVENTORY_MISSING_BEFORE_PLANNING"]
    status = _s(inv.get("status"))
    if status not in {"complete", "no_source_materials"}:
        errors.append("SOURCE_INVENTORY_STATUS_INVALID")
    checked = _items(inv.get("checked_assets"))
    if status == "complete":
        if not checked:
            errors.append("SOURCE_INVENTORY_COMPLETE_WITHOUT_CHECKED_ASSETS")
        for i, item in enumerate(checked):
            if not isinstance(item, dict) or not _s(item.get("asset_id")) or not _s(item.get("locator")) or not _s(item.get("source_quote")) or item.get("read") is not True:
                errors.append(f"SOURCE_INVENTORY_ASSET_NOT_TRACEABLE:{i}")
    if status == "no_source_materials" and len(_s(inv.get("no_source_reason"))) < 20:
        errors.append("SOURCE_INVENTORY_NO_SOURCE_REASON_MISSING")
    actual_real = _real_project_ids(brief)
    relevant = set(map(_s, _items(inv.get("relevant_real_case_ids"))))
    selected = set(map(_s, _items(inv.get("selected_real_case_ids"))))
    excluded_rows = _items(inv.get("excluded_relevant_source_ids"))
    excluded = {_s(x.get("id")): _s(x.get("reason")) for x in excluded_rows if isinstance(x, dict)}
    if not relevant.issubset(actual_real):
        errors.append("SOURCE_INVENTORY_RELEVANT_CASE_IDS_NOT_IN_FACTS")
    if not selected.issubset(relevant):
        errors.append("SOURCE_INVENTORY_SELECTED_CASE_NOT_RELEVANT_OR_UNKNOWN")
    if not set(excluded).issubset(relevant):
        errors.append("SOURCE_INVENTORY_EXCLUDED_CASE_NOT_RELEVANT_OR_UNKNOWN")
    for fid in relevant:
        if fid not in selected and len(excluded.get(fid, "")) < 12:
            errors.append(f"RELEVANT_REAL_CASE_IGNORED_WITHOUT_REASON:{fid}")
    policy = _s(brief.get("case_policy") or "prefer_real")
    if policy not in {"prefer_real", "real_only", "allow_simulation_if_no_fit", "explicit_simulation"}:
        errors.append("CASE_POLICY_INVALID")
    if policy == "real_only" and relevant and not selected:
        errors.append("REAL_ONLY_POLICY_BUT_NO_REAL_CASE_SELECTED")
    if policy == "explicit_simulation" and brief.get("explicit_simulation_authorized") is not True:
        errors.append("SIMULATION_NOT_EXPLICITLY_AUTHORIZED")
    if policy == "prefer_real" and relevant and not selected and not excluded:
        errors.append("PREFER_REAL_POLICY_IGNORED_AVAILABLE_REAL_CASE")
    if not _s(inv.get("selection_reason")) and status == "complete":
        errors.append("SOURCE_INVENTORY_SELECTION_REASON_MISSING")
    return errors

def _validate_benchmark_reference(row: dict, domain: str, catalog: dict, sid: str) -> list[str]:
    errors: list[str] = []
    ref = row.get("benchmark_reference")
    if not isinstance(ref, dict):
        return [f"{sid}:BENCHMARK_REFERENCE_DECISION_MISSING"]
    if ref.get("used") is not True:
        if len(_s(ref.get("reason"))) < 12:
            errors.append(f"{sid}:BENCHMARK_NONUSE_REASON_MISSING")
        return errors
    bid = _s(ref.get("benchmark_id"))
    item = next((x for x in _items(catalog.get("benchmarks")) if isinstance(x, dict) and bid in {x.get("benchmark_id"), x.get("benchmark_key")}), None)
    if not item:
        return [f"{sid}:BENCHMARK_REFERENCE_UNKNOWN:{bid or 'EMPTY'}"]
    if item.get("domain") != domain:
        errors.append(f"{sid}:CROSS_DOMAIN_BENCHMARK_USE_BLOCKED:{bid}")
    if ref.get("used_as_few_shot") is True:
        errors.append(f"{sid}:BENCHMARK_USED_AS_FEW_SHOT_BLOCKED:{bid}")
    chosen = set(map(_s, _items(ref.get("mechanisms_selected"))))
    allowed = set(map(_s, _items(item.get("transferable_mechanisms"))))
    if not chosen or not chosen.issubset(allowed):
        errors.append(f"{sid}:BENCHMARK_MECHANISM_SELECTION_INVALID:{bid}")
    for key in ("transfer_reason", "new_application", "non_transferable_acknowledged"):
        if len(_s(ref.get(key))) < 12:
            errors.append(f"{sid}:BENCHMARK_TRANSFER_{key.upper()}_MISSING")
    return errors

def validate_plan_marketing(decision: dict, brief: dict, domain: str, catalog: dict) -> list[str]:
    errors = validate_benchmark_catalog(catalog)
    errors.extend(validate_source_inventory(brief))
    selected = _plan_rows(decision)
    if not selected:
        return errors + ["MARKETING_PLAN_SELECTED_MISSING"]
    inv = brief.get("source_inventory", {}) if isinstance(brief.get("source_inventory"), dict) else {}
    relevant_real = set(map(_s, _items(inv.get("relevant_real_case_ids"))))
    selected_real = set(map(_s, _items(inv.get("selected_real_case_ids"))))
    policy = _s(brief.get("case_policy") or "prefer_real")
    for row in selected:
        sid = _plan_id(row) or "UNKNOWN"
        mode = _s(row.get("content_mode"))
        if mode not in CONTENT_MODES:
            errors.append(f"{sid}:CONTENT_MODE_MISSING_OR_INVALID")
        source = row.get("source_selection") if isinstance(row.get("source_selection"), dict) else {}
        selected_ids = set(map(_s, _items(source.get("selected_fact_ids"))))
        facts = _fact_map(brief)
        unknown_ids = selected_ids - set(facts)
        if unknown_ids:
            errors.append(f"{sid}:SOURCE_SELECTION_FACT_IDS_NOT_IN_BRIEF:{','.join(sorted(unknown_ids))}")
        rejected = _items(source.get("rejected_relevant_case_ids"))
        rejected_ids = {_s(x.get("id")): _s(x.get("reason")) for x in rejected if isinstance(x, dict)}
        if relevant_real and policy in {"prefer_real", "real_only"}:
            if not (selected_ids & relevant_real):
                errors.append(f"{sid}:REAL_USER_CASE_NOT_SELECTED")
            if not selected_real.issubset(selected_ids):
                errors.append(f"{sid}:INTAKE_SELECTED_REAL_CASE_DROPPED_IN_PLAN")
            for fid in relevant_real - selected_ids:
                if len(rejected_ids.get(fid, "")) < 12:
                    errors.append(f"{sid}:RELEVANT_REAL_CASE_REJECTED_WITHOUT_REASON:{fid}")
        if mode == "real_commercial_case":
            selected_real_facts = selected_ids & _real_project_ids(brief)
            case_ref = source.get("case_source_ref") if isinstance(source.get("case_source_ref"), dict) else {}
            case_ref_status = _s(case_ref.get("source_status"))
            case_ref_valid = case_ref_status in {"USER_PROVIDED", "VERIFIED"} and all(_s(case_ref.get(k)) for k in ("source_asset_id", "source_locator", "source_quote"))
            if not selected_real_facts and not case_ref_valid:
                errors.append(f"{sid}:REAL_COMMERCIAL_CASE_WITHOUT_USER_PROJECT_SOURCE")
            if source.get("case_mode") == "simulated":
                errors.append(f"{sid}:REAL_COMMERCIAL_CASE_MARKED_SIMULATED")
        if mode == "hypothetical_scenario":
            if policy != "explicit_simulation" and not (policy == "allow_simulation_if_no_fit" and not selected_real and relevant_real.issubset(set(rejected_ids))):
                errors.append(f"{sid}:HYPOTHETICAL_MODE_NOT_AUTHORIZED_OR_REAL_CASE_AVAILABLE")
            if len(_s(source.get("simulation_disclosure"))) < 12:
                errors.append(f"{sid}:SIMULATION_DISCLOSURE_MISSING_IN_PLAN")
        story = row.get("story_plan") if isinstance(row.get("story_plan"), dict) else {}
        required_story = {
            "ai_workflow_tutorial": ("original_input", "ai_process", "human_judgment", "output", "application_value"),
            "real_commercial_case": ("buyer_need", "professional_judgment", "tool_or_method", "product_translation", "result", "transferable_value"),
            "design_decision_analysis": ("product_brief", "design_constraints", "tradeoff", "product_fit", "decision_rule"),
            "business_opportunity_analysis": ("user_opportunity", "market_evidence", "business_logic", "risk_boundary", "action_recommendation"),
            "hypothetical_scenario": ("simulation_disclosure", "assumptions", "decision_path", "illustrative_output", "applicability_boundary"),
        }.get(mode, ())
        for key in required_story:
            if len(_s(story.get(key))) < 10:
                errors.append(f"{sid}:STORY_PLAN_{mode.upper()}_{key.upper()}_MISSING")
        errors.extend(_validate_benchmark_reference(row, domain, catalog, sid))
    return errors

def validate_script_marketing(batch: dict, decision: dict, brief: dict, domain: str, catalog: dict) -> list[str]:
    errors: list[str] = []
    plans = {_plan_id(x): x for x in _plan_rows(decision)}
    resources = {_s(x.get("id")): x for x in _items(brief.get("production_resources")) if isinstance(x, dict)}
    for script in _scripts(batch):
        sid = _script_id(script) or "UNKNOWN"
        plan = plans.get(_script_plan_id(script))
        if not plan:
            errors.append(f"{sid}:MARKETING_PLAN_NOT_FOUND")
            continue
        plan_mode = _s(plan.get("content_mode"))
        mode = _s(script.get("content_mode") or (script.get("professional_decision", {}) or {}).get("content_mode"))
        if mode != plan_mode:
            errors.append(f"{sid}:SCRIPT_CONTENT_MODE_DIFFERS_FROM_APPROVED_PLAN")
        source = plan.get("source_selection") if isinstance(plan.get("source_selection"), dict) else {}
        selected_ids = set(map(_s, _items(source.get("selected_fact_ids"))))
        script_ids = set(map(_s, _items(script.get("source_fact_ids"))))
        if selected_ids and not selected_ids.issubset(script_ids):
            errors.append(f"{sid}:SCRIPT_DROPPED_APPROVED_SOURCE_FACTS")
        pd = script.get("professional_decision") if isinstance(script.get("professional_decision"), dict) else {}
        if mode == "real_commercial_case" and _s(pd.get("case_mode")).lower() in {"simulated", "hypothetical"}:
            errors.append(f"{sid}:REAL_CASE_SILENTLY_REPLACED_WITH_SIMULATION")
        if mode == "hypothetical_scenario":
            disclosure = _s(pd.get("simulation_disclosure"))
            all_speech = "\n".join(_s(x.get("text")) for x in _segments(script))
            if not disclosure or disclosure not in all_speech:
                errors.append(f"{sid}:SIMULATION_NOT_DISCLOSED_IN_SPOKEN_SCRIPT")
        all_speech = "\n".join(_s(x.get("text")) for x in _segments(script))
        if domain == "ai_video" and any(term in all_speech for term in CAPABILITY_CLAIMS):
            proof_ids = set(map(_s, _items(script.get("capability_claim_evidence_ids"))))
            valid = {rid for rid, res in resources.items() if res.get("status") == "available" and res.get("evidence_role") in {"proof", "demonstration"}}
            if not (proof_ids & valid):
                errors.append(f"{sid}:AI_CAPABILITY_AMPLIFICATION_WITHOUT_AVAILABLE_DEMONSTRATION")
    return errors

def validate_marketing_review(batch: dict, decision: dict, review: dict, brief: dict, domain: str) -> list[str]:
    errors: list[str] = []
    scripts = {_script_id(x): x for x in _scripts(batch)}
    plans = {_plan_id(x): x for x in _plan_rows(decision)}
    reviewer = review.get("marketing_reviewer") if isinstance(review, dict) else None
    if not isinstance(reviewer, dict) or reviewer.get("independent") is not True or reviewer.get("same_model_role") is not False or reviewer.get("mode") not in REVIEW_MODES:
        errors.append("MARKETING_REVIEWER_NOT_INDEPENDENT")
    elif not _s(reviewer.get("reviewer_id")) or not _s(reviewer.get("generator_id")):
        errors.append("MARKETING_REVIEWER_IDENTITY_FIELDS_MISSING")
    elif _s(reviewer.get("reviewer_id")) == _s(reviewer.get("generator_id")):
        errors.append("MARKETING_REVIEWER_ID_EQUALS_GENERATOR")
    checks = _items(review.get("marketing_checks")) if isinstance(review, dict) else []
    if {_s(x.get("script_id")) for x in checks if isinstance(x, dict)} != set(scripts):
        return errors + ["MARKETING_REVIEW_ITEMS_DO_NOT_MATCH_BATCH"]
    for item in checks:
        sid = _s(item.get("script_id"))
        script = scripts[sid]
        plan = plans.get(_script_plan_id(script), {})
        mode = _s(plan.get("content_mode"))
        relevance = item.get("user_relevance", {})
        if relevance.get("passed") is not True or len(_s(relevance.get("reason"))) < 20 or not _quote_in_roles(script, relevance.get("quote"), HOOK_ROLES | BRIDGE_ROLES):
            errors.append(f"{sid}:USER_RELEVANCE_REVIEW_FAILED_OR_UNANCHORED")
        click = item.get("click_chain", {})
        if click.get("passed") is not True or len(_s(click.get("reason"))) < 20:
            errors.append(f"{sid}:CLICK_CHAIN_REVIEW_FAILED")
        if not _quote_in_roles(script, click.get("hook_quote"), HOOK_ROLES):
            errors.append(f"{sid}:CLICK_CHAIN_HOOK_QUOTE_NOT_IN_SCRIPT")
        if not _quote_in_roles(script, click.get("bridge_quote"), BRIDGE_ROLES) or not _quote_in_roles(script, click.get("new_information_quote"), BRIDGE_ROLES):
            errors.append(f"{sid}:CLICK_CHAIN_BRIDGE_OR_NEW_INFO_NOT_IN_SCRIPT")
        payoff = item.get("promise_payoff", {})
        if payoff.get("passed") is not True or len(_s(payoff.get("reason"))) < 20:
            errors.append(f"{sid}:PROMISE_PAYOFF_REVIEW_FAILED")
        if not _quote_in_cover_or_hook(script, payoff.get("promise_quote")) or not _quote_in_roles(script, payoff.get("payoff_quote"), BODY_ROLES):
            errors.append(f"{sid}:PROMISE_PAYOFF_QUOTES_NOT_BOUND_TO_SCRIPT")
        mode_check = item.get("content_mode_fit", {})
        if mode_check.get("passed") is not True or _s(mode_check.get("mode")) != mode or len(_s(mode_check.get("reason"))) < 20 or not _quote_in_roles(script, mode_check.get("evidence_quote"), BODY_ROLES):
            errors.append(f"{sid}:CONTENT_MODE_FIT_REVIEW_FAILED")
        capability = item.get("capability_amplification", {})
        if capability.get("applicable") is True:
            resources = {_s(x.get("id")): x for x in _items(brief.get("production_resources")) if isinstance(x, dict)}
            resource = resources.get(_s(capability.get("evidence_ref")), {})
            if capability.get("passed") is not True or not _quote_in_roles(script, capability.get("quote"), BODY_ROLES) or len(_s(capability.get("human_ai_boundary"))) < 12 or resource.get("status") != "available" or resource.get("evidence_role") not in {"proof", "demonstration"}:
                errors.append(f"{sid}:CAPABILITY_AMPLIFICATION_UNPROVEN")
        elif len(_s(capability.get("reason"))) < 20:
            errors.append(f"{sid}:CAPABILITY_AMPLIFICATION_APPLICABILITY_NOT_EXPLAINED")
        next_value = item.get("next_level_value", {})
        cta_quote = _s(next_value.get("quote"))
        if next_value.get("passed") is not True or len(_s(next_value.get("next_need"))) < 12 or len(_s(next_value.get("reason"))) < 20 or not _quote_in_roles(script, cta_quote, CTA_ROLES):
            errors.append(f"{sid}:NEXT_LEVEL_VALUE_NOT_SPOKEN_OR_REVIEWED")
        promised = _s((plan.get("content_contract") or plan.get("expression_contract") or {}).get("promised_payoff"))
        if promised and _similarity(promised, next_value.get("next_need")) > 0.82:
            errors.append(f"{sid}:NEXT_LEVEL_VALUE_REPEATS_CURRENT_PAYOFF")
        source_check = item.get("source_fidelity", {})
        expected_source_ids = set(map(_s, _items((plan.get("source_selection") or {}).get("selected_fact_ids"))))
        used_source_ids = set(map(_s, _items(source_check.get("used_fact_ids"))))
        if source_check.get("passed") is not True or len(_s(source_check.get("reason"))) < 20 or not expected_source_ids.issubset(used_source_ids):
            errors.append(f"{sid}:SOURCE_FIDELITY_REVIEW_FAILED")
        ignored = _items(source_check.get("ignored_relevant_sources"))
        if any(not isinstance(x, dict) or len(_s(x.get("reason"))) < 12 for x in ignored):
            errors.append(f"{sid}:IGNORED_RELEVANT_SOURCE_WITHOUT_REASON")
    return errors

def release_validation_status(review: dict) -> str:
    """External validation remains pending until evidence exists; model review is not market proof."""
    ext = review.get("external_validation", {}) if isinstance(review, dict) else {}
    required = ("human_voice_test", "target_user_blind_read", "rights_and_permissions", "platform_outcome")
    return "PASS" if all(ext.get(k) == "PASSED" for k in required) else "VALIDATION_PENDING"
