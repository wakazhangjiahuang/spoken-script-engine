#!/usr/bin/env python3
"""v3.4.2 source-bound content gate.

This module does not invent audiences or score creative appeal. It verifies that
existing domain guidance is actually loaded, each plan/script points to an exact
source need, and the professional decision is genuinely spoken and reviewable.
"""
from __future__ import annotations
import hashlib, json, re, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

VALID_CASE_MODES = {"real", "simulated", "method"}
VALID_SOURCE_STATUS = {"USER_PROVIDED", "VERIFIED", "PUBLIC_SOURCE", "INFERENCE", "SIMULATED", "UNKNOWN"}
AI_DIMS = {"audience_need", "cover_click_reason", "opening_bridge", "body_payoff", "evidence_credibility", "platform_native", "cta_comment", "human_voice_originality"}
ILL_DIMS = {"audience_and_task", "entry_and_click_reason", "first_8_seconds", "professional_judgment_and_payoff", "facts_evidence_and_rights", "platform_native_expression", "calling_and_action", "spoken_naturalness"}
ILL_WEIGHTS = {"audience_and_task":15,"entry_and_click_reason":15,"first_8_seconds":15,"professional_judgment_and_payoff":20,"facts_evidence_and_rights":15,"platform_native_expression":10,"calling_and_action":5,"spoken_naturalness":5}
BODY_ROLES = {"context", "judgment", "value", "proof", "evidence", "material", "decision"}
ACTION_ROLES = {"calling", "cta"}


def _s(v):
    return str(v or "").strip()

def _canonical_domain(brief):
    d = _s(brief.get('domain')).lower().replace('-', '_')
    topic = _s(brief.get('topic'))
    if d in {'ai_video','ai_video_business','aivideo','ai视频','ai视频业务'} or brief.get('quality_profile') == 'ai_video_v4_1':
        return 'ai_video'
    if d in {'illustration','print_design','illustration_surface_pattern_textile_print'} or (d == 'design_service' and any(x in topic for x in ('插画','印花'))):
        return 'illustration'
    if not d and any(x in topic for x in ('插画','印花','母婴图案','床品图案')):
        return 'illustration'
    return d or 'general'


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_text(path: Path) -> str:
    """Extract readable source text without changing the source file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {'.md', '.txt', '.json', '.jsonl'}:
        return path.read_text(encoding='utf-8', errors='replace')
    if suffix == '.docx':
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml')
        root = ET.fromstring(xml)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        blocks = []
        for para in root.findall('.//w:p', ns):
            value = ''.join(t.text or '' for t in para.findall('.//w:t', ns)).strip()
            if value:
                blocks.append(value)
        return '\n'.join(blocks)
    if suffix == '.xlsx':
        try:
            from openpyxl import load_workbook
        except Exception as exc:
            raise ValueError('openpyxl is required to read a source workbook') from exc
        wb = load_workbook(path, data_only=True, read_only=True)
        out = []
        for ws in wb.worksheets:
            out.append(f'[{ws.title}]')
            for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 600), values_only=True):
                vals = [str(v) for v in row if v is not None and str(v).strip()]
                if vals:
                    out.append(' | '.join(vals))
        wb.close()
        return '\n'.join(out)
    return ''


def build_source_registry(root: Path, run_dir: Path, brief: dict, pack: dict) -> dict:
    """Build a runtime registry from current private manifests and staged user sources."""
    root, run_dir = Path(root), Path(run_dir)
    registry = {}
    # Text already extracted into the pack is authoritative only when it carries a source ID.
    for key, item in (pack.get('must_read_guidance') or {}).items():
        if not isinstance(item, dict):
            continue
        aid = _s(item.get('source_asset_id'))
        text = _s(item.get('text'))
        if aid and text:
            registry[aid] = {'asset_id': aid, 'source_path': _s(item.get('source_path') or key), 'text': text,
                             'sha256': _s(item.get('sha256') or item.get('file_sha256')), 'role': _s(item.get('role'))}
    domain = _canonical_domain(brief)
    manifest_path = None
    if domain == 'illustration':
        manifest_path = root / 'assets/illustration/manifest.json'
    elif domain == 'ai_video':
        manifest_path = root / 'assets/ai-video/manifest.json'
    if manifest_path and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for asset in manifest.get('current_assets', []):
            aid, rel = _s(asset.get('asset_id')), _s(asset.get('path'))
            if not aid or not rel:
                continue
            path = (root / rel).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                continue
            expected = _s(asset.get('sha256'))
            actual = _sha(path)
            if expected and expected != actual:
                raise ValueError(f'current source asset SHA mismatch: {aid}')
            text = extract_text(path)
            if text:
                registry[aid] = {'asset_id': aid, 'source_path': rel, 'text': text, 'sha256': actual,
                                 'role': _s(asset.get('role'))}
    # Staged AI-video files bind their logical source IDs to the exact copied file in this run.
    dm_path = run_dir / 'domain-asset-manifest.json'
    if dm_path.is_file():
        dm = json.loads(dm_path.read_text(encoding='utf-8'))
        for asset in dm.get('assets', []):
            aid = _s(asset.get('source_asset_id'))
            rel = _s(asset.get('run_path'))
            if not aid or not rel:
                continue
            path = (run_dir / rel).resolve()
            if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
                continue
            actual = _sha(path)
            expected = _s(asset.get('sha256'))
            if expected and actual != expected:
                raise ValueError(f'staged source asset SHA mismatch: {aid}')
            text = extract_text(path)
            if text:
                registry[aid] = {'asset_id': aid, 'source_path': rel, 'text': text, 'sha256': actual,
                                 'role': _s(asset.get('role'))}
    # User-supplied files are valid evidence sources, but do not silently become domain guidance.
    sm_path = run_dir / 'source-manifest.json'
    if sm_path.is_file():
        sm = json.loads(sm_path.read_text(encoding='utf-8'))
        for source in sm.get('sources', []):
            rel = _s(source.get('stored_path'))
            if not rel:
                continue
            path = (run_dir / rel).resolve()
            if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
                continue
            actual = _sha(path)
            expected = _s(source.get('sha256'))
            if expected and actual != expected:
                raise ValueError('user source SHA mismatch: ' + rel)
            text = extract_text(path)
            aid = 'USER_SOURCE:' + _s(source.get('original_name') or Path(rel).name)
            if text:
                registry[aid] = {'asset_id': aid, 'source_path': rel, 'text': text, 'sha256': actual, 'role': 'user_source'}
    return registry


def _locator_matches(locator: str, source_text: str) -> bool:
    tokens = [x.strip() for x in re.split(r'[>/／|#]+', locator) if len(x.strip()) >= 2]
    return bool(tokens) and any(token in source_text for token in tokens)


def validate_need_ref(ref: dict, registry: dict, domain: str = '') -> list[str]:
    errors = []
    if not isinstance(ref, dict):
        return ['AUDIENCE_NEED_REF_MISSING']
    aid = _s(ref.get('source_asset_id'))
    locator = _s(ref.get('source_locator'))
    quote = _s(ref.get('source_quote'))
    if not aid or aid not in registry:
        errors.append('AUDIENCE_NEED_SOURCE_ASSET_NOT_LOADED:' + (aid or 'EMPTY'))
        return errors
    text = registry[aid]['text']
    if len(quote) < 6 or quote not in text:
        errors.append('AUDIENCE_NEED_QUOTE_NOT_VERBATIM:' + aid)
    if len(locator) < 3 or not _locator_matches(locator, text):
        errors.append('AUDIENCE_NEED_LOCATOR_NOT_IN_SOURCE:' + aid)
    d = domain.lower().replace('-', '_')
    if d in {'illustration', 'print_design', 'illustration_surface_pattern_textile_print', 'design_service'} and aid not in {'ILLUSTRATION-GUIDANCE-V2.0'}:
        errors.append('ILLUSTRATION_NEED_MUST_BIND_TO_V2_GUIDANCE')
    if d in {'ai_video', 'ai_video_business', 'aivideo', 'ai视频', 'ai视频业务'} and aid not in {'AI-VIDEO-BUSINESS-GUIDE-V4.1'}:
        errors.append('AI_VIDEO_NEED_MUST_BIND_TO_V4_1_BUSINESS_GUIDE')
    return errors


def _ngrams(s: str):
    s = re.sub(r'[^\w\u4e00-\u9fff]', '', _s(s)).casefold()
    s = re.sub(r'[和与及以及还有]', '', s)
    if len(s) < 3:
        return {s} if s else set()
    return {s[i:i+2] for i in range(len(s)-1)}


def _similarity(a: str, b: str) -> float:
    aa, bb = _ngrams(a), _ngrams(b)
    return len(aa & bb) / max(1, len(aa | bb))


def _segments(script):
    return script.get('segments', []) if isinstance(script.get('segments'), list) else []


def _find_segment(script, seg_id):
    return next((x for x in _segments(script) if _s(x.get('id')) == _s(seg_id)), None)


def _anchor_check(script, anchors, key, allowed_roles):
    if not isinstance(anchors, dict) or not isinstance(anchors.get(key), dict):
        return [f'SPOKEN_DECISION_ANCHOR_MISSING:{key}']
    item = anchors[key]
    seg = _find_segment(script, item.get('segment_id'))
    quote = _s(item.get('quote'))
    if not seg or len(quote) < 6 or quote not in _s(seg.get('text')):
        return [f'SPOKEN_DECISION_ANCHOR_NOT_VERBATIM:{key}']
    if _s(seg.get('role')).lower() not in allowed_roles:
        return [f'SPOKEN_DECISION_ANCHOR_WRONG_ROLE:{key}']
    return []


def validate_professional_decision(script: dict, expected_need: dict, registry: dict, known_evidence: set, domain: str) -> list[str]:
    sid = _s(script.get('script_id') or script.get('id') or 'UNKNOWN')
    errors = []
    pd = script.get('professional_decision')
    if not isinstance(pd, dict):
        return [f'{sid}:PROFESSIONAL_DECISION_MISSING']
    need = pd.get('audience_need_ref')
    errors.extend([f'{sid}:{e}' for e in validate_need_ref(need, registry, domain)])
    if expected_need is not None and need != expected_need:
        errors.append(f'{sid}:SCRIPT_AUDIENCE_NEED_REF_DIFFERS_FROM_APPROVED_PLAN')
    required = ('viewer_task','case_mode','concrete_input','constraints','options_considered','chosen_option','rejected_option',
                'decision_reason','source_status','evidence_refs','applicability_boundary','viewer_action','spoken_anchors')
    for key in required:
        if key not in pd or pd.get(key) in (None, '', []):
            errors.append(f'{sid}:PROFESSIONAL_DECISION_{key.upper()}_MISSING')
    if pd.get('case_mode') not in VALID_CASE_MODES:
        errors.append(f'{sid}:CASE_MODE_INVALID')
    if pd.get('source_status') not in VALID_SOURCE_STATUS:
        errors.append(f'{sid}:SOURCE_STATUS_INVALID')
    if len(_s(pd.get('viewer_task'))) < 8:
        errors.append(f'{sid}:VIEWER_TASK_TOO_GENERIC')
    if expected_need and _s(pd.get('viewer_task')) != _s(script.get('viewer_task') or pd.get('viewer_task')):
        errors.append(f'{sid}:VIEWER_TASK_NOT_ALIGNED_TO_SCRIPT')
    if len(_s(pd.get('concrete_input'))) < 20:
        errors.append(f'{sid}:CONCRETE_INPUT_TOO_GENERIC')
    constraints = pd.get('constraints') if isinstance(pd.get('constraints'), list) else []
    if len([x for x in constraints if len(_s(x)) >= 6]) < 2:
        errors.append(f'{sid}:TWO_CONCRETE_CONSTRAINTS_REQUIRED')
    options = pd.get('options_considered') if isinstance(pd.get('options_considered'), list) else []
    labels = [_s(x.get('option')) for x in options if isinstance(x, dict)]
    if len(options) < 2 or len(set(labels)) < 2 or any(len(_s(x.get('tradeoff'))) < 10 for x in options if isinstance(x, dict)):
        errors.append(f'{sid}:OPTIONS_NOT_COMPARABLE')
    elif any(_similarity(labels[i], labels[j]) > 0.72 for i in range(len(labels)) for j in range(i+1, len(labels))):
        errors.append(f'{sid}:OPTIONS_ARE_PARAPHRASES_NOT_DISTINCT_CHOICES')
    chosen, rejected = _s(pd.get('chosen_option')), _s(pd.get('rejected_option'))
    if chosen == rejected or chosen not in labels or rejected not in labels:
        errors.append(f'{sid}:DECISION_CHOICE_NOT_TRACEABLE')
    if len(_s(pd.get('decision_reason'))) < 20:
        errors.append(f'{sid}:DECISION_REASON_TOO_THIN')
    if len(_s(pd.get('applicability_boundary'))) < 15:
        errors.append(f'{sid}:APPLICABILITY_BOUNDARY_MISSING')
    if len(_s(pd.get('viewer_action'))) < 10:
        errors.append(f'{sid}:VIEWER_ACTION_NOT_ACTIONABLE')
    refs = pd.get('evidence_refs') if isinstance(pd.get('evidence_refs'), list) else []
    if not refs or not any(_s(x) for x in refs):
        errors.append(f'{sid}:EVIDENCE_REFS_MISSING')
    else:
        unknown = [x for x in refs if _s(x) not in known_evidence and not _s(x).startswith('SIMULATED:')]
        if unknown:
            errors.append(f'{sid}:EVIDENCE_REFS_NOT_RESOLVED:' + ','.join(map(str, unknown)))
        if need and _s(need.get('source_asset_id')) not in {_s(x) for x in refs}:
            errors.append(f'{sid}:SOURCE_NEED_ASSET_NOT_IN_EVIDENCE_REFS')
    mode, status = pd.get('case_mode'), pd.get('source_status')
    if mode == 'simulated' or status == 'SIMULATED':
        if mode != 'simulated' or status != 'SIMULATED' or not any(_s(x).startswith('SIMULATED:') for x in refs):
            errors.append(f'{sid}:SIMULATION_STATUS_OR_REFERENCE_INCONSISTENT')
        disclosure = pd.get('simulation_disclosure') if isinstance(pd.get('simulation_disclosure'), dict) else {}
        dseg = _find_segment(script, disclosure.get('segment_id'))
        dq = _s(disclosure.get('quote'))
        if not dseg or not dq or dq not in _s(dseg.get('text')) or not re.search(r'示意|模拟|假设情境|虚构情境', dq):
            errors.append(f'{sid}:SIMULATION_DISCLOSURE_NOT_SPOKEN')
    elif status in {'UNKNOWN', 'SIMULATED'}:
        errors.append(f'{sid}:UNSUPPORTED_REAL_CASE_STATUS')
    anchors = pd.get('spoken_anchors')
    for key in ('chosen_option','rejected_option','decision_reason','applicability_boundary'):
        errors.extend([f'{sid}:{e}' for e in _anchor_check(script, anchors, key, BODY_ROLES)])
    errors.extend([f'{sid}:{e}' for e in _anchor_check(script, anchors, 'viewer_action', ACTION_ROLES)])
    if isinstance(anchors, dict):
        for key, expected in [('chosen_option', chosen), ('rejected_option', rejected)]:
            q = _s((anchors.get(key) or {}).get('quote'))
            if q and expected and _similarity(q, expected) < 0.35:
                errors.append(f'{sid}:SPOKEN_OPTION_ANCHOR_DOES_NOT_NAME_{key.upper()}')
    return errors


def _selected_map(decision):
    rows = decision.get('selected', []) if isinstance(decision, dict) else []
    result = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        for key in ('id','plan_id','topic_id'):
            value = _s(row.get(key))
            if value:
                result[value] = row
    return result


def validate_plan(decision: dict, brief: dict, registry: dict) -> list[str]:
    errors = []
    selected = decision.get('selected', []) if isinstance(decision, dict) else []
    if not isinstance(selected, list) or not selected:
        return ['PLAN_SELECTED_MISSING']
    domain = _canonical_domain(brief)
    for row in selected:
        if not isinstance(row, dict):
            errors.append('PLAN_ROW_INVALID'); continue
        sid = _s(row.get('id') or row.get('plan_id') or row.get('topic_id') or 'UNKNOWN')
        ref = row.get('audience_need_ref')
        errors.extend([f'{sid}:{e}' for e in validate_need_ref(ref, registry, domain)])
        task = _s(row.get('viewer_task') or (row.get('expression_contract') or row.get('information_contract') or {}).get('viewer_task'))
        if len(task) < 8:
            errors.append(f'{sid}:PLAN_VIEWER_TASK_MISSING')
        proof = row.get('proof_plan') or (row.get('expression_contract') or row.get('information_contract') or {}).get('proof_plan')
        if not proof or (isinstance(proof, (list, dict, str)) and len(proof) == 0):
            errors.append(f'{sid}:PLAN_PROOF_PLAN_MISSING')
    return errors


def validate_batch(batch: dict, brief: dict, pack: dict, decision: dict, registry: dict, source_manifest: dict | None = None) -> list[str]:
    scripts = batch.get('scripts', []) if isinstance(batch, dict) else []
    if not isinstance(scripts, list) or not scripts:
        return ['BATCH_SCRIPTS_MISSING']
    errors = []
    ids = [_s(x.get('script_id') or x.get('id')) for x in scripts]
    if any(not x for x in ids) or len(ids) != len(set(ids)):
        errors.append('BATCH_SCRIPT_IDS_MISSING_OR_DUPLICATED')
    selected = _selected_map(decision)
    known = set(registry)
    for item in (pack.get('assets') or []):
        if isinstance(item, dict) and item.get('asset_id'):
            known.add(_s(item.get('asset_id')))
    for fact in brief.get('facts', []) if isinstance(brief.get('facts'), list) else []:
        for key in ('id','claim_id','fact_id'):
            if fact.get(key): known.add(_s(fact[key]))
    for resource in brief.get('production_resources', []) if isinstance(brief.get('production_resources'), list) else []:
        if resource.get('id'): known.add(_s(resource['id']))
    domain = _canonical_domain(brief)
    for script in scripts:
        sid = _s(script.get('script_id') or script.get('id'))
        plan_key = _s(script.get('plan_id') or script.get('topic_id') or script.get('id'))
        plan = selected.get(plan_key) or selected.get(_s(script.get('id')))
        if not plan:
            errors.append(f'{sid}:APPROVED_PLAN_ROW_NOT_FOUND')
            expected_need = None
        else:
            expected_need = plan.get('audience_need_ref')
            if not expected_need:
                errors.append(f'{sid}:APPROVED_PLAN_HAS_NO_AUDIENCE_NEED_REF')
            if _s((plan.get('viewer_task') or (plan.get('expression_contract') or plan.get('information_contract') or {}).get('viewer_task'))) != _s((script.get('professional_decision') or {}).get('viewer_task')):
                errors.append(f'{sid}:SCRIPT_VIEWER_TASK_DIFFERS_FROM_PLAN')
        errors.extend([f'{sid}:{e}' for e in validate_professional_decision(script, expected_need, registry, known, domain)])
    return errors


def _get_path(obj, path):
    cur = obj
    if not path:
        return None
    for part in str(path).split('.'):
        if isinstance(cur, list):
            try: cur = cur[int(part)]
            except (ValueError, IndexError): return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _decision_review_errors(script, item):
    sid = _s(script.get('script_id') or script.get('id'))
    errors = []
    need_review = item.get('source_need_review', {})
    ref = (script.get('professional_decision') or {}).get('audience_need_ref', {})
    if need_review.get('passed') is not True or _s(need_review.get('quote')) != _s(ref.get('source_quote')) or len(_s(need_review.get('reason'))) < 15:
        errors.append(f'{sid}:SOURCE_NEED_NOT_INDEPENDENTLY_CONFIRMED')
    dr = item.get('professional_decision_review', {})
    required_true = ('options_materially_distinct','choice_follows_constraints','reason_is_specific','boundary_is_valid','viewer_action_is_useful')
    if dr.get('passed') is not True or len(_s(dr.get('reason'))) < 20 or not _s(dr.get('quote')):
        errors.append(f'{sid}:PROFESSIONAL_DECISION_NOT_REVIEWED')
    for key in required_true:
        if dr.get(key) is not True:
            errors.append(f'{sid}:PROFESSIONAL_DECISION_REVIEW_FAILED:{key}')
    pd = script.get('professional_decision', {})
    anchor_quotes = {_s(x.get('quote')) for x in (pd.get('spoken_anchors') or {}).values() if isinstance(x, dict)}
    if _s(dr.get('quote')) not in anchor_quotes:
        errors.append(f'{sid}:PROFESSIONAL_DECISION_REVIEW_QUOTE_NOT_ANCHORED')
    return errors


def _score_anchor(script, dim, entry, illustration=False):
    sid = _s(script.get('script_id') or script.get('id'))
    errors = []
    quote = _s(entry.get('quote'))
    field = _s(entry.get('field'))
    seg_id = _s(entry.get('segment_id'))
    if field:
        value = _get_path(script, field)
        if not isinstance(value, str) or not quote or quote not in value:
            errors.append(f'{sid}:SCORE_QUOTE_NOT_IN_DECLARED_FIELD:{dim}')
    elif seg_id:
        seg = _find_segment(script, seg_id)
        if not seg or not quote or quote not in _s(seg.get('text')):
            errors.append(f'{sid}:SCORE_QUOTE_NOT_IN_SEGMENT:{dim}')
    else:
        errors.append(f'{sid}:SCORE_ANCHOR_FIELD_OR_SEGMENT_MISSING:{dim}')
        return errors
    if illustration:
        seg = _find_segment(script, seg_id) if seg_id else None
        role = _s(seg.get('role')).lower() if seg else ''
        allowed = {
            'audience_and_task': {'audience','professional_decision.viewer_task','professional_decision.audience_need_ref.source_quote'},
            'entry_and_click_reason': {'cover_main','cover_sub','title','cover'},
            'platform_native_expression': {'publish_description','platform_rationale','platform_note'},
        }
        role_map = {
            'first_8_seconds': {'hook','suspense'},
            'professional_judgment_and_payoff': {'judgment','value','decision'},
            'facts_evidence_and_rights': {'context','judgment','value','proof','evidence'},
            'calling_and_action': {'calling','cta'},
            'spoken_naturalness': {'hook','suspense','context','judgment','value','calling','cta'},
        }
        if dim in allowed and field not in allowed[dim]:
            errors.append(f'{sid}:SCORE_FIELD_NOT_RELEVANT_TO_DIMENSION:{dim}')
        if dim in role_map and role not in role_map[dim]:
            errors.append(f'{sid}:SCORE_SEGMENT_ROLE_NOT_RELEVANT_TO_DIMENSION:{dim}')
    return errors


def validate_ai_video_review(batch: dict, review: dict) -> list[str]:
    scripts = {_s(s.get('script_id') or s.get('id')): s for s in batch.get('scripts', [])}
    items = review.get('items', []) if isinstance(review, dict) else []
    if {_s(x.get('script_id')) for x in items if isinstance(x, dict)} != set(scripts):
        return ['AI_VIDEO_REVIEW_ITEMS_DO_NOT_MATCH_BATCH']
    errors = []
    for item in items:
        sid = _s(item.get('script_id')); script = scripts[sid]
        scores = item.get('scorecard', {})
        if set(scores) != AI_DIMS:
            errors.append(f'{sid}:AI_VIDEO_SCORE_DIMENSIONS_MISMATCH'); continue
        for dim, entry in scores.items():
            score = entry.get('score') if isinstance(entry, dict) else None
            if type(score) is not int or not 3 <= score <= 5:
                errors.append(f'{sid}:AI_VIDEO_DIMENSION_BELOW_3_OR_INVALID:{dim}')
            errors.extend(_score_anchor(script, dim, entry, False))
        errors.extend(_decision_review_errors(script, item))
    return errors


def validate_illustration_review(batch: dict, review: dict, batch_path: Path | None = None) -> list[str]:
    scripts = {_s(s.get('script_id') or s.get('id')): s for s in batch.get('scripts', [])}
    reviewer = review.get('reviewer', {}) if isinstance(review, dict) else {}
    errors = []
    if reviewer.get('independent') is not True or reviewer.get('same_model_role') is not False or reviewer.get('mode') not in ('human','separate_model') or not _s(reviewer.get('identity')) or not _s(reviewer.get('blind_packet_file')) or not re.fullmatch(r'[a-f0-9]{64}', _s(reviewer.get('blind_packet_sha256'))) or not _s(reviewer.get('review_evidence_file')) or not re.fullmatch(r'[a-f0-9]{64}', _s(reviewer.get('review_evidence_sha256'))):
        errors.append('ILLUSTRATION_REVIEWER_NOT_INDEPENDENTLY_IDENTIFIED')
    if batch_path and review.get('batch_sha256') != _sha(batch_path):
        errors.append('ILLUSTRATION_REVIEW_NOT_BOUND_TO_EXACT_BATCH_BYTES')
    if review.get('blind_packet_sha256') != reviewer.get('blind_packet_sha256'):
        errors.append('ILLUSTRATION_BLIND_PACKET_SHA_MISMATCH')
    items = review.get('items', []) if isinstance(review, dict) else []
    if {_s(x.get('script_id')) for x in items if isinstance(x, dict)} != set(scripts):
        return errors + ['ILLUSTRATION_REVIEW_ITEMS_DO_NOT_MATCH_BATCH']
    for item in items:
        sid = _s(item.get('script_id')); script = scripts[sid]
        scores = item.get('scores', {})
        if set(scores) != ILL_DIMS:
            errors.append(f'{sid}:ILLUSTRATION_SCORE_DIMENSIONS_MISMATCH'); continue
        total = 0.0
        for dim, weight in ILL_WEIGHTS.items():
            entry = scores[dim]
            score = entry.get('score') if isinstance(entry, dict) else None
            if type(score) is not int or not 3 <= score <= 5:
                errors.append(f'{sid}:ILLUSTRATION_DIMENSION_BELOW_3_OR_INVALID:{dim}')
            else:
                total += score * weight / 5
            if not _s(entry.get('reason')) or len(_s(entry.get('reason'))) < 12:
                errors.append(f'{sid}:ILLUSTRATION_SCORE_REASON_TOO_THIN:{dim}')
            errors.extend(_score_anchor(script, dim, entry, True))
        if total < 70:
            errors.append(f'{sid}:ILLUSTRATION_TOTAL_BELOW_70:{round(total,1)}')
        gates = item.get('hard_gates', {})
        required = ('lock_fields','facts','rights','promise_payoff','platform_fit','professional_value','script_04_05_mapping')
        for gate in required:
            if gates.get(gate) is not True:
                errors.append(f'{sid}:ILLUSTRATION_HARD_GATE_FAILED:{gate}')
        if item.get('decision') not in ('PASS','REVISE','FAIL','VALIDATION_PENDING','PUBLISH_HOLD'):
            errors.append(f'{sid}:ILLUSTRATION_DECISION_MISSING')
        errors.extend(_decision_review_errors(script, item))
    return errors


def verify_external_evidence(review: dict, run_dir: Path) -> list[str]:
    errors = []
    # Reviewer identity is declared; retain both blind packet and reviewer work evidence.
    reviewer = review.get('reviewer', {}) if isinstance(review, dict) else {}
    for label, file_key, sha_key in [('REVIEW_BLIND_PACKET','blind_packet_file','blind_packet_sha256'),('REVIEW_EVIDENCE','review_evidence_file','review_evidence_sha256')]:
        rel, expected = _s(reviewer.get(file_key)), _s(reviewer.get(sha_key))
        if not rel or not re.fullmatch(r'[a-f0-9]{64}', expected):
            errors.append(label + '_MISSING_FILE_OR_SHA')
        else:
            path = (Path(run_dir) / rel).resolve()
            if not path.is_relative_to(Path(run_dir).resolve()) or not path.is_file():
                errors.append(label + '_FILE_MISSING_OR_UNSAFE')
            elif _sha(path) != expected:
                errors.append(label + '_SHA_MISMATCH')
    # Batch-level reader tests also need an evidence file and byte-matching SHA.
    for field in ('target_user_blind_read','non_author_read_test'):
        record = review.get(field, {}) if isinstance(review, dict) else {}
        if isinstance(record, dict) and record.get('status') == 'PASS':
            rel, expected = _s(record.get('evidence_file')), _s(record.get('evidence_sha256'))
            if not rel or not re.fullmatch(r'[a-f0-9]{64}', expected):
                errors.append(field.upper() + '_PASS_WITHOUT_FILE_AND_SHA')
            else:
                path = (Path(run_dir) / rel).resolve()
                if not path.is_relative_to(Path(run_dir).resolve()) or not path.is_file():
                    errors.append(field.upper() + '_EVIDENCE_FILE_MISSING_OR_UNSAFE')
                elif _sha(path) != expected:
                    errors.append(field.upper() + '_EVIDENCE_SHA_MISMATCH')
    items = review.get('items', []) if isinstance(review, dict) else []
    for item in items:
        sid = _s(item.get('script_id'))
        for field in ('human_voice_test','blind_test'):
            record = item.get(field, {})
            if not isinstance(record, dict) or record.get('status') != 'PASS':
                continue
            rel, expected = _s(record.get('evidence_file')), _s(record.get('evidence_sha256'))
            if not rel or not re.fullmatch(r'[a-f0-9]{64}', expected):
                errors.append(f'{sid}:{field.upper()}_PASS_WITHOUT_FILE_AND_SHA'); continue
            path = (Path(run_dir) / rel).resolve()
            if not path.is_relative_to(Path(run_dir).resolve()) or not path.is_file():
                errors.append(f'{sid}:{field.upper()}_EVIDENCE_FILE_MISSING_OR_UNSAFE'); continue
            if _sha(path) != expected:
                errors.append(f'{sid}:{field.upper()}_EVIDENCE_SHA_MISMATCH')
    return errors
