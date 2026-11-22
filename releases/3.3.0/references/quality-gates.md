# Runtime Quality Gates — 3.3.0

A rule being present is not proof that the execution used it. Each stage must produce an inspectable artifact.

1. Intake: capture task, domain, platforms, output mode, source files, locks, facts and permissions.
2. Retrieval: read the repository registry; pin the current overlay commit; load only entrypoint-selected assets; verify hashes.
3. Conflict resolution: record version, source role, precedence and the reason for each decision.
4. Domain routing: keep AI-video and illustration facts, samples and audiences isolated.
5. Sample governance: classify BENCHMARK / DERIVED_SCRIPT / CANDIDATE / NEGATIVE / HISTORICAL before retrieval.
6. Lock manifest: extract locked fields by source workbook, sheet, Script_ID and cell; record source SHA.
7. Topic gate: one shared viewer task, one primary question and one deliverable viewer payoff.
8. Entry competition: compare at least three materially different content mechanisms; reject all if none is supported.
9. Expression contract: bind audience, click reason, promise, proof, professional judgement and transferable value.
10. Evidence map: every material claim has a Claim_ID, source, status, scope and permission.
11. Draft: generate only editable fields; do not change the approved audience, angle, evidence boundary or locked text.
12. Blind content review: reviewer sees the brief and draft, not the generator's scores or rationale.
13. Fidelity review: separately verify source fidelity, facts, permissions, lock fields and script-to-shot mapping.
14. Score and hard gates: score each script; do not average across the batch. A failed hard gate cannot be compensated by a high score.
15. Production routing: illustration uses both 04 and 05; AI-video uses 04, 05 or combined according to the selected mode.
16. Export and round-trip: reopen the workbook and verify sheets, rows, IDs, locked values, spoken text, shot duration and mappings.
17. Independent validation: human read, target-user blind read, evidence/rights audit and platform data are separate states.
18. Release: PASS / REVISE / FAIL / VALIDATION_PENDING / PUBLISH_HOLD. Record failure, root cause, minimal repair and regression result.

## Independence
A model reviewing its own output in the same context is not an independent reviewer. Use a human, isolated thread or separate reviewer; otherwise mark NOT_RUN. Do not expose hidden chain-of-thought. Record only candidates, chosen/rejected option, evidence, main objection, confidence and unresolved risk.

## Scoring
Illustration uses an eight-dimension 100-point editorial rubric: audience/task 15; entry/click reason 15; first 8 seconds 15; professional judgement/payoff 20; facts/evidence/rights 15; platform-native expression 10; CTA/action 5; spoken naturalness 5. A 70–80 score is an editorial candidate band, not a platform threshold or market proof. Hard gates remain non-compensatory.
