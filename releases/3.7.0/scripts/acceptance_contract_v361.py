#!/usr/bin/env python3
"""v3.6.1 four-layer evidence and delivery acceptance contract.

Deterministic checks bind source files -> facts -> plan decisions -> spoken lines
-> independent review -> external validation. A PASS means the declared evidence
is internally consistent; it is not a prediction of platform performance.
"""
from __future__ import annotations
import hashlib, json, re, zipfile
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

CONTENT_MODES = {
    "real_commercial_case": ("buyer_need", "professional_judgment", "tool_or_method", "product_translation", "result", "transferable_value"),
    "ai_workflow_tutorial": ("original_input", "ai_process", "human_judgment", "output", "application_value"),
    "design_decision_analysis": ("product_brief", "design_constraints", "tradeoff", "product_fit", "decision_rule"),
    "business_opportunity_analysis": ("user_opportunity", "market_evidence", "business_logic", "risk_boundary", "action_recommendation"),
    "hypothetical_scenario": ("simulation_disclosure", "assumptions", "decision_path", "illustrative_output", "applicability_boundary"),
}
CRITERIA = (
    ("user_need", "用户需求"),
    ("topic_selection", "选题"),
    ("cover", "封面"),
    ("opening_0_3", "0–3秒"),
    ("bridge_3_8", "3–8秒"),
    ("body_mode", "正文模式"),
    ("promise_payoff", "爽点兑现"),
    ("capability_amplification", "能力放大"),
    ("next_level_value", "痒点升维"),
    ("calling", "Calling"),
    ("evidence", "证据"),
    ("platform_fit", "平台"),
    ("oral_delivery", "口播"),
    ("independent_review", "独立验收"),
    ("outcome_feedback", "效果回流"),
)
CRITERION_IDS = {x[0] for x in CRITERIA}
PENDING = {"PENDING", "NOT_RUN", "VALIDATION_PENDING"}
PASS = {"PASS", "PASSED"}
FAIL = {"FAIL", "FAILED", "BLOCKED"}


def _s(v: Any) -> str:
    return str(v or "").strip()


def _items(v: Any) -> list:
    return v if isinstance(v, list) else []


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _norm(v: Any) -> str:
    return re.sub(r"\s+", " ", _s(v)).strip()


def _safe_path(root: Path, rel: str) -> Path | None:
    if not rel or Path(rel).is_absolute() or ".." in Path(rel).parts:
        return None
    root = root.resolve()
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if path.is_file() else None


def _extract_text(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json", ".jsonl", ".yaml", ".yml", ".xml", ".html", ".htm", ".py", ".log"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(path) as z:
                chunks = []
                for name in z.namelist():
                    if name.startswith("word/") and name.endswith(".xml") and any(x in name for x in ("document", "header", "footer", "footnotes", "endnotes")):
                        root = ET.fromstring(z.read(name))
                        chunks.extend(x.text or "" for x in root.iter() if x.tag.endswith("}t"))
                return "\n".join(chunks)
        except Exception:
            return None
    if suffix == ".xlsx":
        try:
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True, data_only=True)
            chunks = []
            for ws in wb.worksheets:
                chunks.append("[SHEET] " + ws.title)
                for row in ws.iter_rows(values_only=True):
                    vals = [str(x) for x in row if x is not None]
                    if vals:
                        chunks.append(" | ".join(vals))
            wb.close()
            return "\n".join(chunks)
        except Exception:
            return None
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
        except Exception:
            try:
                import fitz
                doc = fitz.open(path)
                return "\n".join(p.get_text() for p in doc)
            except Exception:
                return None
    return None


def _source_manifest(run: Path) -> tuple[dict, dict[str, dict]]:
    path = run / "source-manifest.json"
    if not path.is_file():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data, {_s(x.get("stored_path")): x for x in _items(data.get("sources")) if isinstance(x, dict)}


def _source_text(run: Path, asset: dict, manifest_by_path: dict[str, dict]) -> tuple[str | None, list[str]]:
    errors = []
    rel = _s(asset.get("source_file") or asset.get("stored_path"))
    entry = manifest_by_path.get(rel)
    if not entry:
        errors.append("SOURCE_FILE_NOT_IN_SOURCE_MANIFEST:" + (rel or "EMPTY"))
        return None, errors
    path = _safe_path(run, rel)
    if not path:
        errors.append("SOURCE_FILE_MISSING_OR_UNSAFE:" + rel)
        return None, errors
    actual = _sha(path)
    expected = _s(asset.get("source_sha256") or asset.get("sha256"))
    if not expected or actual != expected or actual != _s(entry.get("sha256")):
        errors.append("SOURCE_FILE_SHA256_MISMATCH:" + rel)
    extracted = _extract_text(path)
    if extracted is not None:
        return extracted, errors
    evidence_rel = _s(asset.get("extraction_evidence_path"))
    evidence = _safe_path(run, evidence_rel) if evidence_rel else None
    if not evidence:
        errors.append("NON_TEXT_SOURCE_REQUIRES_EXTRACTION_EVIDENCE:" + rel)
        return None, errors
    evidence_sha = _sha(evidence)
    if evidence_sha != _s(asset.get("extraction_evidence_sha256")):
        errors.append("EXTRACTION_EVIDENCE_SHA256_MISMATCH:" + evidence_rel)
    if len(_s(asset.get("extraction_method"))) < 8 or len(_s(asset.get("source_locator"))) < 2:
        errors.append("EXTRACTION_METHOD_OR_ORIGINAL_LOCATOR_MISSING:" + rel)
    return evidence.read_text(encoding="utf-8", errors="replace"), errors


def validate_source_inventory(brief: dict, run_dir: str | Path) -> list[str]:
    run = Path(run_dir).resolve()
    inv = brief.get("source_inventory") if isinstance(brief, dict) else None
    if not isinstance(inv, dict):
        return ["SOURCE_INVENTORY_MISSING"]
    errors = []
    manifest, manifest_by_path = _source_manifest(run)
    if not manifest or not manifest_by_path:
        errors.append("SOURCE_MANIFEST_MISSING_OR_EMPTY")
    status = _s(inv.get("status"))
    if status not in {"complete", "no_source_materials"}:
        errors.append("SOURCE_INVENTORY_STATUS_INVALID")
    checked = _items(inv.get("checked_assets"))
    if status == "complete" and not checked:
        errors.append("SOURCE_INVENTORY_HAS_NO_CHECKED_ASSETS")
    assets_by_id = {}
    for i, asset in enumerate(checked):
        if not isinstance(asset, dict):
            errors.append(f"SOURCE_ASSET_NOT_OBJECT:{i}"); continue
        aid = _s(asset.get("asset_id"))
        if not aid or aid in assets_by_id:
            errors.append(f"SOURCE_ASSET_ID_MISSING_OR_DUPLICATED:{i}"); continue
        assets_by_id[aid] = asset
        if asset.get("read") is not True or len(_s(asset.get("locator"))) < 2 or len(_s(asset.get("source_quote"))) < 4:
            errors.append("SOURCE_ASSET_READ_LOCATOR_OR_QUOTE_MISSING:" + aid)
        text, errs = _source_text(run, asset, manifest_by_path)
        errors.extend(errs)
        if text is not None and _norm(asset.get("source_quote")) not in _norm(text):
            errors.append("SOURCE_ASSET_QUOTE_NOT_FOUND_IN_ORIGINAL_OR_EXTRACTION:" + aid)
    if status == "no_source_materials" and len(_s(inv.get("no_source_reason"))) < 20:
        errors.append("NO_SOURCE_MATERIALS_REASON_MISSING")
    if status == "complete" and len(_s(inv.get("selection_reason"))) < 20:
        errors.append("SOURCE_SELECTION_REASON_MISSING")
    fact_map = {_s(x.get("id")): x for x in _items(brief.get("facts")) if isinstance(x, dict) and _s(x.get("id"))}
    fact_evidence = {_s(x.get("fact_id")): x for x in _items(inv.get("fact_evidence")) if isinstance(x, dict) and _s(x.get("fact_id"))}
    for fid, fact in fact_map.items():
        state = _s(fact.get("status")).lower()
        if state in {"provided", "verified"}:
            ev = fact_evidence.get(fid)
            if not ev:
                errors.append("FACT_WITHOUT_SOURCE_EVIDENCE:" + fid); continue
            aid = _s(ev.get("source_asset_id")); asset = assets_by_id.get(aid)
            if not asset:
                errors.append("FACT_SOURCE_ASSET_UNKNOWN:" + fid); continue
            if _s(ev.get("source_file")) != _s(asset.get("source_file") or asset.get("stored_path")):
                errors.append("FACT_SOURCE_FILE_DIFFERS_FROM_INVENTORY:" + fid)
            if _s(ev.get("source_sha256")) != _s(asset.get("source_sha256") or asset.get("sha256")):
                errors.append("FACT_SOURCE_HASH_DIFFERS_FROM_INVENTORY:" + fid)
            if _norm(ev.get("source_quote")) != _norm(asset.get("source_quote")) and _norm(ev.get("source_quote")) not in _norm(asset.get("source_quote")):
                errors.append("FACT_QUOTE_NOT_BOUND_TO_INVENTORY_QUOTE:" + fid)
        elif state == "inference":
            if not _items(fact.get("derived_from_fact_ids")):
                errors.append("INFERENCE_WITHOUT_PARENT_FACTS:" + fid)
        elif state in {"hypothetical", "unknown", "not_run", "not_verified"}:
            pass
        else:
            errors.append("FACT_EVIDENCE_STATUS_UNRECOGNIZED:" + fid + ":" + state)
    real_ids = {fid for fid, fact in fact_map.items() if fact.get("evidence_class") == "user_project" and _s(fact.get("status")).lower() in {"provided", "verified"}}
    relevant = set(map(_s, _items(inv.get("relevant_real_case_ids"))))
    selected = set(map(_s, _items(inv.get("selected_real_case_ids"))))
    excluded_rows = _items(inv.get("excluded_relevant_source_ids"))
    excluded = {_s(x.get("id")): _s(x.get("reason")) for x in excluded_rows if isinstance(x, dict)}
    if not relevant.issubset(real_ids): errors.append("RELEVANT_REAL_CASE_IDS_NOT_BACKED_BY_FACTS")
    if not selected.issubset(relevant): errors.append("SELECTED_REAL_CASE_NOT_RELEVANT")
    if not set(excluded).issubset(relevant): errors.append("EXCLUDED_REAL_CASE_NOT_RELEVANT")
    for fid in relevant:
        if fid not in selected and len(excluded.get(fid, "")) < 20:
            errors.append("RELEVANT_REAL_CASE_REJECTED_WITHOUT_REASON:" + fid)
    policy = _s(brief.get("case_policy") or "prefer_real")
    if policy not in {"prefer_real", "real_only", "allow_simulation_if_no_fit", "explicit_simulation"}:
        errors.append("CASE_POLICY_INVALID")
    if policy == "explicit_simulation" and brief.get("explicit_simulation_authorized") is not True:
        errors.append("SIMULATION_NOT_EXPLICITLY_AUTHORIZED")
    if policy == "real_only" and relevant and not selected:
        errors.append("REAL_ONLY_WITHOUT_SELECTED_REAL_CASE")
    if policy == "prefer_real" and relevant and not selected and not relevant.issubset(set(excluded)):
        errors.append("PREFER_REAL_POLICY_IGNORED_RELEVANT_REAL_CASE")
    return errors


def validate_decision_competition(decision: dict, brief: dict, domain: str, run_dir: str | Path) -> list[str]:
    errors = []
    if isinstance(decision, dict) and 'topic_competitions' in decision:
        if 'marketing_entry_competition' in decision:
            return ['TOPIC_AND_BATCH_COMPETITIONS_ARE_AMBIGUOUS']
        rows = decision.get('topic_competitions')
        plans = _items(decision.get('selected'))
        if not isinstance(rows, list) or not rows or any(not isinstance(x, dict) for x in rows):
            return ['TOPIC_COMPETITIONS_MISSING_OR_INVALID']
        plan_ids = [_s(x.get('id') or x.get('plan_id')) for x in plans if isinstance(x, dict)]
        row_ids = [_s(x.get('plan_id')) for x in rows]
        if len(plan_ids) != len(plans) or any(not x for x in plan_ids) or len(set(plan_ids)) != len(plan_ids):
            errors.append('TOPIC_COMPETITION_SELECTED_PLAN_IDS_INVALID')
        if len(set(row_ids)) != len(row_ids):
            errors.append('TOPIC_COMPETITION_PLAN_IDS_DUPLICATED')
        if set(row_ids) != set(plan_ids):
            errors.append('TOPIC_COMPETITION_PLAN_COVERAGE_MISMATCH')
        if errors:
            return errors
        by_plan = {_s(x['plan_id']): x for x in rows}
        for plan in plans:
            pid = _s(plan.get('id') or plan.get('plan_id'))
            one = {'selected': [plan], 'marketing_entry_competition': by_plan[pid].get('competition')}
            errors.extend(pid + ':' + e for e in validate_decision_competition(one, brief, domain, run_dir))
        return errors
    comp = decision.get("marketing_entry_competition") if isinstance(decision, dict) else None
    if not isinstance(comp, dict):
        return ["MARKETING_ENTRY_COMPETITION_MISSING"]
    candidates = _items(comp.get("candidates"))
    if len(candidates) < 3:
        errors.append("MARKETING_ENTRY_REQUIRES_AT_LEAST_THREE_CANDIDATES")
    ids = [_s(x.get("candidate_id")) for x in candidates if isinstance(x, dict)]
    if len(ids) != len(candidates) or any(not x for x in ids) or len(set(ids)) != len(ids):
        errors.append("MARKETING_ENTRY_CANDIDATE_IDS_MISSING_OR_DUPLICATED")
    fields = ("entry_type", "target_user", "user_need", "hook", "click_reason", "promised_payoff", "evidence_refs", "delivery_plan", "commercial_value", "risk", "counter_evidence")
    known_evidence = {_s(x.get("id")) for x in _items(brief.get("facts")) if isinstance(x, dict)} | {_s(x.get("id")) for x in _items(brief.get("production_resources")) if isinstance(x, dict)}
    known_evidence |= {_s(x.get("asset_id")) for x in _items((brief.get("source_inventory") or {}).get("checked_assets")) if isinstance(x, dict)}
    for i, c in enumerate(candidates):
        if not isinstance(c, dict):
            errors.append(f"MARKETING_ENTRY_CANDIDATE_NOT_OBJECT:{i}"); continue
        cid = _s(c.get("candidate_id")) or str(i)
        for key in fields:
            val = c.get(key)
            if key == "evidence_refs":
                if not _items(val): errors.append("MARKETING_ENTRY_EVIDENCE_PLAN_MISSING:" + cid)
                elif any(_s(ref) not in known_evidence for ref in _items(val)): errors.append("MARKETING_ENTRY_EVIDENCE_REF_UNKNOWN:" + cid)
            elif len(_s(val)) < 12:
                errors.append(f"MARKETING_ENTRY_{key.upper()}_MISSING:{cid}")
        if c.get("selected") is True and len(_s(c.get("selection_reason"))) < 20:
            errors.append("SELECTED_ENTRY_SELECTION_REASON_MISSING:" + cid)
        if c.get("selected") is not True and len(_s(c.get("rejection_reason"))) < 20:
            errors.append("REJECTED_ENTRY_REASON_MISSING:" + cid)
    selected = [x for x in candidates if isinstance(x, dict) and x.get("selected") is True]
    if len(selected) != 1:
        errors.append("MARKETING_ENTRY_MUST_SELECT_EXACTLY_ONE")
    if len({_s(x.get("entry_type")) for x in candidates if isinstance(x, dict)}) < 3:
        errors.append("MARKETING_ENTRY_TYPES_NOT_THREE_DISTINCT")
    for key in ("hook", "user_need", "click_reason", "promised_payoff"):
        vals = {_norm(x.get(key)) for x in candidates if isinstance(x, dict) and _s(x.get(key))}
        if len(vals) < 3:
            errors.append("MARKETING_ENTRY_OPTIONS_ARE_SUPERFICIAL_REWRITES:" + key)
    if len(_s(comp.get("comparison_summary"))) < 30 or len(_s(comp.get("decision_reason"))) < 30:
        errors.append("MARKETING_ENTRY_COMPARISON_OR_DECISION_REASON_MISSING")
    if not _items(comp.get("tradeoffs")):
        errors.append("MARKETING_ENTRY_TRADEOFFS_MISSING")
    if selected:
        plan_ids = {_s(x.get("id") or x.get("plan_id")) for x in _items(decision.get("selected")) if isinstance(x, dict)}
        chosen = selected[0]
        selected_id = _s(chosen.get("candidate_id"))
        if _s(comp.get("selected_candidate_id")) != selected_id:
            errors.append("MARKETING_ENTRY_SELECTED_ID_MISMATCH")
        for plan in _items(decision.get("selected")):
            if isinstance(plan, dict) and _s(plan.get("selected_entry_candidate_id")) != selected_id:
                errors.append("PLAN_NOT_BOUND_TO_SELECTED_ENTRY_CANDIDATE:" + _s(plan.get("id")))
    return errors


def _script_text(script: dict) -> str:
    return "\n".join(_s(x.get("text")) for x in _items(script.get("segments")) if isinstance(x, dict))


def _role_segments(script: dict, roles: set[str]) -> list[dict]:
    return [x for x in _items(script.get("segments")) if isinstance(x, dict) and _s(x.get("role")).lower() in roles]


def validate_draft_delivery(batch: dict, decision: dict, brief: dict, domain: str, run_dir: str | Path) -> list[str]:
    errors = []
    plans = {_s(x.get("id") or x.get("plan_id")): x for x in _items(decision.get("selected")) if isinstance(x, dict)}
    inv = brief.get("source_inventory", {}) if isinstance(brief.get("source_inventory"), dict) else {}
    fact_ids = {_s(x.get("id")) for x in _items(brief.get("facts")) if isinstance(x, dict)}
    for script in _items(batch.get("scripts")):
        if not isinstance(script, dict): continue
        sid = _s(script.get("script_id") or script.get("id")) or "UNKNOWN"
        pid = _s(script.get("plan_id") or script.get("topic_id"))
        plan = plans.get(pid)
        if not plan:
            errors.append("SCRIPT_PLAN_NOT_FOUND:" + sid); continue
        mode = _s(plan.get("content_mode"))
        if _s(script.get("content_mode")) != mode:
            errors.append("SCRIPT_CONTENT_MODE_MISMATCH:" + sid)
        if _s(script.get("selected_entry_candidate_id")) != _s(plan.get("selected_entry_candidate_id")):
            errors.append("SCRIPT_NOT_BOUND_TO_SELECTED_ENTRY:" + sid)
        # Exact source-to-speech anchors: each factual spoken claim must resolve to a selected fact.
        claim_rows = _items(script.get("claim_evidence"))
        if not claim_rows:
            errors.append("SCRIPT_CLAIM_EVIDENCE_MAP_MISSING:" + sid)
        inv_assets = {_s(x.get("asset_id")): x for x in _items(inv.get("checked_assets")) if isinstance(x, dict)}
        _, manifest_by_path = _source_manifest(Path(run_dir).resolve())
        for row in claim_rows:
            if not isinstance(row, dict): continue
            fid = _s(row.get("fact_id")); claim = _s(row.get("spoken_claim_quote")); source_quote = _s(row.get("source_quote"))
            if fid not in fact_ids or fid not in set(map(_s, _items(script.get("source_fact_ids")))):
                errors.append("SCRIPT_CLAIM_FACT_NOT_SELECTED:" + sid + ":" + fid)
            if not claim or claim not in _script_text(script):
                errors.append("SCRIPT_CLAIM_QUOTE_NOT_IN_SPOKEN_TEXT:" + sid + ":" + fid)
            aid = _s(row.get("source_asset_id")); asset = inv_assets.get(aid)
            if not asset:
                errors.append("SCRIPT_SOURCE_ASSET_NOT_IN_INVENTORY:" + sid + ":" + aid)
            else:
                expected_file = _s(asset.get("source_file") or asset.get("stored_path"))
                expected_hash = _s(asset.get("source_sha256") or asset.get("sha256"))
                if _s(row.get("source_file")) != expected_file or _s(row.get("source_sha256")) != expected_hash:
                    errors.append("SCRIPT_SOURCE_FILE_OR_HASH_NOT_BOUND_TO_INVENTORY:" + sid + ":" + fid)
                text, source_errors = _source_text(Path(run_dir).resolve(), asset, manifest_by_path)
                errors.extend(source_errors)
                if text is not None and (not source_quote or _norm(source_quote) not in _norm(text)):
                    errors.append("SCRIPT_SOURCE_QUOTE_NOT_FOUND_IN_ORIGINAL:" + sid + ":" + fid)
            fact_ev = next((x for x in _items(inv.get("fact_evidence")) if isinstance(x, dict) and _s(x.get("fact_id")) == fid), {})
            if not source_quote or len(_s(row.get("source_locator"))) < 2 or len(_s(row.get("source_sha256"))) != 64:
                errors.append("SCRIPT_SOURCE_CITATION_INCOMPLETE:" + sid + ":" + fid)
            if _s(row.get("source_locator")) != _s(fact_ev.get("source_locator")):
                errors.append("SCRIPT_SOURCE_LOCATOR_NOT_BOUND_TO_FACT_EVIDENCE:" + sid + ":" + fid)
        selected_facts = set(map(_s, _items((plan.get("source_selection") or {}).get("selected_fact_ids"))))
        script_facts = set(map(_s, _items(script.get("source_fact_ids"))))
        if not selected_facts.issubset(script_facts):
            errors.append("SCRIPT_DROPPED_SELECTED_FACTS:" + sid)
        # Mode-specific narrative map must map every required story beat to actual spoken words.
        nmap = script.get("narrative_map") if isinstance(script.get("narrative_map"), dict) else {}
        if _s(nmap.get("content_mode")) != mode:
            errors.append("NARRATIVE_MAP_MODE_MISSING_OR_MISMATCH:" + sid)
        stages = { _s(x.get("stage_id")): x for x in _items(nmap.get("stages")) if isinstance(x, dict) }
        for stage in CONTENT_MODES.get(mode, ()):
            row = stages.get(stage)
            if not row or len(_s(row.get("quote"))) < 8 or _s(row.get("quote")) not in _script_text(script):
                errors.append("NARRATIVE_STAGE_NOT_ANCHORED_TO_SPOKEN_TEXT:" + sid + ":" + stage)
        if mode == "hypothetical_scenario":
            disclosure = _s((plan.get("source_selection") or {}).get("simulation_disclosure"))
            if not disclosure or disclosure not in _script_text(script):
                errors.append("SIMULATION_DISCLOSURE_NOT_SPOKEN:" + sid)
        # Cover and first-eight-second chain are real copy, not decorative metadata.
        cover = script.get("cover") if isinstance(script.get("cover"), dict) else {}
        main = _s(script.get("cover_main") or cover.get("main"))
        sub = _s(script.get("cover_sub") or cover.get("sub"))
        if len(main) < 6 or len(sub) < 6 or _norm(main) == _norm(sub):
            errors.append("COVER_MAIN_SUBTITLE_NOT_DISTINCT:" + sid)
        hooks = _role_segments(script, {"hook", "opening", "opening_0_3", "0_3", "0–3"})
        bridges = _role_segments(script, {"bridge", "suspense", "opening_bridge", "3_8", "3–8"})
        if not hooks or not _s(hooks[0].get("text")):
            errors.append("OPENING_0_3_MISSING:" + sid)
        if not bridges or not _s(bridges[0].get("text")):
            errors.append("BRIDGE_3_8_MISSING:" + sid)
        elif hooks and _norm(bridges[0].get("text")) == _norm(hooks[0].get("text")):
            errors.append("BRIDGE_3_8_REPEATS_OPENING:" + sid)
        # Calling is a single action, reason and user payoff.
        calling = script.get("calling") if isinstance(script.get("calling"), dict) else {}
        cta_quote = _s(calling.get("quote"))
        cta_text = " ".join(_s(x.get("text")) for x in _role_segments(script, {"calling", "cta"}))
        if not cta_quote or cta_quote not in cta_text or len(_s(calling.get("action"))) < 5 or len(_s(calling.get("reason"))) < 12 or len(_s(calling.get("user_payoff"))) < 12:
            errors.append("CALLING_NOT_SINGLE_ACTION_WITH_REASON_AND_USER_PAYOFF:" + sid)
        # Platform-native output must be explicit, not one script copied three times.
        platform = _s(script.get("platform"))
        fit = script.get("platform_fit") if isinstance(script.get("platform_fit"), dict) else {}
        if not platform or _s(fit.get("platform")) != platform or len(_s(fit.get("user_task"))) < 12 or len(_s(fit.get("native_expression_reason"))) < 20 or not _s(fit.get("quote")) or _s(fit.get("quote")) not in _script_text(script):
            errors.append("PLATFORM_NATIVE_DELIVERY_NOT_EVIDENCED:" + sid)
    return errors


def _file_evidence(run: Path, record: dict, path_key: str, sha_key: str, prefix: str) -> tuple[Path | None, list[str]]:
    errors = []
    rel = _s(record.get(path_key)); path = _safe_path(run, rel) if rel else None
    if not path:
        errors.append(prefix + "_EVIDENCE_FILE_MISSING_OR_UNSAFE")
        return None, errors
    if _sha(path) != _s(record.get(sha_key)):
        errors.append(prefix + "_EVIDENCE_SHA256_MISMATCH")
    return path, errors


def validate_reviewer_attestation(review: dict, batch_path: Path, decision_path: Path, run: Path) -> list[str]:
    errors = []
    a = review.get("reviewer_attestation") if isinstance(review, dict) else None
    if not isinstance(a, dict): return ["INDEPENDENT_REVIEW_ATTESTATION_MISSING"]
    for key in ("reviewer_id", "generator_id", "reviewer_session_id", "generator_session_id", "reviewed_at", "independence_level", "review_evidence_path", "review_evidence_sha256", "blind_packet_path", "blind_packet_sha256", "batch_sha256", "decision_sha256", "source_manifest_sha256", "attestation_method"):
        if not _s(a.get(key)): errors.append("REVIEW_ATTESTATION_FIELD_MISSING:" + key)
    if _s(a.get("reviewer_id")) == _s(a.get("generator_id")):
        errors.append("REVIEWER_ID_EQUALS_GENERATOR")
    if _s(a.get("reviewer_session_id")) == _s(a.get("generator_session_id")):
        errors.append("REVIEWER_SESSION_EQUALS_GENERATOR_SESSION")
    if a.get("independent") is not True or a.get("same_model_role") is not False:
        errors.append("REVIEWER_INDEPENDENCE_NOT_ATTESTED")
    if a.get("reviewer_mode") not in {"human", "separate_model"}:
        errors.append("REVIEWER_MODE_INVALID")
    if a.get("reviewer_mode") == "separate_model" and _s(a.get("reviewer_model")) == _s(a.get("generator_model")):
        errors.append("REVIEWER_MODEL_EQUALS_GENERATOR_MODEL")
    if a.get("reviewer_mode") == "human" and len(_s(a.get("reviewer_confirmation"))) < 20:
        errors.append("HUMAN_REVIEWER_CONFIRMATION_MISSING")
    if _s(a.get("batch_sha256")) != _sha(batch_path): errors.append("REVIEW_ATTESTATION_BATCH_SHA_MISMATCH")
    if _s(a.get("decision_sha256")) != _sha(decision_path): errors.append("REVIEW_ATTESTATION_DECISION_SHA_MISMATCH")
    manifest_path = run / "source-manifest.json"
    if not manifest_path.is_file() or _s(a.get("source_manifest_sha256")) != _sha(manifest_path):
        errors.append("REVIEW_ATTESTATION_SOURCE_MANIFEST_SHA_MISMATCH")
    review_file, errs = _file_evidence(run, a, "review_evidence_path", "review_evidence_sha256", "REVIEW")
    errors.extend(errs)
    blind_file, errs = _file_evidence(run, a, "blind_packet_path", "blind_packet_sha256", "BLIND_PACKET")
    errors.extend(errs)
    if review_file:
        content = review_file.read_text(encoding="utf-8", errors="replace")
        if _s(a.get("batch_sha256")) not in content or _s(a.get("reviewer_id")) not in content:
            errors.append("REVIEW_EVIDENCE_DOES_NOT_BIND_REVIEWER_AND_BATCH")
    if blind_file:
        content = blind_file.read_text(encoding="utf-8", errors="replace")
        if a.get("contains_scores") is not False:
            errors.append("BLIND_PACKET_MUST_NOT_CONTAIN_SCORES_OR_REVIEWER_CUES")
        if _s(a.get("batch_sha256")) not in content:
            errors.append("BLIND_PACKET_NOT_BOUND_TO_BATCH")
    return errors


def _validate_external(run: Path, review: dict, scripts: list[dict], attestation: dict) -> tuple[str, list[str], dict]:
    errors = []
    ext = review.get("external_validation") if isinstance(review, dict) else None
    if not isinstance(ext, dict): return "VALIDATION_PENDING", ["EXTERNAL_VALIDATION_MISSING"], {}
    ids = {_s(x.get("script_id") or x.get("id")) for x in scripts}
    report = {}
    # Human voice test: each script must have a non-author reader and a real recording/log.
    voice_rows = {_s(x.get("script_id")): x for x in _items(ext.get("human_voice_test")) if isinstance(x, dict)}
    for sid in ids:
        row = voice_rows.get(sid)
        if row and _s(row.get("status")) in FAIL:
            errors.append("HUMAN_VOICE_TEST_FAILED:" + sid)
            continue
        if not row or _s(row.get("status")) not in PASS:
            report.setdefault(sid, []).append("human_voice_test_pending")
            continue
        if row.get("reader_is_author") is not False or len(_s(row.get("reader_id"))) < 2:
            errors.append("HUMAN_VOICE_READER_NOT_INDEPENDENT:" + sid)
        if not isinstance(row.get("measured_seconds"), (int, float)) or not isinstance(row.get("target_seconds"), (int, float)) or row.get("target_seconds", 0) <= 0:
            errors.append("HUMAN_VOICE_TIMING_MISSING:" + sid)
        elif abs(row["measured_seconds"] - row["target_seconds"]) / row["target_seconds"] > 0.20:
            errors.append("HUMAN_VOICE_DURATION_DEVIATION_OVER_20_PERCENT:" + sid)
        voice_evidence, e = _file_evidence(run, row, "evidence_path", "evidence_sha256", "HUMAN_VOICE")
        errors.extend(e)
        if voice_evidence and voice_evidence.suffix.lower() not in {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}:
            if len(_s(row.get("reader_confirmation"))) < 20 or row.get("recording_present") is not True:
                errors.append("HUMAN_VOICE_NON_AUDIO_LOG_LACKS_READER_ATTESTATION:" + sid)
    # Target-user blind read: per-script, 3-5 anonymous readers, thresholded comprehension.
    blind_rows = {_s(x.get("script_id")): x for x in _items(ext.get("target_user_blind_read")) if isinstance(x, dict)}
    for sid in ids:
        row = blind_rows.get(sid)
        if row and _s(row.get("status")) in FAIL:
            errors.append("TARGET_USER_BLIND_READ_FAILED:" + sid)
            continue
        if not row or _s(row.get("status")) not in PASS:
            report.setdefault(sid, []).append("target_user_blind_read_pending"); continue
        participants = _items(row.get("participants")); pids = [_s(x.get("participant_id")) for x in participants if isinstance(x, dict)]
        n = len(participants)
        if not 3 <= n <= 5 or len(set(pids)) != n or any(not x for x in pids):
            errors.append("BLIND_READ_REQUIRES_3_TO_5_UNIQUE_READERS:" + sid)
        if row.get("author_present") is not False:
            errors.append("BLIND_READ_NOT_BLIND:" + sid)
        topic = row.get("correct_topic_count", -1); value = row.get("correct_value_count", -1)
        if any(not isinstance(x, dict) or type(x.get("topic_understood")) is not bool or type(x.get("value_understood")) is not bool for x in participants):
            errors.append("BLIND_READ_PARTICIPANT_ANSWERS_MISSING:" + sid)
        else:
            observed_topic = sum(1 for x in participants if x.get("topic_understood") is True)
            observed_value = sum(1 for x in participants if x.get("value_understood") is True)
            if topic != observed_topic or value != observed_value:
                errors.append("BLIND_READ_COUNTS_DO_NOT_MATCH_PARTICIPANT_ANSWERS:" + sid)
        if _s(row.get("blind_packet_sha256")) != _s(attestation.get("blind_packet_sha256")):
            errors.append("BLIND_READ_PACKET_SHA_MISMATCH:" + sid)
        if not isinstance(topic, int) or not isinstance(value, int) or (n and (topic < int((0.8*n)+0.999) or value < int((0.6*n)+0.999))):
            errors.append("BLIND_READ_COMPREHENSION_THRESHOLD_NOT_MET:" + sid)
        _, e = _file_evidence(run, row, "evidence_path", "evidence_sha256", "BLIND_READ")
        errors.extend(e)
    # Rights: every used original asset needs a documented basis.
    rights = ext.get("rights_and_permissions") if isinstance(ext.get("rights_and_permissions"), dict) else {}
    rights_rows = {_s(x.get("asset_id")): x for x in _items(rights.get("assets")) if isinstance(x, dict)}
    used_assets = set()
    for s in scripts:
        used_assets.update(map(_s, _items(s.get("source_asset_ids"))))
        used_assets.update(map(_s, _items(s.get("production_resource_ids"))))
    for aid in used_assets:
        row = rights_rows.get(aid)
        if row and _s(row.get("rights_status")) in {"DENIED", "NOT_AUTHORIZED", "EXPIRED", "REVOKED"}:
            errors.append("RIGHTS_OR_PERMISSION_DENIED:" + aid)
            continue
        if not row or _s(row.get("rights_status")) not in {"USER_OWNED", "LICENSED", "AUTHORIZED", "PUBLIC_DOMAIN", "NOT_REQUIRED"}:
            report.setdefault(_s(next((s.get("id") or s.get("script_id") for s in scripts if aid in _items(s.get("source_asset_ids")) + _items(s.get("production_resource_ids"))), "unknown")), []).append("rights_and_permissions_pending")
            continue
        if _s(row.get("rights_status")) != "NOT_REQUIRED":
            _, e = _file_evidence(run, row, "evidence_path", "evidence_sha256", "RIGHTS")
            errors.extend(e)
    # Platform outcome: a real post and traceable analytics are required; no invented zeroes.
    outcomes = {_s(x.get("script_id")): x for x in _items(ext.get("platform_outcome")) if isinstance(x, dict)}
    for sid in ids:
        row = outcomes.get(sid)
        if row and _s(row.get("status")) in FAIL:
            errors.append("PLATFORM_OUTCOME_FAILED:" + sid)
            continue
        if not row or _s(row.get("status")) not in PASS:
            report.setdefault(sid, []).append("platform_outcome_pending"); continue
        metrics = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
        if not _s(row.get("post_url")) or not _s(row.get("post_id")) or not _s(row.get("published_at")) or not _s(row.get("captured_at")) or not _s(row.get("data_source")):
            errors.append("PLATFORM_OUTCOME_POST_OR_CAPTURE_METADATA_MISSING:" + sid)
        if not any(isinstance(v, (int, float)) and v >= 0 for v in metrics.values()):
            errors.append("PLATFORM_OUTCOME_HAS_NO_OBSERVED_METRICS:" + sid)
        _, e = _file_evidence(run, row, "evidence_path", "evidence_sha256", "PLATFORM_OUTCOME")
        errors.extend(e)
        analysis = row.get("analysis") if isinstance(row.get("analysis"), dict) else {}
        for key in ("baseline_or_comparator", "diagnosis", "attribution_limit", "next_action"):
            if len(_s(analysis.get(key))) < 20:
                errors.append("PLATFORM_OUTCOME_FEEDBACK_FIELD_MISSING:" + sid + ":" + key)
    if errors:
        return "BLOCKED", errors, report
    if any(report.values()):
        return "VALIDATION_PENDING", [], report
    return "PASS", [], report


def visible_review_copy(script: dict) -> dict:
    """Actual delivery only. This verifies review input fidelity, not quality."""
    cover = script.get('cover') if isinstance(script.get('cover'), dict) else {}
    return {
        'script_id': _s(script.get('script_id') or script.get('id')),
        'platform': _s(script.get('platform')),
        'target_audience': _s(script.get('audience') or script.get('target_audience')),
        'publish_title': _s(script.get('title')),
        'cover_main': _s(script.get('cover_main') or cover.get('main')),
        'cover_sub': _s(script.get('cover_sub') or cover.get('sub')),
        'segments': [{k: seg[k] for k in ('id', 'role', 'duration_seconds', 'text', 'visual', 'subtitle', 'shot') if k in seg}
                     for seg in _items(script.get('segments')) if isinstance(seg, dict)],
        'comment_hook': script.get('comment_hook'),
    }


def validate_blind_copy(blind_data: dict, scripts: list[dict]) -> list[str]:
    rows = blind_data.get('actual_copy') if isinstance(blind_data, dict) else None
    if not isinstance(rows, list) or not rows:
        return ['BLIND_PACKET_ACTUAL_COPY_MISSING']
    if any(not isinstance(x, dict) for x in rows):
        return ['BLIND_PACKET_ACTUAL_COPY_INVALID']
    expected = {x['script_id']: x for x in map(visible_review_copy, scripts)}
    ids = [_s(x.get('script_id')) for x in rows]
    if len(set(ids)) != len(ids) or set(ids) != set(expected):
        return ['BLIND_PACKET_ACTUAL_COPY_COVERAGE_MISMATCH']
    return ['BLIND_PACKET_COPY_MISMATCH:' + x['script_id'] for x in rows if x != expected[x['script_id']]]


def _competition_for_plan(decision: dict, plan_id: str) -> dict:
    if 'topic_competitions' in decision:
        row = next((x for x in _items(decision.get('topic_competitions'))
                    if isinstance(x, dict) and _s(x.get('plan_id')) == plan_id), {})
        return row.get('competition', {})
    return decision.get('marketing_entry_competition', {})


def validate_review(batch: dict, decision: dict, brief: dict, review: dict, run_dir: str | Path, batch_path: str | Path) -> dict:
    run = Path(run_dir).resolve(); bp = Path(batch_path).resolve(); dp = run / "decision.json"
    errors = []
    if not dp.is_file(): errors.append("SEALED_DECISION_JSON_MISSING")
    scripts = [x for x in _items(batch.get("scripts")) if isinstance(x, dict)]
    acceptance_rows = _items(review.get("delivery_acceptance"))
    checks_by_id = {_s(x.get("script_id")): x for x in acceptance_rows if isinstance(x, dict)}
    ids = {_s(x.get("script_id") or x.get("id")) for x in scripts}
    if set(checks_by_id) != ids or len(acceptance_rows) != len(ids) or len(checks_by_id) != len(acceptance_rows):
        errors.append("DELIVERY_ACCEPTANCE_SCRIPT_COVERAGE_MISMATCH_OR_DUPLICATE")
    att = review.get("reviewer_attestation") if isinstance(review.get("reviewer_attestation"), dict) else {}
    att_errors = validate_reviewer_attestation(review, bp, dp, run) if dp.is_file() else ["DECISION_FILE_MISSING_FOR_REVIEW_ATTESTATION"]
    if not att_errors:
        review_evidence = _safe_path(run, _s(att.get("review_evidence_path")))
        blind_packet = _safe_path(run, _s(att.get("blind_packet_path")))
        script_ids = {_s(x.get("script_id") or x.get("id")) for x in scripts}
        if review_evidence:
            evidence_text = review_evidence.read_text(encoding="utf-8", errors="replace")
            if any(sid not in evidence_text for sid in script_ids):
                att_errors.append("REVIEW_EVIDENCE_DOES_NOT_COVER_EVERY_SCRIPT")
        if blind_packet:
            try:
                blind_data = json.loads(blind_packet.read_text(encoding="utf-8"))
                if not isinstance(blind_data, dict):
                    raise ValueError('blind packet must be an object')
                att_errors.extend(validate_blind_copy(blind_data, scripts))
                blind_ids = set(map(_s, _items(blind_data.get("script_ids"))))
                if not script_ids.issubset(blind_ids):
                    att_errors.append("BLIND_PACKET_DOES_NOT_COVER_EVERY_SCRIPT")
                def has_score_key(obj):
                    if isinstance(obj, dict):
                        return any(("score" in str(k).lower() or "评分" in str(k) or "reviewer" in str(k).lower()) or has_score_key(v) for k, v in obj.items())
                    if isinstance(obj, list): return any(has_score_key(v) for v in obj)
                    return False
                if has_score_key(blind_data):
                    att_errors.append("BLIND_PACKET_CONTAINS_REVIEWER_OR_SCORE_CUES")
            except (ValueError, OSError):
                att_errors.append('BLIND_PACKET_JSON_OBJECT_REQUIRED')
    errors.extend(att_errors)
    att_status = "PASS" if not att_errors else "BLOCKED"
    ext_status, ext_errors, ext_report = _validate_external(run, review, scripts, att)
    errors.extend(ext_errors)
    overall_pending = ext_status == "VALIDATION_PENDING"
    for script in scripts:
        sid = _s(script.get("script_id") or script.get("id")); record = checks_by_id.get(sid, {})
        rows = _items(record.get("checks"))
        by_criterion = {_s(x.get("criterion_id")): x for x in rows if isinstance(x, dict)}
        if set(by_criterion) != CRITERION_IDS or len(rows) != 15 or len(by_criterion) != len(rows):
            errors.append("FIFTEEN_CRITERIA_NOT_EXACTLY_COVERED:" + sid)
        for cid, label in CRITERIA:
            item = by_criterion.get(cid, {})
            status = _s(item.get("status"))
            if status not in {"PASS", "FAIL", "PENDING", "NOT_APPLICABLE"}:
                errors.append("CRITERION_STATUS_INVALID:" + sid + ":" + cid); continue
            if len(_s(item.get("reason"))) < 20:
                errors.append("CRITERION_REASON_TOO_SHORT:" + sid + ":" + cid)
            quotes = list(map(_s, _items(item.get("quotes"))))
            if status == "PASS" and cid not in {"topic_selection", "evidence", "oral_delivery", "independent_review", "outcome_feedback"}:
                if not quotes or any(q not in _script_text(script) and q not in _s(script.get("cover_main")) and q not in _s(script.get("cover_sub")) for q in quotes):
                    errors.append("CRITERION_PASS_WITHOUT_ACTUAL_SCRIPT_QUOTES:" + sid + ":" + cid)
            if status == "NOT_APPLICABLE" and (cid != "capability_amplification" or len(_s(item.get("not_applicable_reason"))) < 20):
                errors.append("CRITERION_NOT_APPLICABLE_NOT_JUSTIFIED:" + sid + ":" + cid)
            if status == "FAIL": errors.append("NON_COMPENSATORY_CRITERION_FAILED:" + sid + ":" + cid)
            if status == "PENDING": overall_pending = True
            hook_text = " ".join(_s(x.get("text")) for x in _role_segments(script, {"hook", "opening", "opening_0_3", "0_3", "0–3"}))
            bridge_text = " ".join(_s(x.get("text")) for x in _role_segments(script, {"bridge", "suspense", "opening_bridge", "3_8", "3–8"}))
            cta_text = " ".join(_s(x.get("text")) for x in _role_segments(script, {"calling", "cta"}))
            body_text = " ".join(_s(x.get("text")) for x in _items(script.get("segments")) if isinstance(x, dict) and _s(x.get("role")).lower() not in {"hook", "opening", "opening_0_3", "0_3", "0–3", "bridge", "suspense", "opening_bridge", "3_8", "3–8", "calling", "cta"})
            if cid == "user_need" and status == "PASS" and not any(q in hook_text + " " + bridge_text for q in quotes):
                errors.append("USER_NEED_NOT_EXPRESSED_IN_OPENING:" + sid)
            if cid == "topic_selection" and status == "PASS":
                comp = _competition_for_plan(decision, _s(script.get('plan_id') or script.get('topic_id')))
                candidate_ids = {_s(x.get("candidate_id")) for x in _items(comp.get("candidates")) if isinstance(x, dict)}
                used = set(map(_s, _items(item.get("evidence_refs"))))
                if not candidate_ids or not candidate_ids.issubset(used) or _s(comp.get("selected_candidate_id")) not in used:
                    errors.append("TOPIC_SELECTION_NOT_BOUND_TO_THREE_CANDIDATE_COMPARISON:" + sid)
            if cid == "cover" and status == "PASS":
                if _s(script.get("cover_main")) not in quotes or _s(script.get("cover_sub")) not in quotes:
                    errors.append("COVER_ACCEPTANCE_MUST_QUOTE_MAIN_AND_SUBTITLE:" + sid)
            if cid == "opening_0_3" and status == "PASS" and not any(q in hook_text for q in quotes):
                errors.append("OPENING_ACCEPTANCE_NOT_BOUND_TO_0_3_HOOK:" + sid)
            if cid == "bridge_3_8" and status == "PASS" and not any(q in bridge_text for q in quotes):
                errors.append("BRIDGE_ACCEPTANCE_NOT_BOUND_TO_3_8_SEGMENT:" + sid)
            if cid == "body_mode" and status == "PASS":
                nmap = script.get("narrative_map", {})
                required_stages = CONTENT_MODES.get(_s(nmap.get("content_mode")), ())
                stage_quotes = [_s(x.get("quote")) for x in _items(nmap.get("stages")) if isinstance(x, dict)]
                if not required_stages or any(not q or q not in body_text for q in stage_quotes) or not set(stage_quotes).issubset(set(quotes)):
                    errors.append("BODY_MODE_ACCEPTANCE_NOT_BOUND_TO_ALL_MODE_STAGES:" + sid)
            if cid == "promise_payoff" and status == "PASS":
                if len(quotes) < 2 or not (quotes[0] in _s(script.get("cover_main")) + _s(script.get("cover_sub")) + hook_text) or quotes[1] not in body_text:
                    errors.append("PROMISE_PAYOFF_MUST_BIND_PROMISE_AND_BODY_RESULT:" + sid)
            if cid == "capability_amplification" and status == "PASS":
                cap = script.get("capability_amplification") if isinstance(script.get("capability_amplification"), dict) else {}
                if not quotes or not any(q in body_text for q in quotes) or not _items(item.get("evidence_refs")) or len(_s(cap.get("human_ai_boundary"))) < 12:
                    errors.append("CAPABILITY_AMPLIFICATION_ACCEPTANCE_LACKS_BODY_PROOF_OR_HUMAN_AI_BOUNDARY:" + sid)
            if cid == "next_level_value" and status == "PASS":
                next_need = _s(item.get("next_need")); promised = _s((next((x for x in _items(decision.get("selected")) if _s(x.get("id")) == _s(script.get("plan_id"))), {}) or {}).get("content_contract", {}).get("promised_payoff"))
                similarity = SequenceMatcher(None, _norm(next_need), _norm(promised), autojunk=False).ratio() if promised and next_need else 0.0
                if not quotes or not any(q in cta_text for q in quotes) or len(next_need) < 12 or similarity > 0.82:
                    errors.append("NEXT_LEVEL_VALUE_NOT_DISTINCT_OR_NOT_IN_CALLING:" + sid)
            if cid == "calling" and status == "PASS":
                calling = script.get("calling", {}) if isinstance(script.get("calling"), dict) else {}
                if not quotes or not any(q in cta_text for q in quotes) or len(_s(calling.get("action"))) < 5 or len(_s(calling.get("reason"))) < 12 or len(_s(calling.get("user_payoff"))) < 12:
                    errors.append("CALLING_NOT_ONE_ACTION_REASON_AND_USER_PAYOFF:" + sid)
            if cid == "evidence" and status == "PASS":
                fact_refs = set(map(_s, _items(script.get("source_fact_ids"))))
                used = set(map(_s, _items(item.get("evidence_refs"))))
                if fact_refs and not fact_refs.issubset(used): errors.append("EVIDENCE_ACCEPTANCE_DROPS_FACT_IDS:" + sid)
            if cid == "platform_fit" and status == "PASS":
                fit = script.get("platform_fit", {}) if isinstance(script.get("platform_fit"), dict) else {}
                if not quotes or _s(fit.get("quote")) not in quotes or _s(fit.get("platform")) != _s(script.get("platform")):
                    errors.append("PLATFORM_ACCEPTANCE_NOT_BOUND_TO_PLATFORM_NATIVE_QUOTE:" + sid)
            if cid == "oral_delivery" and status == "PASS" and ext_status == "VALIDATION_PENDING":
                if "human_voice_test_pending" in ext_report.get(sid, []): errors.append("ORAL_DELIVERY_PASS_WITHOUT_HUMAN_VOICE_EVIDENCE:" + sid)
            if cid == "independent_review" and status == "PASS" and att_status != "PASS":
                errors.append("INDEPENDENT_REVIEW_PASS_WITHOUT_VALID_ATTESTATION:" + sid)
            if cid == "outcome_feedback" and status == "PASS" and "platform_outcome_pending" in ext_report.get(sid, []):
                errors.append("OUTCOME_FEEDBACK_PASS_WITHOUT_REAL_PLATFORM_DATA:" + sid)
    if errors:
        status = "BLOCKED"
    elif overall_pending or ext_status != "PASS":
        status = "VALIDATION_PENDING"
    else:
        status = "PASS"
    return {
        "passed": status == "PASS",
        "status": status,
        "errors": errors,
        "external_validation_status": ext_status,
        "reviewer_attestation_status": att_status,
        "script_count": len(scripts),
        "criteria_per_script": len(CRITERIA),
        "criteria_total": len(CRITERIA) * len(scripts),
        "average_score_used_for_release": False,
        "per_script_external_pending": ext_report,
        "release_rule": "No average-score compensation. Any failed criterion blocks; any unrun human/user/platform validation remains VALIDATION_PENDING."
    }


def validate_plan_stage(decision: dict, brief: dict, domain: str, run_dir: str | Path) -> list[str]:
    errors = validate_source_inventory(brief, run_dir)
    errors.extend(validate_decision_competition(decision, brief, domain, run_dir))
    return errors


def validate_draft_stage(batch: dict, decision: dict, brief: dict, domain: str, run_dir: str | Path) -> list[str]:
    errors = validate_source_inventory(brief, run_dir)
    errors.extend(validate_decision_competition(decision, brief, domain, run_dir))
    errors.extend(validate_draft_delivery(batch, decision, brief, domain, run_dir))
    return errors


def main():
    import argparse, sys
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=["intake", "plan", "draft", "review"], required=True)
    p.add_argument("--run", required=True)
    p.add_argument("--brief")
    p.add_argument("--decision")
    p.add_argument("--batch")
    p.add_argument("--review")
    a = p.parse_args()
    run = Path(a.run).resolve()
    brief = json.loads(Path(a.brief or run / "brief.json").read_text(encoding="utf-8"))
    if a.stage == "intake": errors = validate_source_inventory(brief, run)
    elif a.stage == "plan": errors = validate_plan_stage(json.loads(Path(a.decision).read_text(encoding="utf-8")), brief, _s(brief.get("domain")), run)
    elif a.stage == "draft": errors = validate_draft_stage(json.loads(Path(a.batch).read_text(encoding="utf-8")), json.loads(Path(a.decision).read_text(encoding="utf-8")), brief, _s(brief.get("domain")), run)
    else:
        result = validate_review(json.loads(Path(a.batch).read_text(encoding="utf-8")), json.loads(Path(a.decision).read_text(encoding="utf-8")), brief, json.loads(Path(a.review).read_text(encoding="utf-8")), run, a.batch)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result["status"] != "BLOCKED" else 2
    print(json.dumps({"passed": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2

if __name__ == "__main__":
    raise SystemExit(main())
