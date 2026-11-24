# Inactive candidate: fresh intake and review-copy integrity

This patch is based on the generic runtime code shipped in plugin package 3.6.3 (core 3.6.1). It is a review artifact, not an active release. It does not update the registry, installed plugin, Skill version, or audience/sharing settings.

## Behavior

- Fresh intake reads the structured brief from --input and preserves --request as raw text.
- Core intake owns creation of a new run directory; alias reports are written after initialization.
- AI video asset delegation captures its original callable before route replacement, preventing wrapper recursion.
- Review packets contain an exact projection of the actual delivery. Missing, omitted, or altered copy blocks the review. prepare_review.py --phase blind builds this packet.
- Current domain guidance is selected by active manifest source identities, not an obsolete domains/ path prefix. Missing required guidance is rejected before content review.
- Optional topic_competitions binds a separate entry competition to each selected plan. Legacy batch-scoped competitions remain supported; ambiguous or incomplete coverage is rejected.

## Apply and validate

Apply runtime-review-fix.patch at the root of a complete private 3.6.3 Skill copy using git apply --check first. Tests require the complete existing runtime and private domain assets. These private files are not included here. The public layered source tree is not identical to the assembled private package; do not apply the patch blindly to the repository root.

The two new test modules exercise three fresh-process CLI intake routes and review packet integrity, projection, schema and per-topic binding. The original acceptance fixture now supplies actual copy; this fixture update does not represent a real independent review.

The local assembled candidate passed 65 checks: the existing six suites (49 checks) and the added two suites (16 checks). These results cover structural behavior and bundled source loading. They do not certify full planning, drafting, workbook delivery, human review, audience response or marketing outcomes.

## Remaining limitations

Two deliberate synthetic semantic probes remain unresolved: equivalent customer decisions phrased differently can pass the entry validator; and incorrect positive labels for a generic opening can pass the structural review module while the overall result remains VALIDATION_PENDING. No external reviewer was actually invoked in these probes.

A standalone A-mode planner, calibrated editorial judge, controlled final delivery and new-versus-old content trial remain unimplemented. No claim is made that these patches solve topic quality or the whole knowing-versus-doing problem.

## Follow-up: knowledge handoff

The original PR description records the initial 63-check candidate. A subsequent projection-boundary probe extracted both current illustration guides from the complete private package but found neither in the content-review domain_standard field. The source-ID selection fix now hands off both, with two additional checks (65 total). The probe stubs only upstream provenance to isolate this projection boundary; it does not invoke a model or certify semantic use of the guidance. Private source text is excluded from the public results.
