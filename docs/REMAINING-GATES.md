# Remaining Gates Dashboard

> **Snapshot:** 2026-09-19  
> **Purpose:** Show the shortest path from the current repository state to the next evidence-bearing milestones without confusing technical preparation with external, human, commercial, or administrative evidence.

The repository is technically active and CI-green, but several important gates **cannot be completed by adding more code alone**.

## Current repository state

Already implemented and tested in repository CI:

- candidate Activity Receipt schema + semantic invariants;
- canonical Activity Record + deterministic Receipt derivation;
- OpenTelemetry GenAI and MCP synthetic adapter paths;
- interoperability mapping checks;
- multi-hop delegation research profile;
- external-evidence/C2PA reference research;
- test-only DSSE/Ed25519 attestation research;
- heterogeneous synthetic workflow pilot;
- AR-P003 v0.3 development runner/bundle/scoring pipeline;
- exact assignment binding and end-to-end development smoke tests;
- one-command reproducibility suite;
- repository security smoke checks;
- CodeQL advanced setup for Python and JavaScript/TypeScript;
- independent reproduction handoff instructions.

These are engineering/research accomplishments. They do not close the gates below.

## Gate 1 — Repository owner/admin governance

### Main protection — issue #36

**Status:** Open; owner/admin action required.

Required:

- protect `main` with a GitHub ruleset/branch protection;
- require the primary validation check;
- require CodeQL Python and JavaScript/TypeScript checks;
- block force-push and branch deletion;
- verify the rule actually blocks merge before checks complete.

The API still reports no repository rulesets.

### Security settings — issue #37

**Status:** Partially complete.

Complete:

- CodeQL advanced setup is on `main`;
- Python scan is green;
- JavaScript/TypeScript scan is green.

Still manual/admin:

- private vulnerability reporting;
- Dependabot security alerts/security updates;
- owner security-alert notifications;
- inspect the CodeQL alert inventory.

A green CodeQL workflow is not evidence that the alert count is zero.

### Repository license — issue #44

**Status:** Preflight complete; explicit owner/IP decision still required.

The repository currently has **no explicit license**.

Completed preparation:

- third-party/dependency/action inventory published;
- direct dependency + GitHub Action drift guard added to CI/reproducibility;
- owner decision brief published at [LICENSE-PREFLIGHT.md](LICENSE-PREFLIGHT.md);
- current no-license boundary preserved.

Do not describe the repository as MIT, Apache, CC, or otherwise open-source licensed until the owner deliberately selects terms.

The remaining action is the owner's explicit choice for project-authored code, documentation, synthetic fixtures, and any future released study material. This gate should be resolved before broad reuse/redistribution or a release intended for outside implementation.

## Gate 2 — AR-P003 study-instrument readiness

### Manual browser/device smoke tests — issue #38

**Status:** Open; requires real browser/device interaction.

A structured smoke-test record schema and validator now exist so each tested environment can be preserved with exact runner commit/hash, browser/OS/device details, per-check status, and defects. The checked-in example is an incomplete template and is not evidence that any environment passed.

Automated tests cannot establish:

- pause/resume behavior in actual browsers;
- background/visibility timing behavior;
- download persistence;
- navigation/reload warning behavior;
- keyboard/accessibility behavior;
- responsive/zoom usability;
- supported browser/device compatibility.

Use only synthetic development bundles.

### Preregistration/freeze decisions — issue #47

**Methodology-source conflicts:** now explicitly tracked. The current executable draft and the earlier project research review differ on comparison conditions, primary endpoint, timing semantics, and misleading-Receipt challenge architecture. The repository now fails closed against a future frozen protocol while required methodology decisions remain unresolved. See [AR-P003-V0.3-METHODOLOGY-DECISIONS.md](AR-P003-V0.3-METHODOLOGY-DECISIONS.md).

**Status:** Open; human-study methodology decisions required.

**Crossed-design planning tooling:** prepared. The repository now simulates the actual balanced reviewer/case assignment with reviewer/case random effects and two-way clustered uncertainty. This removes the earlier tooling gap but does not select the effect/precision target or freeze the sample size.

**Machine-readable readiness guard:** published at `benchmark/arp003_v0_3/freeze-readiness.current.json` with validator `check_freeze_readiness.py`. The current state is `development_not_ready`; the guard rejects premature ready/frozen claims but does not make the missing decisions.

**Leakage audit tooling:** prepared. `audit_leakage.py` operates analysis-side on generated reviewer bundles plus hidden gold and reports literal incident-label leakage, answer-option degeneracy, cross-presentation evidence drift, and Receipt presentation expansion. It is a heuristic pre-freeze screen, not proof that cases are unbiased or realistic.

Before confirmatory human execution:

- deliberately select the final comparison-condition design rather than inheriting the current two-condition implementation by default;
- define reviewer population/eligibility;
- freeze primary endpoint(s);
- define meaningful effect/precision target;
- freeze the assumptions/endpoint target for reviewer × case power/precision planning (design-specific crossed simulation tooling is now prepared);
- freeze sample size/allocation/stopping rule;
- create fresh sealed corpus;
- run the development leakage/presentation audit on the final build output and preserve the report;
- remove answer leakage from realistic heterogeneous logs and complete human case review;
- include stale/incomplete/conflicting Receipt strata;
- finalize reviewer instructions;
- freeze assignment/case order;
- freeze timing/exclusion rules;
- freeze scorer/statistical analysis;
- obtain ethics/REB/IRB review or determination as applicable;
- record final freeze hashes.

**Hard stop:** do not recruit or make human-benefit claims before these gates are complete.

## Gate 3 — Independent external reproduction

### First outside attempt — issue #39

**Status:** Prepared, not completed.

Public handoff:

- `docs/EXTERNAL-REPRODUCTION-HANDOFF.md`

The first independent party should use a clean checkout and the exact-lock reproduction path without undocumented project help.

A failed/partial reproduction is still valid evidence and must be preserved.

Project-authored CI cannot satisfy this gate.

## Gate 4 — Production/security claims

**Status:** Intentionally open.

The repository contains research/test-only cryptographic and governance mechanisms.

Production signing/attestation still requires:

- real identity issuance;
- protected private-key storage;
- rotation/compromise procedures;
- revocation/status infrastructure;
- deployment trust roots;
- trusted timestamp/history strategy where required.

Do not convert successful research DSSE tests into a production-trust claim.

## Gate 5 — Realistic external workflow evidence

**Status:** Open.

Synthetic workflows and protocol adapters are useful engineering evidence, but the repository still needs realistic heterogeneous workflow traces or independently produced traces before making broader capture/interoperability claims.

Any such work must preserve:

- source provenance;
- authorization evidence boundaries;
- privacy restrictions;
- negative/missing evidence;
- current schema/version boundaries.

## Commercialization boundary

This repository does **not** close the commercial evidence gaps for Ancient Immortal Art.

Customer discovery, one-buyer/one-workflow focus, pricing evidence, delivery-cost evidence, revenue, financing readiness, and product-market validation remain separate business evidence tracks.

Technical GitHub activity must not be counted as customer validation or revenue evidence.

## Recommended execution order

For repository work, the shortest non-circular sequence is:

1. owner/admin: issues #36 and #37;
2. owner/IP: issue #44;
3. manual runner smoke test: issue #38;
4. AR-P003 design/freeze work: issue #47;
5. independent reproduction: issue #39;
6. only then decide whether additional technical integration work has a stronger evidence payoff than commercialization/customer-validation work.

## Change-control rule

When a gate changes status:

1. preserve the evidence that changed it;
2. update the corresponding GitHub issue;
3. update `research/project-continuity-state.json`;
4. update `docs/PROJECT-CONTINUITY-2026-09-19.md` or its successor;
5. rerun the full validation/reproducibility suite;
6. avoid upgrading adjacent evidence classes that the new evidence does not support.
