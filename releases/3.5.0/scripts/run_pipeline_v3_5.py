#!/usr/bin/env python3
"""v3.5.0 sole entrypoint: v3.4.2 source/lock pipeline + content payoff gate."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import run_pipeline_v3_4 as base
from content_quality_gate_v350 import (
    validate_plan_quality, validate_batch_quality, validate_review_quality,
)


def _latest_batch(run: Path) -> Path:
    files = list(run.glob("batch-v*.json"))
    if not files:
        raise ValueError("draft stage did not create a versioned batch JSON")
    def version(path: Path) -> int:
        import re
        m = re.search(r"v(\d+)", path.stem)
        return int(m.group(1)) if m else -1
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


def _run_regression() -> None:
    test_dir = ROOT / "tests"
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", "test_content_quality_v350.py"]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode:
        raise SystemExit("v3.5.0 regression gate failed:\n" + result.stdout + result.stderr)


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


def main() -> None:
    args = base._args()
    _run_regression()
    if args.stage == "intake":
        base.main()
        return

    run, brief, domain, pack, registry = _load_context(args)
    decision_path = run / "decision.json"

    if args.stage == "plan":
        if not args.input:
            raise ValueError("plan requires --input decision JSON")
        proposed = base._read(Path(args.input))
        errors = validate_plan_quality(proposed, registry, domain)
        if errors:
            raise SystemExit("v3.5.0 plan-value gate blocked:\n- " + "\n- ".join(errors))
        base.main()
        sealed = base._read(decision_path)
        errors = validate_plan_quality(sealed, registry, domain)
        if errors:
            raise SystemExit("v3.5.0 sealed plan failed:\n- " + "\n- ".join(errors))
        return

    if args.stage == "draft":
        if not decision_path.is_file():
            raise ValueError("draft requires run/decision.json")
        decision = base._read(decision_path)
        errors = validate_plan_quality(decision, registry, domain)
        if errors:
            raise SystemExit("v3.5.0 draft blocked by plan-value gate:\n- " + "\n- ".join(errors))
        base.main()
        batch_path = _latest_batch(run)
        batch = base._read(batch_path)
        errors = validate_batch_quality(batch, decision, registry, domain)
        if errors:
            raise SystemExit("v3.5.0 draft failed worked-example/value gate:\n- " + "\n- ".join(errors))
        return

    if args.stage in ("validate", "export"):
        if not args.input:
            raise ValueError("validate/export requires --input batch JSON")
        batch_path = Path(args.input).resolve()
        batch = base._read(batch_path)
        decision = base._read(decision_path) if decision_path.is_file() else {}
        errors = validate_batch_quality(batch, decision, registry, domain)
        review_path = _review_path(args, run, domain)
        review = base._read(review_path)
        errors.extend(validate_review_quality(batch, review, domain))
        if errors:
            raise SystemExit("v3.5.0 pre-export content-value gate blocked:\n- " + "\n- ".join(errors))
        base.main()
        return

    raise ValueError("unsupported stage: " + str(args.stage))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print("v3.5.0 pipeline error: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
