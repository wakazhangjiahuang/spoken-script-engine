#!/usr/bin/env python3
"""v3.6.1 sole entrypoint: v3.6.0 domain gates + 15-point evidence closure."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import run_pipeline_v3_6 as v360
from acceptance_contract_v361 import (
    validate_source_inventory,
    validate_plan_stage,
    validate_draft_stage,
    validate_review,
)


def _read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_v361_regression():
    test_dir = ROOT / "tests"
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", "test_acceptance_contract_v361.py", "-v"]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("v3.6.1 four-layer regression failed:\n" + result.stdout + result.stderr)


def _save_report(run: Path, report: dict, stage: str):
    payload = {
        "engine_version": "3.6.1",
        "stage": stage,
        "status": report.get("status", "PASS" if report.get("passed") else "BLOCKED"),
        "passed": report.get("passed", False),
        "errors": report.get("errors", []),
        "criteria_per_script": report.get("criteria_per_script", 15),
        "criteria_total": report.get("criteria_total"),
        "average_score_used_for_release": False,
        "external_validation_status": report.get("external_validation_status", "NOT_RUN"),
        "reviewer_attestation_status": report.get("reviewer_attestation_status", "NOT_RUN"),
        "release_rule": "Any failed criterion blocks; any missing human/user/platform evidence remains VALIDATION_PENDING. Average scores never compensate for failed criteria."
    }
    (run / "v3.6.1-validation-status.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _call_v360(run: Path, stage: str):
    try:
        return v360.main()
    except SystemExit as exc:
        detail = str(exc) if str(exc) else "legacy v3.6.0/domain gate returned non-zero"
        _save_report(run, {"passed": False, "status": "BLOCKED", "errors": ["V3_6_0_OR_DOMAIN_GATE_FAILED:" + detail]}, stage)
        raise


def main():
    args = v360.base._args()
    _run_v361_regression()
    run = Path(args.run).resolve()

    if args.stage == "intake":
        _call_v360(run, "intake")
        brief = _read(run / "brief.json")
        errors = validate_source_inventory(brief, run)
        report = {"passed": not errors, "status": "PASS" if not errors else "BLOCKED", "errors": errors}
        _save_report(run, report, "intake")
        if errors:
            raise SystemExit("v3.6.1 source-evidence intake gate blocked:\n- " + "\n- ".join(errors))
        return

    run, brief, domain, pack, registry = v360._load_context(args)
    decision_path = run / "decision.json"

    if args.stage == "plan":
        if not args.input:
            raise ValueError("plan requires --input decision JSON")
        proposed = _read(Path(args.input))
        errors = validate_plan_stage(proposed, brief, domain, run)
        if errors:
            raise SystemExit("v3.6.1 plan competition/source gate blocked:\n- " + "\n- ".join(errors))
        _call_v360(run, "plan")
        sealed = _read(decision_path)
        errors = validate_plan_stage(sealed, brief, domain, run)
        report = {"passed": not errors, "status": "PASS" if not errors else "BLOCKED", "errors": errors}
        _save_report(run, report, "plan")
        if errors:
            raise SystemExit("v3.6.1 sealed plan gate blocked:\n- " + "\n- ".join(errors))
        return

    if args.stage == "draft":
        if not decision_path.is_file():
            raise ValueError("draft requires sealed run/decision.json")
        decision = _read(decision_path)
        plan_errors = validate_plan_stage(decision, brief, domain, run)
        if plan_errors:
            raise SystemExit("v3.6.1 draft blocked by decision/source gate:\n- " + "\n- ".join(plan_errors))
        _call_v360(run, "draft")
        batch_path = v360._latest_batch(run)
        batch = _read(batch_path)
        errors = validate_draft_stage(batch, decision, brief, domain, run)
        report = {"passed": not errors, "status": "PASS" if not errors else "BLOCKED", "errors": errors}
        _save_report(run, report, "draft")
        if errors:
            raise SystemExit("v3.6.1 generated delivery gate blocked:\n- " + "\n- ".join(errors))
        return

    if args.stage in ("validate", "export"):
        if not args.input:
            raise ValueError("validate/export requires --input batch JSON")
        if not decision_path.is_file():
            raise ValueError("validate/export requires sealed run/decision.json")
        batch_path = Path(args.input).resolve()
        batch = _read(batch_path)
        decision = _read(decision_path)
        review_path = v360._review_path(args, run, domain)
        review = _read(review_path)
        report = validate_review(batch, decision, brief, review, run, batch_path)
        _save_report(run, report, args.stage)
        if report["status"] == "BLOCKED":
            raise SystemExit("v3.6.1 15-point non-compensatory acceptance blocked:\n- " + "\n- ".join(report["errors"]))
        # VALIDATION_PENDING permits a clearly labelled draft export, never a publish-ready claim.
        _call_v360(run, args.stage)
        _save_report(run, report, args.stage)
        return

    raise ValueError("unsupported stage: " + str(args.stage))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print("v3.6.1 pipeline error: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
