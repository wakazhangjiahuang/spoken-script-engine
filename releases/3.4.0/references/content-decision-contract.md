# Content Decision Contract v1.0

## Do not re-derive what is already known
If current domain guidance already defines audience segments, core needs, content lines and examples, treat them as authoritative inputs. A script must reference one specific source item. A role label alone is not a need.

## Required unit in every script
The script must carry a professional_decision object containing:
- audience_need_ref: source asset ID, source locator and original need statement.
- viewer_task: one task the viewer is actually trying to complete.
- case_mode: real, simulated or method.
- concrete_input: a specific brief, artifact, workflow, document, product or problem.
- constraints: conditions that affect the decision.
- options_considered: at least two distinct options and their trade-offs.
- chosen_option and rejected_option.
- decision_reason.
- source_status and evidence_refs.
- applicability_boundary.
- viewer_action.
- spoken_anchor: exact segment ID and quote from the spoken body.

A simulated case must include simulation_disclosure, also anchored to actual spoken text. Never present simulation as a real client, order, test or outcome.

## Editorial sequence
1. Select the viewer task from the current need source.
2. Identify the exact information gap or decision that blocks the task.
3. Select a concrete input or clearly disclosed simulation.
4. Compare at least two viable options and their trade-offs.
5. Explain the chosen decision and why.
6. State when the decision does not apply.
7. Give one immediate viewer action.

## Non-compensatory release rules
- Missing source binding or professional decision: reject.
- Decision not spoken in the body: reject.
- Simulated case not disclosed: reject.
- Review quote absent from the actual script: reject.
- Any editorial dimension below 3/5: revise; no total-score compensation.
- External reading/blind-test PASS requires a real evidence file and matching SHA-256.

The contract validates editorial substance structure. It does not predict platform reach or commercial results.
