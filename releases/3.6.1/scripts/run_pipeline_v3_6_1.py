#!/usr/bin/env python3
"""v3.6.1 sole entrypoint: v3.5.1 gates + source-first mode selection + marketing review."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import run_pipeline_v3_4 as base
from content_quality_gate_v350 import validate_plan_quality, validate_batch_quality, validate_review_quality
from formal_v41_gate_v351 import validate_formal_v41
from marketing_quality_gate_v361 import (
    validate_benchmark_catalog,
    validate_source_inventory,
    validate_plan_marketing,
    validate_script_marketing,
    validate_marketing_review,
    release_validation_status,
)
from validate_v41 import validate as validate_v41_review

CATALOG_PATH = ROOT / "references" / "benchmark-governance-v360.json"

def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def _catalog():
    if not CATALOG_PATH.is_file():
        raise FileNotFoundError("v3.6.1 benchmark governance catalog missing: " + str(CATALOG_PATH))
    data = _read(CATALOG_PATH)
    errors = validate_benchmark_catalog(data)
    if errors:
        raise SystemExit("v3.6.1 benchmark catalog invalid:\n- " + "\n- ".join(errors))
    return data

def _latest_batch(run: Path) -> Path:
    files = list(run.glob("batch-v*.json"))
    if not files:
        raise ValueError("draft stage did not create a versioned batch JSON")
    import re
    def version(path):
        match = re.search(r"v(\d+)", path.stem)
        return int(match.group(1)) if match else -1
    return sorted(files, key=version)[-1]

def _review_path(args, run: Path, domain: str) -> Path:
    if domain == "ai_video":
        if not args.v41_review:
            raise ValueError("AI video requires --v41-review")
        return Path(args.v41_review).resolve()
    if domain == "illustration":
        path = run / "illustration-review.json"
        if not path.is_file():
            raise ValueError("illustration requires run/illustration-review.json")
        return path
    if args.review:
        return Path(args.review).resolve()
    raise ValueError("review JSON is required")

def _run_regression():
    test_dir = ROOT / "tests"
    patterns = (
        "test_content_quality_v350.py",
        "test_formal_v41_gate_v351.py",
        "test_marketing_quality_gate_v361.py",
        "test_release_alignment_v361.py",
    )
    for pattern in patterns:
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", pattern]
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if result.returncode:
            raise SystemExit("v3.6.1 regression gate failed [" + pattern + "]:\n" + result.stdout + result.stderr)

def _load_context(args):
    run = Path(args.run).resolve()
    brief_path = run / "brief.json"
    brief = base._read(brief_path) if brief_path.is_file() else {}
    if not brief and args.request and Path(args.request).is_file():
        request = base._read(Path(args.request))
        brief = request.get("brief", request) if isinstance(request, dict) else {}
    domain = base._domain(brief)
    base.ensure_asset_aliases(ROOT, run, domain=domain)
    base._patch_asset_routes()
    pack, registry = base._context(run, brief)
    return run, brief, domain, pack, registry

def _write_release_status(run: Path, review: dict):
    status = release_validation_status(review)
    payload = {
        "engine_version": "3.6.0",
        "editorial_review": "PASSED" if review.get("marketing_checks") else "NOT_RUN",
        "external_validation_status": status,
        "external_validation": review.get("external_validation", {}),
        "rule": "A successful code/independent editorial review does not certify human voice, target-user response, rights or platform performance."
    }
    (run / "v3.6.1-validation-status.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    args = base._args()
    _run_regression()
    catalog = _catalog()
    if args.stage == "intake":
        base.main()
        run = Path(args.run).resolve()
        brief_path = run / "brief.json"
        if not brief_path.is_file():
            raise ValueError("intake did not create run/brief.json")
        errors = validate_source_inventory(base._read(brief_path))
        if errors:
            raise SystemExit("v3.6.1 intake source-first gate blocked:\n- " + "\n- ".join(errors))
        return

    run, brief, domain, pack, registry = _load_context(args)
    decision_path = run / "decision.json"

    if args.stage == "plan":
        if not args.input:
            raise ValueError("plan requires --input decision JSON")
        proposed = base._read(Path(args.input))
        errors = validate_plan_quality(proposed, registry, domain)
        errors.extend(validate_plan_marketing(proposed, brief, domain, catalog))
        if errors:
            raise SystemExit("v3.6.1 plan/source/mode gate blocked:\n- " + "\n- ".join(errors))
        base.main()
        sealed = base._read(decision_path)
        errors = validate_plan_quality(sealed, registry, domain)
        errors.extend(validate_plan_marketing(sealed, brief, domain, catalog))
        if errors:
            raise SystemExit("v3.6.1 sealed plan failed:\n- " + "\n- ".join(errors))
        return

    if args.stage == "draft":
        if not decision_path.is_file():
            raise ValueError("draft requires run/decision.json")
        decision = base._read(decision_path)
        errors = validate_plan_quality(decision, registry, domain)
        errors.extend(validate_plan_marketing(decision, brief, domain, catalog))
        if errors:
            raise SystemExit("v3.6.1 draft blocked by plan/source/mode gate:\n- " + "\n- ".join(errors))
        base.main()
        batch_path = _latest_batch(run)
        batch = base._read(batch_path)
        errors = validate_batch_quality(batch, decision, registry, domain)
        errors.extend(validate_script_marketing(batch, decision, brief, domain, catalog))
        if errors:
            raise SystemExit("v3.6.1 draft failed source-fidelity/marketing gate:\n- " + "\n- ".join(errors))
        return

    if args.stage in ("validate", "export"):
        if not args.input:
            raise ValueError("validate/export requires --input batch JSON")
        batch_path = Path(args.input).resolve()
        batch = base._read(batch_path)
        decision = base._read(decision_path) if decision_path.is_file() else {}
        errors = validate_batch_quality(batch, decision, registry, domain)
        errors.extend(validate_script_marketing(batch, decision, brief, domain, catalog))
        review_path = _review_path(args, run, domain)
        review = base._read(review_path)
        if domain == "ai_video":
            formal_errors, _ = validate_formal_v41(batch, review, batch_path, validate_v41_review, require_full=bool(args.require_v41_full_validation))
            errors.extend(formal_errors)
        errors.extend(validate_review_quality(batch, review, domain))
        errors.extend(validate_marketing_review(batch, decision, review, brief, domain))
        if errors:
            raise SystemExit("v3.6.1 pre-export marketing/source/independent-review gate blocked:\n- " + "\n- ".join(errors))
        _write_release_status(run, review)
        base.main()
        return

    raise ValueError("unsupported stage: " + str(args.stage))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print("v3.6.1 pipeline error: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
