# v3.5.0 upgrade summary

## What changed
- Reuses existing audience, need and topic assets; no new audience taxonomy or topic expansion.
- Adds a plan-level content contract: shared task, why-now, click reason, promised payoff, proof plan, three different entry candidates and counterevidence.
- Adds a body-level worked example: concrete input, decision criterion, before/after state, observable delta and transferable rule, each with verbatim spoken anchors.
- Adds a Calling value-exchange contract: one action, reason and user reward.
- Raises core marketing/professional-value review dimensions to 4/5; non-core dimensions remain 3/5; total-score averaging cannot compensate for a failed core gate.
- Adds 13 regression tests and preserves the previous six low-quality scripts as private negative-only fixtures.
- Makes `scripts/run_pipeline_v3_5.py` the sole execution entrypoint while retaining the existing V4.1 and V2.0 validators, lock fields and output contracts.

## Preserved
- AI video V4.1 content standard and 2026-11-23 production handbook.
- Illustration V2.0 content standard, BENCHMARK immutability, 18-script/72-cell lock contract and six-sheet workbook.
- Shared Cover Title Guide V4.
- Existing source binding, source evidence, H3/04/05 execution and external-validation status rules.

## Validation status
- Local content-quality regression suite: 13 tests.
- Six previous scripts: all rejected by the new content gates.
- Live plugin pipeline end-to-end: pending installation of this package update and execution against a fresh task run directory.
- External human review, target-user blind read and platform outcome: not run; never represented as PASS.
