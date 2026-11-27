"""V3 purchase evidence, competing entries, exact draft fields and release gates."""
from datetime import date
import re
import unicodedata

from execution_contract import canonical
from acceptance_contract_v361 import CONTENT_MODES

FIELDS = ("audience", "content_entry", "cover_main", "cover_sub", "hook_0_3",
          "bridge_3_8", "body", "calling", "comment")
GATES = {
    "customer_value": ("audience",),
    "marketing_expression": ("content_entry", "cover_main", "cover_sub", "hook_0_3", "bridge_3_8"),
    "fulfillment": ("body", "calling", "comment"),
}
REPAIR = dict(zip(FIELDS, ("M04", "M06.1", "M08.1", "M08.1", "M08.1", "M08.1",
                          "M01/M05.1/M08.1", "M08.1", "M08.1")))
DIMENSIONS = ("relevance", "click_reason", "new_information", "customer_benefit",
              "proof", "platform_task", "commercial_next_step")
ENTRY_TYPES = {"objection", "decision", "scenario", "comparison", "risk", "efficiency",
               "evidence", "contrast", "experience"}
STRENGTH = {"ADVANTAGE_VERIFIED": 3, "FIT_SUPPORTED": 2, "INFO_ONLY": 1}
CLAIMS = {"fact": 1, "fit": 2, "comparison": 3}
ARCHIVE = {"KB_ACCESS_DENIED", "KB_NO_MATCH", "KB_HASH_MISMATCH", "KB_VERSION_MISMATCH",
           "KB_NOT_CONFIGURED"}


def require(condition, code, repair, detail):
    if not condition:
        raise ValueError(f"{code} [{repair}] {detail}")


def normalized(value):
    return "".join(ch for ch in unicodedata.normalize("NFKC", value).casefold() if ch.isalnum())


def text_fields(record, fields, repair):
    require(isinstance(record, dict), "CONTRACT_INVALID", repair, "expected an object")
    for field in fields:
        val = record.get(field)
        require(isinstance(val, str) and bool(val.strip()), "FIELD_MISSING", repair, field)


def ids(rows, key, repair):
    require(isinstance(rows, list) and bool(rows), "RECORDS_MISSING", repair, key)
    result = {}
    for row in rows:
        text_fields(row, (key,), repair)
        value = row[key]
        require(value not in result, "DUPLICATE_ID", repair, value)
        result[value] = row
    return result


def refs(values, available, repair, optional=False):
    require(isinstance(values, list) and (optional or values) and all(
        isinstance(item, str) and item in available for item in values
    ), "PROOF_REF_MISSING", repair, str(values))


def validate_snapshot(snapshot):
    text_fields(snapshot, ("status",), "M03")
    if snapshot["status"] != "VERIFIED":
        require(snapshot["status"] in ARCHIVE, "KB_STATUS_INVALID", "M03", snapshot["status"])
        text_fields(snapshot, ("reason",), "M03")
        require(not snapshot.get("assets"), "KB_UNVERIFIED_ASSETS", "M03", "discard inaccessible results")
        return
    text_fields(snapshot, ("repository_id", "registry_ref", "asset_ref", "manifest_sha256"), "M03")
    for key, length in (("registry_ref", 40), ("asset_ref", 40), ("manifest_sha256", 64)):
        require(bool(re.fullmatch(f"[a-f0-9]{{{length}}}", snapshot[key])),
                "KB_VERSION_MISMATCH", "M03", key)
    for item in ids(snapshot.get("assets"), "id", "M03").values():
        text_fields(item, ("locator", "use", "citation"), "M03")
        require(f"/blob/{snapshot['asset_ref']}/" in item["citation"],
                "KB_VERSION_MISMATCH", "M03", item["id"])


def evidence_for(record, sources, as_of):
    evidence = ids(record.get("evidence"), "id", "M01")
    for key, item in evidence.items():
        text_fields(item, ("source_id", "locator", "scope", "rights", "status", "kind",
                           "supported_statement", "claim_limit", "source_date"), "M01")
        source = sources.get(item["source_id"], {})
        require(source.get("read") is True and source.get("locator") == item["locator"]
                and source.get("source_sha256") == item.get("sha256"),
                "EVIDENCE_SOURCE_MISMATCH", "M01", key)
        require(item["rights"] in {"public", "authorized", "internal"} and item.get("conflict") is not True,
                "RIGHTS_OR_FACT_HOLD", "M01", key)
        require(item["status"] in {"VERIFIED", "USER_PROVIDED", "PUBLIC_SOURCE", "INFERENCE", "SIMULATED"},
                "EVIDENCE_STATUS_INVALID", "M01", key)
        require(item["kind"] in {"attribute", "comparison", "experience", "service", "need", "demo"},
                "EVIDENCE_KIND_INVALID", "M01", key)
        date.fromisoformat(item["source_date"])
        if item.get("valid_until"):
            require(date.fromisoformat(item["valid_until"]) >= date.fromisoformat(as_of),
                    "EVIDENCE_STALE", "M01/M05.1", key)
    return evidence


def validate_claim(claim, evidence, level):
    text_fields(claim, ("id", "type", "text", "scope"), "M05.1")
    kind = claim["type"]
    require(kind in CLAIMS and CLAIMS[kind] <= STRENGTH[level],
            "CLAIM_OVERREACH", "M05.1", claim["id"])
    refs(claim.get("proof_refs"), evidence, "M05.1")
    proof = [evidence[ref] for ref in claim["proof_refs"]]
    require(all(row["rights"] in {"public", "authorized"} for row in proof),
            "RIGHTS_OR_FACT_HOLD", "M01", claim["id"])
    if kind == "comparison":
        require(any(row["kind"] == "comparison" and row["status"] == "VERIFIED" for row in proof),
                "PROJECT_CHOICE_PROOF_INSUFFICIENT", "M05.1", claim["id"])
    if kind == "fit":
        require(any(row["kind"] in {"attribute", "service", "demo"}
                    and row["status"] in {"VERIFIED", "USER_PROVIDED", "PUBLIC_SOURCE"} for row in proof),
                "PROJECT_CHOICE_PROOF_INSUFFICIENT", "M05.1", claim["id"])
    testimonials = [row for row in proof if row["kind"] == "experience"]
    if testimonials:
        identity_allowed = not claim.get("identifies_customer") or all(
            row.get("identity_authorized") is True for row in testimonials)
        require(claim.get("population") == "specific_sample" and identity_allowed,
                "TESTIMONIAL_OVERREACH", "M01/M05.1", claim["id"])
    require(claim.get("guaranteed_outcome") is not True, "CLAIM_OVERREACH", "M05.1", claim["id"])
    if any(row["status"] == "SIMULATED" for row in proof):
        require(claim.get("simulation_disclosed") is True, "SIMULATION_UNDISCLOSED", "M01", claim["id"])


def validate_topic(topic, brief):
    record = topic.get("decision_v3")
    text_fields(record, ("as_of",), "M00")
    date.fromisoformat(record["as_of"])
    customer = record.get("customer")
    text_fields(customer, ("audience_id", "decision_id", "buyer_role", "context", "current_task",
                           "root_need", "trigger", "alternative", "barrier", "decision_criterion",
                           "benefit"), "M04")
    require(customer["current_task"] == topic["buyer_decision"] and customer["benefit"] == topic["payoff"],
            "CUSTOMER_DECISION_DRIFT", "M04", topic["id"])
    sources = {row["asset_id"]: row for row in brief["source_inventory"]["checked_assets"]}
    evidence = evidence_for(record, sources, record["as_of"])
    refs(customer.get("evidence_refs"), evidence, "M04")
    category = record.get("category")
    text_fields(category, ("option", "alternative", "reason", "tradeoff"), "M05")
    require(normalized(category["option"]) != normalized(category["alternative"]),
            "CATEGORY_ALTERNATIVE_MISSING", "M05", topic["id"])
    purchase = record.get("purchase")
    text_fields(purchase, ("id", "status", "reason", "content_type", "claim_limit", "counter_evidence"), "M05.1")
    level = purchase["status"]
    if level not in STRENGTH:
        require(False, "PROJECT_CHOICE_PROOF_INSUFFICIENT" if level != "BLOCKED" else "PUBLISH_HOLD",
                "M05.1", "repair, or explicitly resubmit as INFO_ONLY with scoped facts")
    refs(purchase.get("proof_refs"), evidence, "M05.1")
    purchase_proof = [evidence[key] for key in purchase["proof_refs"]]
    if level == "ADVANTAGE_VERIFIED":
        comparison = purchase.get("comparison")
        text_fields(comparison, ("option", "alternative", "dimension", "scenario", "period",
                                 "specification", "denominator"), "M05.1")
        require(comparison.get("comparable") is True and
                normalized(comparison["option"]) != normalized(comparison["alternative"]) and
                any(row["kind"] == "comparison" and row["status"] == "VERIFIED" for row in purchase_proof),
                "COMPARISON_NOT_COMPARABLE", "M05.1", topic["id"])
    elif level == "FIT_SUPPORTED":
        require(any(row["kind"] in {"attribute", "service", "demo"} and row["status"] in
                    {"VERIFIED", "USER_PROVIDED", "PUBLIC_SOURCE"} for row in purchase_proof),
                "PROJECT_CHOICE_PROOF_INSUFFICIENT", "M05.1", topic["id"])
    else:
        require(purchase["content_type"] in {"information", "scene_discovery", "education"} and
                any(row["status"] in {"VERIFIED", "USER_PROVIDED", "PUBLIC_SOURCE"} for row in purchase_proof),
                "PROJECT_CHOICE_PROOF_INSUFFICIENT", "M05.1", "INFO_ONLY needs facts and an informational goal")

    mapping = record.get("value_map")
    text_fields(mapping, ("feature", "capability", "capability_scope", "difference_or_fit", "benefit",
                          "purchase_reason_id", "entry_id", "platform_task", "expression", "claim_limit"),
                "M06.1")
    refs(mapping.get("proof_refs"), evidence, "M06.1")
    require(mapping["benefit"] == customer["benefit"] and mapping["purchase_reason_id"] == purchase["id"]
            and normalized(mapping["feature"]) != normalized(mapping["benefit"]),
            "BENEFIT_MAP_INVALID", "M05.1/M06.1", topic["id"])
    claims = ids(record.get("claims"), "id", "M05.1")
    for claim in claims.values():
        validate_claim(claim, evidence, level)
    entries = ids(record.get("entries"), "id", "M06.1")
    seen = set()
    for entry in entries.values():
        text_fields(entry, ("id", "angle", "question", "benefit", "payoff", "candidate_copy", "rationale"),
                    "M06.1")
        require(entry["angle"] in ENTRY_TYPES, "INVALID_ENTRY_TYPE", "M06.1", entry["id"])
        refs(entry.get("proof_refs"), evidence, "M06.1", optional=True)
        scores = entry.get("scores", {})
        require(set(scores) == set(DIMENSIONS) and all(type(n) is int and 0 <= n <= 4 for n in scores.values()),
                "ENTRY_COMPARISON_INCOMPLETE", "M06.1", entry["id"])
        seen.add((normalized(entry["question"]), normalized(entry["benefit"]), normalized(entry["payoff"])))
    require(len(entries) >= 3 and len(seen) == len(entries), "ENTRIES_NOT_DISTINCT", "M06.1", topic["id"])
    selected = entries.get(mapping["entry_id"])
    require(selected and selected["proof_refs"] and selected["benefit"] == customer["benefit"]
            and all(selected["scores"][field] >= 3 for field in ("relevance", "proof", "customer_benefit")),
            "ENTRY_NOT_SUPPORTED", "M06.1", topic["id"])
    require(all(normalized(entry["candidate_copy"]) != normalized(selected["candidate_copy"])
                for entry in entries.values() if entry is not selected),
            "ENTRIES_NOT_DISTINCT", "M06.1", topic["id"])
    text_fields(record, ("promise", "content_goal", "calling_action", "calling_reason",
                         "calling_reward", "comment_task", "risk", "platform_difference",
                         "series_id", "topic_type", "presentation_form", "narrative_mode",
                         "funnel_stage", "unique_payoff"), "M06.1")
    require(record["narrative_mode"] in CONTENT_MODES, "NARRATIVE_MODE_INVALID",
            "M06.1/M08.1", topic["id"])
    require(record["calling_action"] == topic["next_step"], "ACTION_DRIFT", "M07", topic["id"])
    if level == "INFO_ONLY":
        require(record["content_goal"] in {"information", "scene_discovery", "education"},
                "PROJECT_CHOICE_PROOF_INSUFFICIENT", "M05.1", topic["id"])
    return record


def actual_fields(script, topic):
    by_role = {}
    body = []
    for segment in script["segments"]:
        role, text = segment["role"], segment["text"]
        if role in {"bridge", "bridge_3_8"}:
            role = "suspense"
        if role in {"hook", "suspense", "calling"}:
            require(role not in by_role, "MULTIPLE_PRIMARY_SEGMENTS", "M08.1", role)
            by_role[role] = text
        elif role != "comment":
            body.append(text)
    return {"audience": script.get("audience"), "content_entry": script.get("v3_content_entry"),
            "cover_main": script.get("cover_main"), "cover_sub": script.get("cover_sub"),
            "hook_0_3": by_role.get("hook"), "bridge_3_8": by_role.get("suspense"),
            "body": "\n".join(body), "calling": by_role.get("calling"),
            "comment": script.get("comment_hook", {}).get("line")}


def validate_draft(batch, topics):
    for script in batch["scripts"]:
        topic = topics[script["plan_id"]]
        record = topic["decision_v3"]
        require(script.get("v3_handoff_sha256") == canonical(record)
                and script.get("content_mode") == record["narrative_mode"]
                and script.get("selected_entry_candidate_id") == record["value_map"]["entry_id"],
                "HANDOFF_DRIFT", "M07", topic["id"])
        fields = actual_fields(script, topic)
        text_fields(fields, FIELDS, "M08.1")
        winner = next(item for item in record["entries"] if item["id"] == record["value_map"]["entry_id"])
        require(fields["content_entry"] == winner["question"], "HANDOFF_DRIFT", "M06.1/M07", topic["id"])
        opening = [normalized(fields[key]) for key in ("cover_main", "cover_sub", "hook_0_3", "bridge_3_8")]
        require(len(set(opening)) == len(opening), "NO_EXPRESSION_PROGRESSION", "M08.1", topic["id"])
        require(normalized(record["calling_action"]) in normalized(fields["calling"]),
                "CALLING_DRIFT", "M08.1", topic["id"])
        require(not any(normalized(s["text"]) == normalized(fields["comment"]) for s in script["segments"])
                or record.get("allow_spoken_comment") is True, "SPOKEN_COMMENT_UNAUTHORIZED", "M08.1", topic["id"])
        claims = {row["id"]: row for row in record["claims"]}
        traces = ids(script.get("v3_claims"), "claim_id", "M08.1")
        require(set(traces) <= claims.keys() and any(row.get("field") == "body" for row in traces.values()),
                "BODY_PROOF_MISSING", "M01/M05.1/M08.1", topic["id"])
        for row in traces.values():
            text_fields(row, ("field", "quote"), "M08.1")
            require(row["field"] in FIELDS and row["quote"] in fields[row["field"]],
                    "CLAIM_QUOTE_MISMATCH", "M08.1", row["claim_id"])


def validate_review(batch, topics, record, batch_sha, reviewer_id):
    text_fields(record, ("batch_sha256", "reviewer_id"), "M12.1")
    require(record["batch_sha256"] == batch_sha and reviewer_id and record["reviewer_id"] == reviewer_id,
            "V3_REVIEW_BINDING", "M12.1", "reviewer or batch changed")
    reviews = ids(record.get("scripts"), "plan_id", "M12.1")
    require(set(reviews) == set(topics), "V3_REVIEW_COVERAGE", "M12.1", "review each selected topic")
    for script in batch["scripts"]:
        i = script["plan_id"]
        actual = actual_fields(script, topics[i])
        review = reviews[i]
        checks = ids(review.get("fields"), "id", "M12.1")
        require(set(checks) == set(FIELDS), "NINE_FIELD_COVERAGE", "M12.1", i)
        for field, check in checks.items():
            text_fields(check, ("quote", "reason", "status"), "M12.1")
            require(check["quote"] in actual[field] and check["status"] == "PASS",
                    "NINE_FIELD_BLOCKED", REPAIR[field], f"{i}/{field}: {check['reason']}")
        gates = ids(review.get("gates"), "id", "M12.1")
        require(set(gates) == set(GATES), "THREE_GATE_COVERAGE", "M12.1", i)
        for gate, fields in GATES.items():
            check = gates[gate]
            text_fields(check, ("reason", "status"), "M12.1")
            require(set(check.get("fields", [])) == set(fields) and check["status"] == "PASS",
                    "THREE_GATE_BLOCKED", {"customer_value": "M04/M05.1",
                                           "marketing_expression": "M06.1/M08.1",
                                           "fulfillment": "M01/M05.1/M08.1"}[gate],
                    f"{i}/{gate}: {check['reason']}")


def validate_context(context):
    text_fields(context, ("run_id", "execution_mode", "offer", "commercial_goal"), "M00")
    require(context["execution_mode"] in {"proposal", "direct", "revision"},
            "RUN_MODE_INVALID", "M00", context["execution_mode"])
    route = context.get("route")
    text_fields(route, ("primary_adapter_id", "adapter_version", "business_model", "route_reason"),
                "M02")
    require(isinstance(route.get("overlay_adapter_ids"), list) and
            route.get("route_confidence") in {"verified", "provisional"},
            "ADAPTER_ROUTE_INVALID", "M02", "mark uncertain routes provisional")
    project = context.get("project_scope")
    if project is not None:
        text_fields(project, ("project_id", "client_id", "rights_scope", "access_scope"), "M02")
        require(project["access_scope"] in {"current_task", "authorized_project"},
                "KB_ACCESS_DENIED", "M02", project["project_id"])
    require(context.get("production_mode", "none") in {"none", "04", "05", "04+05"},
            "PRODUCTION_MODE_INVALID", "M10", str(context.get("production_mode")))
    validate_snapshot(context.get("knowledge"))
