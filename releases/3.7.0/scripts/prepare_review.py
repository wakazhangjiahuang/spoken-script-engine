#!/usr/bin/env python3
"""Prepare a blind editorial view with v3.6.0 quote-bound marketing review contract."""
import json
import argparse
import hashlib
from pathlib import Path

REMOVED = {"selection_scores", "内部评分", "评分简评", "historical_score_not_current"}


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in REMOVED}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def review_guidance(pack):
    manifest = pack.get('domain_asset_manifest', {})
    required = set(manifest.get('required_source_asset_ids') or manifest.get('must_read_source_asset_ids') or [])
    guides = pack.get('must_read_guidance', {})
    selected = {k: v for k, v in guides.items()
                if k.startswith('domains/') or v.get('source_asset_id') in required}
    missing = required - {v.get('source_asset_id') for v in selected.values()}
    if missing:
        raise ValueError('current domain guidance missing from review input: ' + ','.join(sorted(missing)))
    return selected


def prepare(run, batch, phase="content", content_review=None):
    run = Path(run)
    batch = Path(batch)
    root = Path(__file__).resolve().parents[1]
    from execution_contract import provenance
    errors = provenance(run, batch)
    if errors:
        raise ValueError("Cannot review a structurally rejected or unbound draft: " + "; ".join(errors))

    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    from surface_contract import delivery_packet
    b = read(batch)
    brief = read(run / "brief.json")
    pack = read(run / "asset-pack.json")
    source_manifest = read(run / "source-manifest.json")
    marketing_schema = read(root / "schemas" / "marketing-review-v360.schema.json")
    source_schema = read(root / "schemas" / "source-inventory-v360.schema.json")
    if phase == 'blind':
        from acceptance_contract_v361 import visible_review_copy
        copies = [visible_review_copy(s) for s in b['scripts']]
        return {'batch_sha256': sha(batch), 'script_ids': [s['script_id'] for s in copies], 'actual_copy': copies}
    data = {
        "review_input_version": "3.6.0",
        "phase": phase,
        "blinding": {
            "producer_selection_scores": "REMOVED",
            "producer_payoff_explanations": "HIDDEN_UNTIL_CONTENT_JUDGEMENT",
            "review_scope": "Independent editorial review, not target-user or published performance"
        },
        "bindings": {
            "batch_sha256": sha(batch),
            "decision_sha256": sha(run / "decision.json"),
            "asset_pack_sha256": sha(run / "asset-pack.json")
        },
        "actual_request": (run / source_manifest["sources"][0]["stored_path"]).read_text(encoding="utf-8"),
        "production_resources": brief["production_resources"],
        "source_inventory": brief.get("source_inventory", {}),
        "deliverables": [delivery_packet(script) for script in b["scripts"]],
        "source_manifest": source_manifest,
        "source_directory": str((run / "sources").resolve()),
        "rubric": pack["rubric"],
        "domain_standard": review_guidance(pack),
        "marketing_review_contract": marketing_schema,
        "source_inventory_contract": source_schema,
        "marketing_review_instructions": [
            "逐篇判断，不得用平均分补偿短板。",
            "每项结论必须引用实际交付台词；不得用备注、JSON字段或模型自述代替台词。",
            "检查用户相关性、点击链路、3–8秒新增信息、标题承诺与正文兑现、内容模式匹配、能力放大与人机边界、Calling痒点升维和来源保真。",
            "评审者必须与生成者独立；同一模型切换角色不算独立评审。",
            "没有真实证据的能力、客户、订单、效率、互动数据或传播结果必须降级主张或阻断。",
            "真人试读、目标用户盲读、权利授权和平台结果未执行时，外部验证保持NOT_RUN/VALIDATION_PENDING。"
        ],
        "external_validation_default": {
            "human_voice_test": "NOT_RUN",
            "target_user_blind_read": "NOT_RUN",
            "rights_and_permissions": "NOT_RUN",
            "platform_outcome": "NOT_RUN"
        }
    }
    if phase == "fidelity":
        if not content_review:
            raise ValueError("record the visible-delivery content judgement before revealing the production plan")
        review = read(content_review)
        if review.get("batch_sha256") != sha(batch) or review.get("reviewer", {}).get("independent") is not True:
            raise ValueError("content judgement is not independently bound to this batch")
        decisions = review.get("content_decisions", [])
        if {x.get("script_id") for x in decisions} != {s["id"] for s in b["scripts"]} or any(x.get("verdict") != "DRAFT_FOR_USER_REVIEW" for x in decisions):
            raise ValueError("rewrite rejected content before formula-fidelity review")
        data.update({
            "content_review_sha256": sha(content_review),
            "brief": brief,
            "plan": clean(read(run / "decision.json")),
            "asset_pack": clean(pack),
            "batch": clean(b)
        })
    elif phase != "content":
        raise ValueError("unknown review phase")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--batch", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--phase", choices=["blind", "content", "fidelity"], default="content")
    parser.add_argument("--content-review", type=Path)
    args = parser.parse_args()
    try:
        payload = prepare(args.run, args.batch, args.phase, args.content_review)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"review_input": str(args.output), "producer_scores": "REMOVED", "original_bindings": "PRESERVED", "marketing_review_contract": "v3.6.0"}))
    except ValueError as exc:
        parser.exit(2, str(exc) + "\n")
