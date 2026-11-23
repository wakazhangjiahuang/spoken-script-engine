# spoken-script-engine v3.5.0 public overlay

This release is a targeted content-quality overlay on the existing v3.4.3 engine. It does not recreate the audience taxonomy, topic libraries, AI-video V4.1 content standard, illustration V2.0 standard, title governance or private source workbooks.

## v3.5.0 changes
- Requires a plan-level content contract binding the existing audience need to one shared task, why-now, click reason, promised payoff, proof plan and three materially different entry candidates.
- Requires a spoken worked example: concrete input, decision criterion, before/after state, observable delta and transferable rule, with verbatim body anchors.
- Requires a Calling value exchange: one action, the reason to take it and the user reward.
- Sets non-compensatory floors: core marketing/professional-value dimensions >=4/5; other dimensions >=3/5. Existing domain weights and the 70-point minimum remain unchanged; 80 remains the internal target.
- Adds deterministic checks and regression tests. The private plugin separately includes the exact six prior low-quality scripts as negative-only fixtures; user materials are not published here.

## Files
- `scripts/content_quality_gate_v350.py`: plan, body-proof, first-eight and Calling gate.
- `scripts/run_pipeline_v3_5.py`: sole v3.5.0 entrypoint; wraps the existing v3.4.3 source/lock pipeline.
- `references/v3.5.0-runtime-quality-overlay.md`: operational contract.
- `schemas/content-proof-v3.5.0.schema.json`: worked-example schema.
- `assets/qa/quality-gate-v3.5.0.json`: non-compensatory thresholds.
- `tests/test_content_quality_v350.py`: public synthetic regression tests.

## Runtime dependency
The overlay expects the existing v3.4.3 base modules and current private domain assets to be installed alongside it. Private Word/XLSX files, original lock workbook, client materials and raw negative regression examples are not included.

## Validation boundary
Automated checks verify source binding, structural completeness, verbatim anchors and score floors. They do not prove that a real audience will click, watch, save or buy. Human voice tests, target-user blind reads, rights checks and publication outcomes must remain `NOT_RUN` until actual evidence is recorded.
