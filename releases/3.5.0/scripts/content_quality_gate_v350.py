#!/usr/bin/env python3
"""v3.5.0 content-payoff gate.

Adds non-compensatory checks for a concrete worked example, observable change,
source-bound audience task, first-eight progression and CTA value exchange.
It deliberately reuses the current V4.1 / illustration V2.0 audience assets.
"""
from __future__ import annotations
import re
from typing import Any

AI_CRITICAL = {"audience_need", "cover_click_reason", "opening_bridge", "body_payoff", "cta_comment"}
ILL_CRITICAL = {"audience_and_task", "entry_and_click_reason", "first_8_seconds", "professional_judgment_and_payoff", "calling_and_action"}
BODY_ROLES = {"context", "judgment", "value", "proof", "evidence", "material", "decision", "body"}
HOOK_ROLES = {"hook", "opening", "opening_0_3", "0_3", "0–3"}
BRIDGE_ROLES = {"bridge", "suspense", "opening_bridge", "3_8", "3–8"}
CTA_ROLES = {"calling", "cta"}
GENERIC_TASKS = ("了解ai", "了解相关信息", "学习方法", "判断是否适合", "提高效率", "做出专业结果", "看看怎么做", "了解怎么做")
GENERIC_REWARDS = {"关注我", "点赞", "评论", "收藏", "私信我", "支持我", "关注账号"}


def _s(v: Any) -> str:
    return str(v or "").strip()


def _norm(s: Any) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", _s(s)).casefold()


def _ngrams(s: Any) -> set[str]:
    t = _norm(s)
    if len(t) < 3:
        return {t} if t else set()
    return {t[i:i+2] for i in range(len(t)-1)}


def _similarity(a: Any, b: Any) -> float:
    aa, bb = _ngrams(a), _ngrams(b)
    return len(aa & bb) / max(1, len(aa | bb))


def _pick(d: dict, *keys: str, default=None):
    for key in keys:
        if key in d and d.get(key) not in (None, "", [], {}):
            return d.get(key)
    return default


def _contract(row: dict) -> dict:
    for key in ("content_contract", "expression_contract", "information_contract"):
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _need_ref(row: dict) -> dict:
    c = _contract(row)
    pd = row.get("professional_decision", {}) if isinstance(row.get("professional_decision"), dict) else {}
    return _pick(row, "audience_need_ref", default=_pick(c, "audience_need_ref", default=pd.get("audience_need_ref", {}))) or {}


def _locator_matches(locator: str, source_text: str) -> bool:
    parts = [x.strip() for x in re.split(r"[>/／|#]+", locator) if len(x.strip()) >= 2]
    return bool(parts) and any(x in source_text for x in parts)


def _need_errors(ref: dict, registry: dict, domain: str, sid: str) -> list[str]:
    errors = []
    if not isinstance(ref, dict):
        return [f"{sid}:AUDIENCE_NEED_REF_MISSING"]
    aid, locator, quote = (_s(ref.get(k)) for k in ("source_asset_id", "source_locator", "source_quote"))
    if not aid or aid not in registry:
        return [f"{sid}:AUDIENCE_NEED_SOURCE_ASSET_NOT_LOADED:{aid or 'EMPTY'}"]
    source_text = _s(registry[aid].get("text")) if isinstance(registry[aid], dict) else _s(registry[aid])
    if len(quote) < 8 or quote not in source_text:
        errors.append(f"{sid}:AUDIENCE_NEED_QUOTE_NOT_VERBATIM")
    if len(locator) < 3 or not _locator_matches(locator, source_text):
        errors.append(f"{sid}:AUDIENCE_NEED_LOCATOR_NOT_IN_SOURCE")
    d = domain.lower().replace("-", "_")
    if d in {"illustration", "print_design", "illustration_surface_pattern_textile_print", "design_service"} and aid != "ILLUSTRATION-GUIDANCE-V2.0":
        errors.append(f"{sid}:ILLUSTRATION_NEED_MUST_BIND_TO_V2_GUIDANCE")
    if d in {"ai_video", "ai_video_business", "aivideo", "ai视频", "ai视频业务"} and aid != "AI-VIDEO-BUSINESS-GUIDE-V4.1":
        errors.append(f"{sid}:AI_VIDEO_NEED_MUST_BIND_TO_V4_1_GUIDE")
    return errors


def _candidate_fields(c: dict) -> tuple[str, str, str, str, str]:
    cid = _s(_pick(c, "id", "candidate_id", "entry_id"))
    kind = _s(_pick(c, "entry_type", "mechanism", "hook_type", "angle_type"))
    reason = _s(_pick(c, "click_reason", "viewer_click_reason"))
    payoff = _s(_pick(c, "payoff", "user_payoff", "promised_payoff"))
    proof = _pick(c, "proof_plan", "proof", "evidence_plan", default=[])
    proof_text = " ".join(map(_s, proof)) if isinstance(proof, list) else _s(proof)
    return cid, kind, reason, payoff, proof_text


def _contract_values(c: dict, row: dict) -> dict:
    return {
        "target_audience": _pick(c, "target_audience", "audience_voice", "Audience_Voice", "audience", default=row.get("audience")),
        "shared_task": _pick(c, "shared_task", "viewer_task", "Viewer_Task", default=row.get("viewer_task")),
        "shared_task_reason": _pick(c, "shared_task_reason", "task_reason", "audience_task_link"),
        "why_now": _pick(c, "why_now", "current_situation", "current_belief", "Current_Belief", "core_tension", "Core_Tension"),
        "click_reason": _pick(c, "click_reason", "chosen_click_reason", "Chosen_Click_Reason"),
        "promised_payoff": _pick(c, "promised_payoff", "promise_and_payoff", "Promise_Proof", "desired_outcome", "Desired_Outcome"),
        "proof_plan": _pick(c, "proof_plan", "Promise_Proof", default=row.get("proof_plan")),
        "decision_criteria": _pick(c, "buyer_decision_criteria", "decision_criteria", "illustration_judgement", "Illustration_Judgment", "professional_judgment"),
        "transferable_value": _pick(c, "transferable_value", "Transferable_Value"),
        "next_value": _pick(c, "next_value", "Next_Value"),
        "entry_competition": _pick(c, "entry_competition", "Entry_Competition", "candidate_competition", default=[]),
        "selected_entry_id": _pick(c, "selected_entry_id", "selected_angle_id", "selected_candidate_id"),
        "selection_reason": _pick(c, "selection_reason", "selection_rationale"),
        "counterargument": _pick(c, "counterargument", "main_counterargument", "counter_argument"),
        "counterevidence": _pick(c, "counterevidence", "counter_evidence"),
    }


def _validate_entry_competition(candidates: Any, selected_id: Any, sid: str) -> list[str]:
    errors = []
    if isinstance(candidates, dict):
        candidates = candidates.get("candidates", [])
    if not isinstance(candidates, list) or len(candidates) < 3:
        return [f"{sid}:THREE_MARKETING_ENTRIES_REQUIRED"]
    rows = [_candidate_fields(x) for x in candidates if isinstance(x, dict)]
    if len(rows) < 3:
        return [f"{sid}:THREE_VALID_MARKETING_ENTRIES_REQUIRED"]
    ids = [x[0] for x in rows]
    kinds = [x[1] for x in rows]
    reasons = [x[2] for x in rows]
    payoffs = [x[3] for x in rows]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        errors.append(f"{sid}:ENTRY_IDS_MISSING_OR_DUPLICATED")
    if sum(bool(x) for x in kinds) < 3 or len({_norm(x) for x in kinds if x}) < 2:
        errors.append(f"{sid}:ENTRY_MECHANISMS_NOT_DISTINCT")
    if len({_norm(x) for x in reasons if x}) < 3 or len({_norm(x) for x in payoffs if x}) < 3:
        errors.append(f"{sid}:ENTRY_CLICK_REASONS_OR_PAYOFFS_NOT_DISTINCT")
    for cid, kind, reason, payoff, proof in rows:
        if len(reason) < 10 or len(payoff) < 10 or len(proof) < 8:
            errors.append(f"{sid}:ENTRY_CANDIDATE_INCOMPLETE:{cid or 'UNKNOWN'}")
    if _s(selected_id) not in ids:
        errors.append(f"{sid}:SELECTED_ENTRY_NOT_IN_CANDIDATES")
    return errors


def validate_plan_quality(decision: dict, registry: dict, domain: str) -> list[str]:
    errors = []
    selected = decision.get("selected", []) if isinstance(decision, dict) else []
    if not isinstance(selected, list) or not selected:
        return ["PLAN_SELECTED_MISSING"]
    for row in selected:
        if not isinstance(row, dict):
            errors.append("PLAN_ROW_INVALID")
            continue
        sid = _s(_pick(row, "id", "plan_id", "topic_id", default="UNKNOWN"))
        c = _contract(row)
        values = _contract_values(c, row)
        errors.extend(_need_errors(_need_ref(row), registry, domain, sid))
        required = ("target_audience", "shared_task", "why_now", "click_reason", "promised_payoff", "proof_plan", "decision_criteria", "transferable_value", "next_value", "selection_reason", "counterargument", "counterevidence")
        for key in required:
            value = values.get(key)
            if isinstance(value, list):
                value = " ".join(map(_s, value))
            if len(_s(value)) < (8 if key in ("target_audience", "shared_task") else 12):
                errors.append(f"{sid}:CONTENT_CONTRACT_{key.upper()}_MISSING_OR_THIN")
        task = _s(values.get("shared_task"))
        if any(x in task.lower() for x in GENERIC_TASKS) and len(_s(_pick(c, "task_output", "deliverable", "concrete_output"))) < 8:
            errors.append(f"{sid}:VIEWER_TASK_IS_ABSTRACT_WITHOUT_DELIVERABLE")
        audience = _s(values.get("target_audience"))
        if audience.count("、") >= 2 and len(_s(values.get("shared_task_reason"))) < 12:
            errors.append(f"{sid}:MULTI_ROLE_AUDIENCE_WITHOUT_SHARED_TASK_JUSTIFICATION")
        proof = values.get("proof_plan")
        proof_items = proof if isinstance(proof, list) else [proof]
        if not any(len(_s(x)) >= 10 for x in proof_items):
            errors.append(f"{sid}:PROOF_PLAN_NOT_CONCRETE")
        errors.extend(_validate_entry_competition(values.get("entry_competition"), values.get("selected_entry_id"), sid))
    return errors


def _segments(script: dict) -> list[dict]:
    return script.get("segments", []) if isinstance(script.get("segments"), list) else []


def _find_segment(script: dict, seg_id: Any) -> dict | None:
    return next((x for x in _segments(script) if _s(x.get("id")) == _s(seg_id)), None)


def _segment_by_role(script: dict, roles: set[str]) -> dict | None:
    return next((x for x in _segments(script) if _s(x.get("role")).lower() in roles), None)


def _anchor(script: dict, item: Any, allowed_roles: set[str], label: str, sid: str) -> list[str]:
    if not isinstance(item, dict):
        return [f"{sid}:{label}_ANCHOR_MISSING"]
    seg = _find_segment(script, item.get("segment_id"))
    quote = _s(item.get("quote"))
    if not seg or len(quote) < 8 or quote not in _s(seg.get("text")):
        return [f"{sid}:{label}_ANCHOR_NOT_VERBATIM"]
    if _s(seg.get("role")).lower() not in allowed_roles:
        return [f"{sid}:{label}_ANCHOR_WRONG_ROLE"]
    return []


def _get_cover(script: dict, main: bool) -> str:
    key = "main" if main else "sub"
    direct = _pick(script, "cover_main" if main else "cover_sub", "cover_title" if main else "cover_subtitle")
    if direct:
        return _s(direct)
    cover = script.get("cover", {})
    if isinstance(cover, dict):
        return _s(_pick(cover, key, "title" if main else "subtitle"))
    return ""


def _validate_worked_example(script: dict, pd: dict, sid: str) -> list[str]:
    errors = []
    example = pd.get("worked_example") if isinstance(pd.get("worked_example"), dict) else {}
    required = ("input_snapshot", "decision_criterion", "before_state", "after_state", "observable_delta", "transfer_rule")
    for key in required:
        if len(_s(example.get(key))) < 12:
            errors.append(f"{sid}:WORKED_EXAMPLE_{key.upper()}_MISSING_OR_THIN")
    before, after = _s(example.get("before_state")), _s(example.get("after_state"))
    if before and after and _similarity(before, after) > 0.78:
        errors.append(f"{sid}:WORKED_EXAMPLE_BEFORE_AFTER_NOT_DISTINCT")
    if any(x in _s(example.get("observable_delta")) for x in ("更好", "更专业", "提升质量", "效果更好", "更有价值")):
        errors.append(f"{sid}:WORKED_EXAMPLE_DELTA_IS_VAGUE")
    for key, roles in (("spoken_anchor", BODY_ROLES), ("result_anchor", BODY_ROLES), ("transfer_anchor", BODY_ROLES)):
        errors.extend(_anchor(script, example.get(key), roles, "WORKED_EXAMPLE_" + key.replace("_anchor", "").upper(), sid))
    chosen = _s(pd.get("chosen_option"))
    spoken = _s((example.get("spoken_anchor") or {}).get("quote")) if isinstance(example.get("spoken_anchor"), dict) else ""
    if chosen and spoken and _similarity(chosen, spoken) < 0.18:
        errors.append(f"{sid}:WORKED_EXAMPLE_DOES_NOT_SAY_WHAT_WAS_CHOSEN")
    delta = _s(example.get("observable_delta"))
    result_quote = _s((example.get("result_anchor") or {}).get("quote")) if isinstance(example.get("result_anchor"), dict) else ""
    if delta and result_quote and _similarity(delta, result_quote) < 0.12:
        errors.append(f"{sid}:WORKED_EXAMPLE_RESULT_NOT_SPOKEN")
    transfer = _s(example.get("transfer_rule"))
    transfer_quote = _s((example.get("transfer_anchor") or {}).get("quote")) if isinstance(example.get("transfer_anchor"), dict) else ""
    if transfer and transfer_quote and _similarity(transfer, transfer_quote) < 0.12:
        errors.append(f"{sid}:TRANSFER_RULE_NOT_SPOKEN")
    body_text = "\n".join(_s(x.get("text")) for x in _segments(script) if _s(x.get("role")).lower() in BODY_ROLES)
    if _s(example.get("input_snapshot")) and _similarity(example.get("input_snapshot"), body_text) < 0.08:
        errors.append(f"{sid}:WORKED_EXAMPLE_INPUT_NOT_USED_IN_BODY")
    return errors


def _validate_calling(script: dict, sid: str) -> list[str]:
    errors = []
    item = script.get("calling_value_exchange")
    if not isinstance(item, dict):
        return [f"{sid}:CALLING_VALUE_EXCHANGE_MISSING"]
    action, reason, reward = (_s(item.get(k)) for k in ("action", "reason", "reward"))
    if len(action) < 5 or len(reason) < 10 or len(reward) < 12:
        errors.append(f"{sid}:CALLING_VALUE_EXCHANGE_INCOMPLETE")
    if any(x in action for x in ("并且", "同时", "然后", "+")):
        errors.append(f"{sid}:CALLING_HAS_MULTIPLE_ACTIONS")
    if _norm(reward) in {_norm(x) for x in GENERIC_REWARDS}:
        errors.append(f"{sid}:CALLING_REWARD_IS_ONLY_ENGAGEMENT_REQUEST")
    seg = _find_segment(script, item.get("segment_id"))
    quote = _s(item.get("quote"))
    if not seg or _s(seg.get("role")).lower() not in CTA_ROLES or len(quote) < 12 or quote not in _s(seg.get("text")):
        errors.append(f"{sid}:CALLING_VALUE_EXCHANGE_NOT_SPOKEN")
    elif _similarity(action, quote) < 0.08 or _similarity(reward, quote) < 0.08:
        errors.append(f"{sid}:CALLING_QUOTE_DOES_NOT_CONTAIN_ACTION_AND_REWARD")
    return errors


def validate_script_quality(script: dict, plan: dict | None, registry: dict, domain: str) -> list[str]:
    sid = _s(_pick(script, "script_id", "id", default="UNKNOWN"))
    errors = []
    c = _contract(script)
    if not c:
        errors.append(f"{sid}:CONTENT_CONTRACT_MISSING")
    else:
        vals = _contract_values(c, script)
        for key in ("target_audience", "shared_task", "click_reason", "promised_payoff", "proof_plan"):
            val = vals.get(key)
            if len(_s(val)) < 8:
                errors.append(f"{sid}:SCRIPT_CONTENT_CONTRACT_{key.upper()}_MISSING")
    ref = _need_ref(script)
    errors.extend(_need_errors(ref, registry, domain, sid))
    pd = script.get("professional_decision") if isinstance(script.get("professional_decision"), dict) else {}
    if not pd:
        errors.append(f"{sid}:PROFESSIONAL_DECISION_MISSING")
    else:
        if plan:
            plan_ref = _need_ref(plan)
            if ref != plan_ref:
                errors.append(f"{sid}:SCRIPT_NEED_REF_DIFFERS_FROM_PLAN")
        if _s(pd.get("viewer_task")) != _s(_pick(c, "shared_task", "viewer_task", "Viewer_Task", default=script.get("viewer_task"))):
            errors.append(f"{sid}:PROFESSIONAL_DECISION_TASK_NOT_ALIGNED")
        errors.extend(_validate_worked_example(script, pd, sid))
    main, sub = _get_cover(script, True), _get_cover(script, False)
    if len(main) < 4 or len(sub) < 4:
        errors.append(f"{sid}:COVER_MAIN_SUBTITLE_MISSING")
    progression = script.get("first_8_progression") if isinstance(script.get("first_8_progression"), dict) else {}
    hook = _find_segment(script, progression.get("hook_segment_id")) if progression else _segment_by_role(script, HOOK_ROLES)
    bridge = _find_segment(script, progression.get("bridge_segment_id")) if progression else _segment_by_role(script, BRIDGE_ROLES)
    if not progression:
        errors.append(f"{sid}:FIRST_8_PROGRESSION_CONTRACT_MISSING")
    if not hook or _s(hook.get("role")).lower() not in HOOK_ROLES:
        errors.append(f"{sid}:HOOK_0_3_SEGMENT_MISSING")
    if not bridge or _s(bridge.get("role")).lower() not in BRIDGE_ROLES:
        errors.append(f"{sid}:BRIDGE_3_8_SEGMENT_MISSING")
    if hook and bridge:
        ht, bt = _s(hook.get("text")), _s(bridge.get("text"))
        if _similarity(ht, bt) > 0.78:
            errors.append(f"{sid}:FIRST_8_BRIDGE_REPEATS_HOOK")
        new_info = _s(progression.get("bridge_new_information"))
        if len(new_info) < 8 or new_info not in bt:
            errors.append(f"{sid}:BRIDGE_ADDS_NO_VERIFIABLE_NEW_INFORMATION")
        if len(_s(progression.get("reason_to_continue"))) < 10:
            errors.append(f"{sid}:REASON_TO_CONTINUE_MISSING")
    payoff_anchor = c.get("body_payoff_anchor") or script.get("body_payoff_anchor")
    errors.extend(_anchor(script, payoff_anchor, BODY_ROLES, "BODY_PAYOFF", sid))
    if isinstance(payoff_anchor, dict):
        payoff_quote = _s(payoff_anchor.get("quote"))
        promise = _s(_pick(c, "promised_payoff", "promise_and_payoff", "Promise_Proof", "desired_outcome"))
        if promise and payoff_quote and _similarity(promise, payoff_quote) < 0.08:
            errors.append(f"{sid}:BODY_DOES_NOT_ANCHOR_PROMISED_PAYOFF")
    errors.extend(_validate_calling(script, sid))
    if plan:
        pc = _contract(plan)
        pv = _contract_values(pc, plan)
        sv = _contract_values(c, script)
        for key in ("shared_task", "click_reason", "promised_payoff"):
            if _s(pv.get(key)) != _s(sv.get(key)):
                errors.append(f"{sid}:SCRIPT_CONTENT_CONTRACT_DIFFERS_FROM_PLAN:{key}")
    return errors


def validate_batch_quality(batch: dict, decision: dict, registry: dict, domain: str) -> list[str]:
    scripts = batch.get("scripts", []) if isinstance(batch, dict) else []
    if not isinstance(scripts, list) or not scripts:
        return ["BATCH_SCRIPTS_MISSING"]
    selected = decision.get("selected", []) if isinstance(decision, dict) else []
    by_id = {}
    for row in selected if isinstance(selected, list) else []:
        if isinstance(row, dict):
            for key in ("id", "plan_id", "topic_id"):
                if row.get(key):
                    by_id[_s(row[key])] = row
    errors = []
    for script in scripts:
        sid = _s(_pick(script, "script_id", "id", default="UNKNOWN"))
        key = _s(_pick(script, "plan_id", "topic_id", "id", default=sid))
        plan = by_id.get(key) or by_id.get(sid)
        if not plan:
            errors.append(f"{sid}:APPROVED_PLAN_ROW_NOT_FOUND")
        errors.extend(validate_script_quality(script, plan, registry, domain))
    return errors


def _review_item_checks(script: dict, item: dict, domain: str, sid: str) -> list[str]:
    errors = []
    pd = script.get("professional_decision", {}) if isinstance(script.get("professional_decision"), dict) else {}
    example = pd.get("worked_example", {}) if isinstance(pd.get("worked_example"), dict) else {}
    calling = script.get("calling_value_exchange", {}) if isinstance(script.get("calling_value_exchange"), dict) else {}
    checks = (
        ("worked_example_review", _s((example.get("result_anchor") or {}).get("quote")), "WORKED_EXAMPLE"),
        ("calling_value_review", _s(calling.get("quote")), "CALLING_VALUE"),
        ("click_chain_review", _s((script.get("first_8_progression") or {}).get("bridge_new_information")), "CLICK_CHAIN"),
    )
    for key, expected_quote, label in checks:
        review = item.get(key, {})
        if review.get("passed") is not True or len(_s(review.get("reason"))) < 20:
            errors.append(f"{sid}:{label}_REVIEW_NOT_PASSED_WITH_REASON")
        if not expected_quote or _s(review.get("quote")) != expected_quote:
            errors.append(f"{sid}:{label}_REVIEW_QUOTE_NOT_BOUND_TO_SCRIPT")
    for key in ("input_is_specific", "criterion_applied", "before_after_observable", "transferable_rule"):
        if item.get("worked_example_review", {}).get(key) is not True:
            errors.append(f"{sid}:WORKED_EXAMPLE_REVIEW_FAILED:{key}")
    for key in ("target_user_recognizes_value", "promise_is_specific", "body_fulfills_promise"):
        if item.get("click_chain_review", {}).get(key) is not True:
            errors.append(f"{sid}:CLICK_CHAIN_REVIEW_FAILED:{key}")
    for key in ("one_primary_action", "user_reward_is_clear", "not_engagement_only"):
        if item.get("calling_value_review", {}).get(key) is not True:
            errors.append(f"{sid}:CALLING_VALUE_REVIEW_FAILED:{key}")

    scores = item.get("scorecard", {}) if domain == "ai_video" else item.get("scores", {})
    critical = AI_CRITICAL if domain == "ai_video" else ILL_CRITICAL
    if not isinstance(scores, dict):
        return errors + [f"{sid}:QUALITY_SCORECARD_MISSING"]
    for dim, entry in scores.items():
        score = entry.get("score") if isinstance(entry, dict) else None
        floor = 4 if dim in critical else 3
        if type(score) is not int or score < floor or score > 5:
            errors.append(f"{sid}:NONCOMPENSATORY_DIMENSION_FLOOR_FAILED:{dim}:MIN_{floor}")
    return errors


def validate_review_quality(batch: dict, review: dict, domain: str) -> list[str]:
    scripts = {_s(_pick(x, "script_id", "id")): x for x in batch.get("scripts", [])}
    items = review.get("items", []) if isinstance(review, dict) else []
    if {_s(x.get("script_id")) for x in items if isinstance(x, dict)} != set(scripts):
        return ["CONTENT_REVIEW_ITEMS_DO_NOT_MATCH_BATCH"]
    errors = []
    for item in items:
        sid = _s(item.get("script_id"))
        errors.extend(_review_item_checks(scripts[sid], item, domain, sid))
    if domain == "illustration":
        reviewer = review.get("reviewer", {})
        if reviewer.get("independent") is not True or reviewer.get("same_model_role") is not False or reviewer.get("mode") not in ("human", "separate_model"):
            errors.append("ILLUSTRATION_REVIEW_NOT_INDEPENDENT")
    return errors


def validate_negative_fixture(record: dict, registry: dict | None = None) -> list[str]:
    """Turn a stored negative regression record into a minimal script and verify it is blocked."""
    sid = _s(record.get("script_id") or "NEGATIVE")
    script = {
        "script_id": sid,
        "audience": record.get("audience", ""),
        "viewer_task": record.get("viewer_task", ""),
        "cover_main": record.get("cover_main", record.get("cover", "")),
        "cover_sub": record.get("cover_sub", ""),
        "segments": record.get("segments", []),
    }
    errors = validate_script_quality(script, None, registry or {}, _s(record.get("domain")))
    # The regression is meaningful only if the missing substantive contract is detected.
    required = {"CONTENT_CONTRACT_MISSING", "PROFESSIONAL_DECISION_MISSING", "CALLING_VALUE_EXCHANGE_MISSING"}
    present = {x.split(":", 1)[-1].split(":", 1)[0] for x in errors}
    if not required.issubset(present):
        errors.append(f"{sid}:NEGATIVE_REGRESSION_NOT_CAUGHT_BY_CORE_GATES")
    return errors
