# Remaining Gates Dashboard

> **Snapshot:** 2026-09-20  
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

**Status:** Completed and closed.

Authenticated/admin verification established that the `Protect main` ruleset is active, required validation + CodeQL checks are enforced, force-push/non-fast-forward updates and branch deletion are blocked, and the protected workflow was exercised without weakening the ruleset.

### Security settings — issue #37

**Status:** Completed and closed.

Authenticated owner evidence on 2026-09-20 verifies:

- GitHub Security → Code scanning with `is:open branch:main`: **0 Open / 2 Closed**;
- GitHub displays **“All alerts are resolved.”**;
- both original High CodeQL clear-text-logging findings are resolved on `main`;
- custom repository notifications: **Security alerts — enabled**.

This closes the repository-admin security-settings gate. The result establishes the configured control/alert state only; it is not evidence of vulnerability-free or production-secure software.

### Repository license — issue #44

**Status:** Completed and closed.

Blake Gaucher selected **Apache License 2.0** for project-authored public repository material. The repository publishes the complete standard text as top-level `LICENSE` and an informational `NOTICE` with the 2026 Blake Gaucher attribution.

The third-party/dependency/action preflight remains clear and machine-guarded. The license covers project-authored public code, validators/research utilities, adapters, benchmark tooling, offline runner, documentation, schemas, examples, synthetic fixtures, and synthetic benchmark material.

This does **not** release future private human-study/participant/reviewer/hidden-analysis or privacy-sensitive material; relicense third-party material; grant trademark/endorsement rights in Ancient Immortal Art or AI Activity Receipt; or transfer this decision into ARC / solver or other competition lanes.

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

**Decision-support map:** prepared. Every current ledger candidate is now mapped to its implementation/planning consequences in [AR-P003-V0.3-DECISION-SUPPORT.md](AR-P003-V0.3-DECISION-SUPPORT.md), with a machine guard that prevents silent candidate omission or invention. The research review's proposed +5pp / 3pp / +2pp thresholds are preserved as a candidate only; no methodology choice has been made.

**Crossed-design planning tooling:** prepared. The repository now simulates the actual balanced reviewer/case assignment with reviewer/case random effects and two-way clustered uncertainty. This removes the earlier tooling gap but does not select the effect/precision target or freeze the sample size.

**Machine-readable readiness guard:** published at `benchmark/arp003_v0_3/freeze-readiness.current.json` with validator `check_freeze_readiness.py`. The current state is `development_not_ready`; the guard rejects premature ready/frozen claims but does not make the missing decisions.

**Leakage audit tooling:** prepared. `audit_leakage.py` operates analysis-side on generated reviewer bundles plus hidden gold and reports literal incident-label leakage, answer-option degeneracy, cross-presentation evidence drift, and Receipt presentation expansion. It is a heuristic pre-freeze screen, not proof that cases are unbiased or realistic.

**Manual case-review record:** prepared. `validate_case_methodology_review.py` binds a human methodology review to the exact leakage-audit file and build hash, requires full case coverage for a complete review, blocks completion while automated high-risk flags remain, and requires explicit semantic-leakage, realism, framing-neutrality, and answer-option-quality judgments. The repository example remains `not_tested` and is not review evidence.

Before confirmatory human execution:

- deliberately select the final comparison-condition design rather than inheriting the current two-condition implementation by default;
- define reviewer population/eligibility;
- freeze primary endpoint(s);
- define meaningful effect/precision target;
- freeze the assumptions/endpoint target for reviewer × case power/precision planning (design-specific crossed simulation tooling is now prepared);
- freeze sample size/allocation/stopping rule;
- create fresh sealed corpus;
- run the development leakage/presentation audit on the final build output and preserve the report;
- complete the bound manual case-methodology review for every audited case;
- remove answer leakage from realistic heterogeneous logs and resolve every high-risk/revise/drop case under new hashes;
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

Issue #44 is resolved. The next unresolved repository gates remain:

1. manual runner smoke test: issue #38;
2. AR-P003 design/freeze work: issue #47;
3. independent reproduction: issue #39;
4. only then decide whether additional technical integration work has a stronger evidence payoff than commercialization/customer-validation work.

This licensing change does not advance issues #38, #39, or #47.

## Change-control rule

When a gate changes status:

1. preserve the evidence that changed it;
2. update the corresponding GitHub issue;
3. update `research/project-continuity-state.json`;
4. update `docs/PROJECT-CONTINUITY-2026-09-19.md` or its successor;
5. rerun the full validation/reproducibility suite;
6. avoid upgrading adjacent evidence classes that the new evidence does not support.
