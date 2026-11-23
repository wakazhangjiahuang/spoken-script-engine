# spoken-script-engine v3.4.3

**Release type:** source-bound quality gate + pinned-source alignment.

## Why this release exists
The target audiences, core needs, current guidance and examples already existed. The failure was in the runtime path: some current guidance was only manifest-checked or staged by filename, retired illustration examples could remain in retrieval, and the professional-decision gate checked field presence rather than binding the source need and spoken decision to the approved plan.

## Runtime changes
- Full AI-video V4.1 business guidance and the 2026-11-23 production guide enter the actual asset pack.
- Full illustration V2.0 guidance and Cover Title Guide V4 enter the actual asset pack.
- Retired 2026-11-18 illustration platform examples are excluded from current positive retrieval.
- Every plan binds an exact source asset, locator and verbatim need quote; every script reuses that exact reference.
- Every professional decision includes concrete input, constraints, materially distinct alternatives, chosen/rejected option, rationale, applicability boundary, next action and five exact spoken anchors.
- Simulated cases require spoken disclosure and a SIMULATED evidence ID.
- Illustration review requires field/segment-specific score anchors, 3/5 minimum per dimension, a 70-point weighted floor and non-compensatory hard gates.
- Reviewer identity, mode, blind packet and review evidence are recorded; same-model self-review cannot pass.
- AI video continues to use the V4.1 formal validator.
- `run_pipeline_v3_4.py` is the only supported stage entrypoint.

## Verification
9 source/decision tests passed; 5 review/score-gate tests passed; Python syntax compilation passed. These tests verify deterministic contracts only. Private-asset end-to-end execution, human voice tests, target-user blind reads, rights checks and platform outcomes remain `NOT_RUN` until actually performed.

## Privacy
Public release includes generic validators, schemas and redacted rules only. Private source documents, original Word/XLSX files, lock baselines and client materials remain in the private plugin archive.
