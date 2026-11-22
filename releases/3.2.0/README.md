# Release 3.2.0｜V4.1 decision and QA upgrade

## Scope
Public, redacted release notes and reusable contracts for the private spoken-script-engine 3.2.0 update. The original V4.1 Word guide, team workbook and customer/source materials are not included.

## Added contracts
- Topic Gate 1.2 and Expression Contract 2.0.
- V4.1 Decision Gateway roles and structured decision record.
- Eight-dimension AI-video editorial scorecard and nine hard gates.
- Per-script batch acceptance with Topic_ID / Script_ID count separation.
- Failure-record schema and regression tests.

## Scoring
- 85–100: strong candidate.
- 75–84: publish candidate.
- 70–74: revise.
- Below 70: rewrite.
- Any hard-gate failure blocks regardless of score.
- A score is an editorial diagnostic, not a prediction of platform reach or commercial outcome.

## Domain boundary
The AI-video A/B/C business-line model is loaded only for AI-video tasks. Other industry domains retain their own knowledge and rules.

## Model routing boundary
Fast Screen, Deep Review and Critic are configurable review roles. Jev/Laya are reference role labels, not evidence that those specific model APIs are connected. Same-model role separation is not independent model validation.

## Verification recorded in the private package
15 V4.1 regression tests passed; validator CLI smoke test passed; Python syntax and JSON syntax checks passed. Full legacy host regression and real user/performance validation remain separate and are not claimed by this public release.
