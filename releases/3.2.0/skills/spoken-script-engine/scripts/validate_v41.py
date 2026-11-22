#!/usr/bin/env python3
"""V4.1 AI-video per-script quality gate. Deterministic contract checks only; it does not judge persuasion or performance."""
from __future__ import annotations
import argparse, hashlib, json, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = ROOT / "assets/ai-video/v4.1/quality-rubric.json"
RUBRIC = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
DIMENSIONS = {x["id"]: x for x in RUBRIC["dimensions"]}
GATES = [x["id"] for x in RUBRIC["hard_gates"]]
INDEPENDENT_LEVELS = {"separate_model", "human"}
REVIEW_ROLES = ("fast_screen", "deep_review", "critic")


def _norm(s: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]", "", str(s)).casefold()


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _script_text(script):
    return "\n".join(_strings(script))


def _get_path(obj, path):
    cur = obj
    for part in str(path).split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _get_script(batch, sid):
    for s in batch.get("scripts", []):
        if str(s.get("script_id", s.get("id", ""))) == str(sid):
            return s
    return None


def _gate_errors(item, batch):
    errors = []
    gates = item.get("hard_gates", {})
    missing = [g for g in GATES if g not in gates]
    if missing:
        errors.append("missing hard gates: " + ", ".join(missing))
    for gid, gate in gates.items():
        if gid not in GATES:
            errors.append("unknown hard gate: " + gid)
            continue
        if not isinstance(gate, dict) or not isinstance(gate.get("passed"), bool):
            errors.append("invalid hard gate: " + gid)
            continue
        if not str(gate.get("reason", "")).strip():
            errors.append("hard gate reason missing: " + gid)
        if gate.get("passed") is True and not gate.get("evidence_refs") and not gate.get("quote") and not gate.get("not_applicable_reason"):
            errors.append("hard gate lacks evidence or N/A reason: " + gid)
        if gate.get("passed") is True:
            blob = "\n".join(_strings(batch))
            for ref in gate.get("evidence_refs", []):
                if str(ref) not in blob:
                    errors.append("hard gate evidence reference not found in batch: " + gid + ":" + str(ref))
    return errors


def _score_item(script, item):
    errors = []
    scorecard = item.get("scorecard", {})
    if set(scorecard) != set(DIMENSIONS):
        errors.append("scorecard dimensions mismatch")
    total = 0.0
    text_blob = _script_text(script)
    for dim_id, dim in DIMENSIONS.items():
        entry = scorecard.get(dim_id)
        if not isinstance(entry, dict):
            errors.append("missing score dimension: " + dim_id)
            continue
        score = entry.get("score")
        if type(score) is not int or not 0 <= score <= 5:
            errors.append("score must be integer 0..5: " + dim_id)
            continue
        if entry.get("weight") != dim["weight"]:
            errors.append("weight mismatch: " + dim_id)
        quote = str(entry.get("quote", ""))
        field_value = _get_path(script, entry.get("field", ""))
        if not isinstance(field_value, str) or not field_value:
            errors.append("score evidence field path missing or not text: " + dim_id)
        elif not quote or quote not in field_value:
            errors.append("score evidence quote absent from declared field: " + dim_id)
        if not str(entry.get("reason", "")).strip():
            errors.append("score reason missing: " + dim_id)
        total += score / 5.0 * dim["weight"]
    reported = item.get("reported_total_score")
    if reported is None:
        errors.append("reported_total_score missing")
    elif not isinstance(reported, (int, float)) or abs(float(reported) - total) > 0.05:
        errors.append("reported_total_score does not match weighted calculation")
    return round(total, 2), errors


def _candidate_errors(script, item):
    errors = []
    comp = item.get("candidate_competition", {})
    candidates = comp.get("candidates", [])
    if len(candidates) < 3:
        errors.append("at least 3 distinct marketing-angle candidates required")
    ids = [str(x.get("candidate_id", "")) for x in candidates]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        errors.append("candidate IDs missing or duplicated")
    hook_types = {_norm(x.get("hook_type", "")) for x in candidates if x.get("hook_type")}
    payoffs = {_norm(x.get("user_payoff", "")) for x in candidates if x.get("user_payoff")}
    click_reasons = {_norm(x.get("click_reason", "")) for x in candidates if x.get("click_reason")}
    signatures = [(_norm(x.get("hook_type", "")), _norm(x.get("user_payoff", "")), _norm(x.get("click_reason", ""))) for x in candidates]
    if len(hook_types) < 2 or len(payoffs) < 2 or len(click_reasons) < 2 or len(signatures) != len(set(signatures)):
        errors.append("candidate angles are not substantively distinct")
    selected = comp.get("selected_candidate_id")
    if selected not in ids:
        errors.append("selected candidate ID not found")
    for c in candidates:
        if not isinstance(c.get("proof_plan"), list) or not isinstance(c.get("risk"), list):
            errors.append("candidate proof_plan/risk must be arrays")
    for k in ("selection_reason", "counterargument", "counterevidence"):
        if not str(comp.get(k, "")).strip():
            errors.append("decision record missing " + k)
    confidence = comp.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be 0..1")
    if not isinstance(comp.get("unresolved_risks"), list) or not isinstance(comp.get("repair_fields"), list):
        errors.append("unresolved_risks and repair_fields must be arrays")
    if comp.get("locked"):
        locked_fields = comp.get("locked_fields", {})
        if not locked_fields:
            errors.append("locked topic requires explicit locked_fields")
        for field, original in locked_fields.items():
            if script.get(field) != original:
                errors.append("user-locked field changed: " + field)
    plan_id = script.get("plan_id")
    for lock in script.get("copy_locks", []) + script.get("brief_copy_locks", []):
        if lock.get("plan_id") == plan_id:
            for field in ("cover_main", "cover_sub"):
                if field in lock and script.get(field) != lock[field]:
                    errors.append("copy lock changed: " + field)
    return errors


def _review_errors(item, review):
    errors = []
    routing = item.get("review_routing", {})
    pending = []
    independent = False
    generator_identity = str(review.get("generator_identity", "")).strip()
    generator_model = str(review.get("generator_model", "")).strip()
    for role in REVIEW_ROLES:
        r = routing.get(role)
        if not isinstance(r, dict):
            errors.append("review role missing: " + role)
            pending.append(role)
            continue
        if r.get("status") != "PASS":
            pending.append(role)
        if not str(r.get("reviewer_identity", "")).strip():
            errors.append("reviewer identity missing: " + role)
        if r.get("independence_level") in INDEPENDENT_LEVELS:
            same_identity = bool(generator_identity and r.get("reviewer_identity") == generator_identity)
            same_model = bool(generator_model and r.get("model") and r.get("model") == generator_model)
            if same_identity or same_model:
                errors.append("reviewer falsely marked independent but matches generator identity/model: " + role)
                pending.append("independent_review:" + role)
            else:
                independent = True
    return errors, pending, independent


def _validation_status(item):
    pending = []
    voice = item.get("human_voice_test", {})
    if voice.get("status") != "PASS":
        pending.append("human_voice_test")
    elif voice.get("reader_is_author") is True or not voice.get("reader_identity") or not voice.get("evidence"):
        pending.append("human_voice_test_not_independent_or_unproven")
    blind = item.get("blind_test", {})
    if blind.get("status") != "PASS":
        pending.append("blind_test")
    else:
        n = blind.get("participants", 0)
        topic = blind.get("correct_topic_count", 0)
        value = blind.get("correct_value_count", 0)
        ids = blind.get("reader_ids", [])
        if not 3 <= n <= 5 or len(set(ids)) != n or topic < math.ceil(0.8 * n) or value < math.ceil(0.6 * n):
            pending.append("blind_test_threshold_not_met")
    return pending


def validate(batch, review):
    errors, warnings, reports = [], [], []
    if not isinstance(batch, dict) or not isinstance(review, dict):
        return {"passed": False, "status": "INVALID_INPUT", "errors": ["batch and review must be objects"], "items": []}
    payload_sha = hashlib.sha256(json.dumps(batch, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    expected_digest = review.get("batch_sha256")
    if not expected_digest:
        errors.append("review batch_sha256 missing")
    elif expected_digest != payload_sha and review.get("batch_sha256_payload") != payload_sha:
        errors.append("review not bound to this batch payload")
    manifest = review.get("batch_manifest", {})
    if manifest.get("unit_type") != "platform_script":
        errors.append("batch_manifest.unit_type must be platform_script")
    scripts = batch.get("scripts", [])
    expected_scripts = manifest.get("expected_scripts")
    expected_topics = manifest.get("expected_topics")
    if type(expected_scripts) is not int or len(scripts) != expected_scripts:
        errors.append("expected_scripts count mismatch")
    ids = [str(s.get("script_id", s.get("id", ""))) for s in scripts]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        errors.append("script IDs missing or duplicated")
    topic_ids = [str(s.get("topic_id", "")) for s in scripts]
    if any(not x for x in topic_ids):
        errors.append("topic_id missing from one or more scripts")
    if type(expected_topics) is not int or len(set(topic_ids)) != expected_topics:
        errors.append("expected_topics count mismatch")
    expected_by_platform = manifest.get("expected_by_platform", {})
    observed = {}
    for s in scripts:
        p = s.get("platform")
        observed[p] = observed.get(p, 0) + 1
        if not (s.get("business_line") or batch.get("brief", {}).get("business_line")):
            errors.append(str(s.get("id", "?")) + " business_line missing")
    if expected_by_platform != observed:
        errors.append("expected_by_platform count mismatch")
    review_items = review.get("items", [])
    rids = [str(x.get("script_id", "")) for x in review_items]
    if len(rids) != len(set(rids)) or set(rids) != set(ids):
        errors.append("review item count/IDs do not match batch scripts")

    for item in review_items:
        sid = str(item.get("script_id", ""))
        script = _get_script(batch, sid)
        if not script:
            continue
        local = []
        if str(item.get("topic_id", "")) != str(script.get("topic_id", "")):
            local.append("review topic_id mismatch")
        local.extend(_candidate_errors(script, item))
        score, score_errors = _score_item(script, item)
        local.extend(score_errors)
        local.extend(_gate_errors(item, batch))
        decision = item.get("decision", {})
        if not str(decision.get("verdict", "")).strip() or not str(decision.get("reason", "")).strip():
            local.append("decision verdict/reason missing")
        review_errs, role_pending, has_independent = _review_errors(item, review)
        local.extend(review_errs)
        hard_failed = [g for g, v in item.get("hard_gates", {}).items() if isinstance(v, dict) and v.get("passed") is False]
        validation_pending = _validation_status(item)
        if not has_independent:
            validation_pending.append("independent_review")
        if role_pending:
            validation_pending.extend(["review_role:" + x for x in role_pending])
        if hard_failed:
            status = "BLOCKED"
        elif score < 70:
            status = "REWRITE"
        elif score < 75:
            status = "REVISE"
        elif local:
            status = "REVISE"
        elif validation_pending:
            status = "VALIDATION_PENDING"
        elif score >= 85:
            status = "STRONG_CANDIDATE"
        else:
            status = "CANDIDATE"
        expected_verdict = status
        declared_verdict = decision.get("verdict")
        if declared_verdict != expected_verdict:
            local.append("decision verdict mismatch: expected " + expected_verdict)
            if status not in ("BLOCKED", "REWRITE", "REVISE"):
                status = "REVISE"
        reports.append({"script_id": sid, "topic_id": item.get("topic_id"), "score": score, "score_band": status, "hard_gate_failures": hard_failed, "validation_pending": validation_pending, "errors": local})

    diversity = review.get("diversity_review", {})
    if diversity.get("status") != "PASS":
        errors.append("diversity review not PASS")
    if diversity.get("reviewed_script_count") != len(scripts):
        errors.append("diversity review coverage mismatch")
    if not diversity.get("reviewer_identity"):
        errors.append("diversity reviewer identity missing")
    for pair in diversity.get("near_duplicates", []):
        if pair.get("disposition") == "UNRESOLVED" or not pair.get("reason"):
            errors.append("unresolved or unexplained near-duplicate pair")

    statuses = [x["score_band"] for x in reports]
    if errors or any(s in ("BLOCKED", "REWRITE", "REVISE", "NEEDS_REVIEW_REPAIR") for s in statuses):
        overall = "NEEDS_REVISION"
    elif any(s == "VALIDATION_PENDING" for s in statuses):
        overall = "VALIDATION_PENDING"
    else:
        overall = "PASS"
    if not reports:
        overall = "INVALID_INPUT"
    warnings.append("Editorial score is not a prediction of reach, watch time, leads, revenue or platform performance.")
    warnings.append("Unrun human voice, blind-user or independent review steps remain VALIDATION_PENDING; do not claim they passed.")
    return {"passed": overall == "PASS", "status": overall, "errors": errors, "warnings": warnings, "script_count": len(scripts), "topic_count": len(set(x for x in topic_ids if x)), "items": reports, "average_score_diagnostic_only": round(sum(x["score"] for x in reports)/len(reports), 2) if reports else None, "average_used_for_release": False, "validation_scope": "v4.1_contract_and_declared_reviews_not_measured_marketing_performance"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--batch", required=True, help="batch JSON exported by the existing engine")
    p.add_argument("--review", required=True, help="V4.1 review JSON")
    p.add_argument("--output")
    p.add_argument("--require-full-validation", action="store_true", help="return exit 3 unless all independent/human/user validation is complete")
    a = p.parse_args()
    batch_path, review_path = Path(a.batch), Path(a.review)
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    raw_sha = hashlib.sha256(batch_path.read_bytes()).hexdigest()
    payload_sha = hashlib.sha256(json.dumps(batch, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if review.get("batch_sha256") not in (raw_sha, payload_sha):
        raise ValueError("review.batch_sha256 must match the exact batch file SHA256 or normalized payload SHA256")
    review["batch_sha256_payload"] = payload_sha
    result = validate(batch, review)
    result["batch_sha256"] = raw_sha
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if a.output:
        Path(a.output).write_text(rendered, encoding="utf-8")
    print(rendered)
    if result["status"] in ("NEEDS_REVISION", "INVALID_INPUT"):
        return 2
    if a.require_full_validation and result["status"] != "PASS":
        return 3
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("V4.1 validation error: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
