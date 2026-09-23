# Project Continuity — AR-P003 Primary Timing Selection

**Snapshot date:** 2026-09-23  
**Scope:** AI Activity Receipt / AR-P003 v0.3 methodology continuity  
**Status:** Development-only; not frozen; not executed; recruitment unauthorized.

## Selected methodology state

The current controlled AR-P003 v0.3 methodology selections are:

- `comparison_conditions = three_condition_structured_control`
- `challenge_design = integrated_challenge_strata`
- `reviewer_population = relevant_professional_reviewers`
- `primary_endpoint = correct_completion_by_180s`
- `primary_timing_clock = wall_deadline_with_hidden_sensitivity`

The sole unresolved pre-freeze methodology decision in the ledger is:

- `effect_precision_target`

## Primary timing contract

The selected methodology uses 180 seconds of wall elapsed time for the primary endpoint.

- hidden/background elapsed time remains inside the primary deadline;
- active elapsed time remains a secondary/sensitivity measure;
- trials with more than 10 seconds hidden are reserved for prespecified sensitivity analysis;
- active-time sensitivity cannot replace the wall-clock primary result after outcomes are observed.

The timing/exclusions readiness gate remains prepared rather than complete because exact timeout/last-answer behavior, technical-failure and reload/context-break rules, and allowed browser/device behavior are not frozen or smoke-verified.

## Preserved boundaries

- v0.2.3 remains frozen append-only historical evidence.
- No human evidence has been created by this methodology decision.
- No recruitment or human execution is authorized.
- Final reviewer/case counts, allocation, stopping, effect target, sealed corpus, analysis plan, ethics determination, and freeze manifest remain open.
- Human audit benefit, speed, safety, compliance, and productivity claims remain unproven.

## Authority

Machine-readable current state:

- `benchmark/arp003_v0_3/methodology-decisions.current.json`
- `benchmark/arp003_v0_3/protocol.json`
- `benchmark/arp003_v0_3/freeze-readiness.current.json`
- `research/project-continuity-state.json`

Decision record:

- `docs/AR-P003-V0.3-PRIMARY-TIMING-CLOCK-DECISION-2026-09-23.md`

Proposal history:

- PR #94
