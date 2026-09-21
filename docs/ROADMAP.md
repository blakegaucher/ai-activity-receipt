# AI Activity Receipt — Roadmap

This roadmap describes the current development direction for the **AI Activity Receipt** project.

> **Status:** Early-stage, pre-commercial research and development. Roadmap items are plans, not claims of completed functionality.

For the shortest operational view of what is still blocked on owner/admin, human-study, external-review, or production evidence, see [Remaining Gates Dashboard](REMAINING-GATES.md).

---

## Current foundation

- [x] Preserve cross-conversation/project continuity with a dated human-readable snapshot and machine-readable continuity guard.
- [x] Preserve the frozen AR-P003 v0.2.3 auxiliary-AI baseline separately from v0.3 development.

The project currently has:

- a model-neutral Activity Receipt concept;
- a developing canonical Activity Record model;
- synthetic schema and invariant testing;
- an illustrative Receipt example;
- AR-P001 structural validation;
- AR-P002 expanded engineering checks;
- AR-P003 comparative-audit benchmark development;
- documented benchmark defects and evidence boundaries;
- a human-centered next-test direction;
- a public candidate-v0.2 schema/validator with a 21-fixture reproducibility manifest;
- a dated interoperability research snapshot covering provenance, telemetry, content credentials, agent protocols, and authorization.

---

## Phase 1 — Public research foundation

**Goal:** Make the project understandable, inspectable, and reproducible.

### Work

- [x] Publish project overview.
- [x] Publish illustrative sample Receipt.
- [x] Publish validation record.
- [x] Preserve limitations and negative findings.
- [x] Publish a candidate machine-readable schema.
- [x] Publish invariant definitions.
- [x] Add additional valid and invalid example Receipts.
- [x] Document terminology and field semantics.
- [x] Add deterministic validation examples.

### Exit condition

A technically informed reader should be able to understand what an Activity Receipt represents, what it does not represent, and how basic structural validity is evaluated.

---

## Phase 2 — AR-P003 human-centered benchmark

**Goal:** Test whether the Receipt helps humans reconstruct consequential AI-agent activity.

### Planned design

- [x] Publish candidate v0.3 preregistration draft.
- [x] Publish machine-readable protocol scaffold.
- [x] Publish deterministic component-level scoring utility and smoke test.
- [x] Publish scoring-record JSON Schema.
- [x] Publish seeded balanced assignment generator with per-reviewer/per-case condition-balance guarantees, diagnostics, and smoke tests.
- [x] Publish neutral reviewer-instructions draft.
- [x] Publish SHA-256 freeze-manifest utility.
- [x] Publish a development case-package schema/linter for file separation, path safety, exact leakage markers, and condition-symmetry checks.
- [x] Publish a development sample-size/precision planner and illustrative sensitivity grid without freezing assumptions.
- [x] Publish a development-only offline reviewer runner with structured responses, pause/visibility timing, safe intermissions, and reviewer/analysis data separation.
- [x] Add a neutral pre-case comprehension gate before the first timed case and carry pass metadata through response validation/analysis merge.
- [x] Add an untimed structured practice reconstruction before study timing, with pass metadata excluded from scorer outcomes.
- [x] Publish an analysis-side reviewer-bundle builder that packages seeded assignments + linted case packages while keeping gold/strata hidden and hashing generated artifacts.
- [x] Add a gold-to-answer-option representability guard and pre-freeze option diagnostics.
- [x] Add an end-to-end assignment → bundle → reviewer-response → hidden-label merge → scoring smoke test.
- [x] Publish a machine-readable freeze-readiness guard that distinguishes pending/prepared/complete/not-applicable gates and rejects premature ready/frozen states.
- [x] Publish a structured manual browser/device smoke-record schema and validator without treating the checked-in template as real smoke evidence.
- [x] Bind reviewer bundles/responses to the exact assignment hash/version and reject case/order/condition drift during analysis.
- [x] Ignore common local/private study outputs by default to reduce accidental Git commits.
- [ ] Complete manual browser/device, pause/visibility, reload/download-loss, scrolling, and accessibility smoke tests for the intended study environment.
- [x] Publish a third-party dependency/action inventory and license-decision preflight without selecting terms.
- [ ] Choose and publish an explicit repository license before presenting the project as open-source licensed or inviting broad code redistribution.
- [ ] Define target reviewer population.
- [ ] Freeze primary endpoint(s) and meaningful effect/precision target.
- [ ] Complete sample-size or precision analysis.
- [ ] Create fresh sealed synthetic corpus.
- [ ] Finalize independent human reviewer instructions from the published draft.
- [ ] Freeze randomized balanced assignment and case order using the published generator or a documented replacement.
- [ ] Validate realistic heterogeneous logs and remove answer leakage before freeze.
- [ ] Include stale/incomplete/conflicting Receipt challenge strata.
- [ ] Freeze scorer, exclusions, and statistical analysis plan.
- [ ] Obtain ethics/REB/IRB review or determination as applicable.
- [ ] Record final freeze manifest/hashes before confirmatory data collection.

### Candidate measures

- material-action reconstruction accuracy;
- authorization-violation detection;
- source-attribution accuracy;
- incident classification;
- verification-state accuracy;
- reconstruction time;
- reviewer agreement;
- false incident flags;
- missing-evidence identification;
- reviewer confidence.

### Governance

The corpus, instructions, assignment plan, scoring code, exclusions, and analysis rules should be frozen before scored results are inspected.

Negative, null, confusing, and failed cases remain part of the record.

### Exit condition

Produce a transparent human-review dataset that can estimate whether the Receipt changes audit accuracy, reconstruction time, or reliability.

A positive result is **not** required for this phase to be successful.

---

## Phase 3 — Canonical Activity Record

**Goal:** Separate the authoritative machine record from the compact human-facing Receipt.

### Current engineering progress

- [x] Publish candidate canonical-record JSON Schema.
- [x] Publish normalized actor/source/event representation.
- [x] Add explicit materiality selection for sources and events.
- [x] Publish deterministic record-to-Receipt derivation utility.
- [x] Bind the derived Receipt to the exact canonical record with SHA-256 under a documented project-local serialization profile.
- [x] Add an exact-match synthetic derivation self-test and Receipt re-validation.
- [x] Add pre-derivation canonical-record governance checks that mirror key Receipt invariants for material actions.
- [x] Publish a standalone external evidence-reference schema/validator prototype with record-subject resolution and explicit validation state.
- [x] Content-bind the standalone external evidence-reference index to the exact canonical record under the existing project-local SHA-256 serialization profile.
- [ ] Decide whether to retain the separately bound external evidence-reference index as a companion artifact or integrate it into a future canonical-record version, then implement richer real ingestion references accordingly.
- [x] Exercise the canonical record as the target of a synthetic OTLP/JSON GenAI adapter.
- [x] Define candidate multi-agent and multi-hop delegation-chain semantics, invariants, and standards boundaries.
- [x] Publish a standalone multi-hop delegation-chain validator/schema/example with adversarial invariant tests, without changing candidate-record-v0.1.
- [x] Implement multi-hop delegation in a versioned research future record/Receipt profile with loss-aware migration tests from the direct-delegation profile.
- [ ] Decide whether/when candidate-record-v0.2 should graduate from research/ into the public canonical schema path.
- [x] Publish an integrity/attestation design direction and evaluate established envelope approaches.
- [x] Define a machine-readable candidate signer identity, key-management, payload-type, trust, threshold, and revocation policy for attestation research.
- [x] Implement a research-only DSSE v1 + Ed25519 signing/verification prototype with ephemeral test keys and adversarial verification cases.
- [ ] Implement production signing/attestation only when real identity issuance, protected key storage, revocation/status infrastructure, and deployment trust roots exist.
- [x] Add a heterogeneous synthetic workflow derivation pilot spanning direct records, OpenTelemetry, MCP, success/failure/blocked/pending states, incidents, and verification variants.
- [ ] Test derivation against heterogeneous realistic workflow traces.

### Candidate architecture

1. **Evidence substrate**
   - application logs;
   - traces;
   - tool events;
   - authorization records;
   - source/provenance records;
   - verification evidence.

2. **Canonical Activity Record**
   - normalized actors;
   - authority and delegation;
   - events;
   - material sources;
   - verification;
   - incidents;
   - integrity links.

3. **Activity Receipt View**
   - compact derived representation;
   - explicitly bound to the canonical record;
   - designed for human inspection.

### Candidate integrity fields

- `record_id`
- `record_schema_version`
- `trace_id`
- `record_hash`
- `previous_record_hash`
- `receipt_id`
- `receipt_version`
- `derived_from_record_hash`
- `generated_at`
- optional attestation references

### Exit condition

The **synthetic candidate prototype** now demonstrates deterministic derivation from a canonical record and a hash binding back to that exact record. Separate research artifacts also cover multi-hop delegation, external evidence indexing, trust-policy definition, and test-only DSSE/Ed25519 attestation.

Phase 3 remains open for real evidence-substrate/source-to-record ingestion, a public-version decision for the multi-hop profile, production identity/key/revocation infrastructure, and realistic-workflow testing.

---

## Phase 4 — Interoperability

**Goal:** Map AI Activity Receipt concepts onto existing infrastructure rather than creating an isolated logging system.

### Research directions

- [x] Publish an initial dated field/concept crosswalk.
- [x] Cover W3C PROV / PROV-O.
- [x] Cover OpenTelemetry traces and developing GenAI conventions.
- [x] Cover C2PA 2.4 / Content Credentials.
- [x] Cover MCP 2026-07-28, A2A, OAuth RAR, and current NIST agent identity/authorization work.
- [x] Publish a versioned machine-readable candidate mapping artifact with schema/CI validation against the current canonical Activity Record.
- [x] Prototype an OpenTelemetry GenAI -> canonical-record -> Receipt adapter on synthetic OTLP/JSON traces.
- [x] Prototype an MCP 2026-07-28 evidence adapter that separates self-reported client/server metadata from authenticated identity and authority.
- [x] Add a synthetic cross-adapter normalization parity test for aligned OpenTelemetry/MCP governance-action semantics.
- [x] Evaluate optional C2PA 2.4 content-provenance/repository-receipt references and document an external-reference-first design direction.

### Rule

Interoperability research does not imply standards certification or conformance.

### Exit condition

Publish explicit field mappings and document where Activity Receipt concepts align, extend, or differ. The first dated research snapshot now satisfies the documentation portion; implementation/conformance work remains open.

---

## Phase 5 — Realistic workflow pilots

**Goal:** Test the design outside simplified benchmark fixtures.

Candidate workflows may include:

- research and evidence gathering;
- document analysis;
- administrative workflows;
- multi-agent delegation;
- tool-using assistants;
- human approval before consequential actions.

Initial pilots should remain low-risk and should preserve underlying logs for comparison.

### Exit condition

Determine which Receipt fields remain useful, redundant, missing, or impractical in realistic agent workflows.

---

## Phase 6 — External evaluation
- [x] Publish repository health guidance for external reviewers: contribution rules, security-reporting boundary, citation metadata, PR checklist, and reproducibility issue form.
- [x] Add deterministic repository-local Markdown link integrity checks to CI and the reproducibility suite.
- [x] Add repository-wide JSON syntax, duplicate-key, and declared-schema integrity checks to CI and the reproducibility suite.
- [x] Continuity snapshot/guard now explicitly covers repository-wide Markdown-link and JSON-integrity controls.
- [x] Add repository-file security hardening: least-privilege/pinned CI checks, checkout credential-persistence disablement, finite timeout/stale-run cancellation, Dependabot version updates, CODEOWNERS, deterministic security smoke checks, and stricter offline-runner resource/CSP bounds.
- [x] Add and verify pinned CodeQL advanced setup for Python and JavaScript/TypeScript.
- [x] Verify main-branch protection/ruleset, private vulnerability reporting, Dependabot alerts/security updates, code-scanning alerts, secret-scanning/secret-protection, and push protection.
- [x] Authenticated owner verification confirms Code scanning on `main` is **0 open / 2 closed** and custom repository **Security alerts** notifications are enabled.

**Goal:** Allow people outside the project to challenge the design.

Preparation completed:

- [x] Publish a one-command public reproducibility runner with machine-readable results and SHA-256 artifact manifest.
- [x] Publish a clean-room external reproduction handoff and issue-reporting path.
- [ ] Obtain at least one independent external reproduction attempt.

Potential activities:

- independent reviewers;
- external reproducibility attempts;
- academic collaboration;
- standards/community feedback;
- red-team evaluation;
- implementation by another developer or organization.

### Exit condition

At least one independent party can reconstruct, critique, or implement the specification without relying on undocumented project knowledge.

---

## Longer-term product questions

Only after stronger evidence exists should the project evaluate questions such as:

- deployment architecture;
- developer SDKs;
- APIs;
- audit dashboards;
- enterprise integrations;
- procurement use cases;
- compliance-support tooling;
- commercial models.

These are future product questions, not current capabilities.

---

## Non-goals

The project is not intended to:

- expose private chain-of-thought;
- certify that an AI system is safe;
- replace raw logs or observability platforms;
- guarantee regulatory compliance;
- turn a Receipt into unquestionable ground truth;
- hide failures or unfavorable experimental results.

---

## Guiding principle

**Record what happened. Preserve where the evidence came from. Make authority and verification inspectable. Test whether that representation actually helps people.**
