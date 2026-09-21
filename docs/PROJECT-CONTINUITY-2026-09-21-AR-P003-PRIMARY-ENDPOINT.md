# Project Continuity — AR-P003 v0.3 Primary Endpoint — 2026-09-21

**Snapshot date:** 2026-09-21  
**Lane:** AI Activity Receipt / AR-P003 v0.3 human evaluation methodology  
**Status:** development-only; not frozen; not executed  
**Recruitment:** not authorized

## Authority

Current controlled methodology state:

- `comparison_conditions = three_condition_structured_control`;
- `challenge_design = integrated_challenge_strata`;
- `reviewer_population = relevant_professional_reviewers`;
- `primary_endpoint = correct_completion_by_180s`;
- `primary_timing_clock = unresolved`;
- `effect_precision_target = unresolved`.

The selected primary endpoint is evidence-supported correct audit completion by 180 seconds. Case-specific required judgments and acceptable evidence/support sets are represented in the analysis-side endpoint contract and must be frozen before confirmatory execution. A deadline miss cannot succeed.

Component reconstruction metrics remain secondary diagnostics. Critical false clearance remains a separate prespecified safety endpoint; its threshold remains unresolved.

## Timing boundary

The endpoint decision does **not** choose a primary clock.

Development continues to record both:

- wall elapsed time;
- active elapsed time.

The preserved timing candidates are `active_time_primary` and `wall_deadline_with_hidden_sensitivity`. Confirmatory primary-outcome derivation is non-estimable/fail-closed until that separate methodology decision is selected.

## Development-only contingency

Before confirmatory freeze only, if the 180-second endpoint proves technically invalid or practically unusable, stop and return to methodology-decision state. Do not inspect confirmatory outcomes or automatically promote the component endpoint set. A change requires an explicit owner decision, new protocol version, updated planning/readiness, and new artifact hashes.

After freeze or confirmatory data collection begins, the primary endpoint cannot be switched because results are unfavorable. A later timing failure is reported under the prespecified affected/non-estimable rule.

## Protected boundaries

Do not:

- select the primary timing clock;
- select the effect/precision target;
- freeze final reviewer/case counts, cases per reviewer, challenge allocation, assignment seed, stopping rule, final corpus, or final analysis plan;
- recruit reviewers;
- advance ethics/REB/IRB status;
- execute confirmatory human data collection;
- advance issues #38 or #39;
- transfer this evidence into ARC/solver, CIH, META, Julia/DGAP, DGAP-3D, CASMI, or business-validation lanes.

## Next permitted action

Resolve **one** remaining methodology decision in a separately authorized change. The endpoint implementation itself does not authorize the timing decision.
