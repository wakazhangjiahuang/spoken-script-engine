# spoken-script-engine v3.4.0 — Content Decision Gate

This is a targeted quality repair over the existing 3.3.0 runtime. It does not expand audience research or replace domain guidance.

## Defect addressed
A script could satisfy field/schema checks while remaining generic: no concrete source-bound viewer task, no professional trade-off, no decision spoken in the body, and score quotes that did not appear in the script. Structural completion was mistaken for editorial quality.

## New contract
1. Reuse current confirmed audience and core-need assets. Do not regenerate or broaden them without a source gap.
2. Bind every script to one exact audience-need source: source asset ID, source locator and original need quote.
3. Require one spoken professional decision unit: concrete input, constraints, at least two options with trade-offs, selected/rejected option, reason, evidence status, applicability boundary, viewer action and exact spoken-body anchor.
4. Simulated cases must be explicitly disclosed in spoken text.
5. Every review score must quote text that exists in the actual script. Every dimension must be at least 3/5; high totals cannot offset weak core dimensions.
6. External test status cannot be marked PASS without an evidence file and matching SHA-256.
7. User-rejected scripts remain negative regression cases, never positive few-shot examples.

## Files
- references/content-decision-contract.md
- schemas/professional-decision.schema.json
- scripts/validate_content_decision.py
- tests/test_content_decision.py

## Limits
The validator checks source binding, decision structure, spoken anchors, review evidence and non-compensatory score floors. It cannot prove audience click intent, retention, conversion or market performance. Those require independent blind review and actual platform data.
