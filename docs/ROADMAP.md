# AI Activity Receipt — Roadmap

This roadmap describes the current development direction for the **AI Activity Receipt** project.

> **Status:** Early-stage, pre-commercial research and development. Roadmap items are plans, not claims of completed functionality.

---

## Current foundation

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
- a public candidate-v0.2 schema/validator with a 17-fixture reproducibility manifest;
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

- fresh sealed synthetic corpus;
- independent human reviewers;
- randomized case order;
- balanced control and Receipt conditions;
- realistic heterogeneous logs;
- reduced answer leakage;
- proper wall-clock timing;
- safe reviewer breaks;
- stale/incomplete Receipt cases;
- Receipt/raw-evidence conflict cases;
- frozen scoring rules and endpoints.

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

A Receipt can be deterministically derived from a canonical record and traced back to its underlying evidence.

---

## Phase 4 — Interoperability

**Goal:** Map AI Activity Receipt concepts onto existing infrastructure rather than creating an isolated logging system.

### Research directions

- [x] Publish an initial dated field/concept crosswalk.
- [x] Cover W3C PROV / PROV-O.
- [x] Cover OpenTelemetry traces and developing GenAI conventions.
- [x] Cover C2PA 2.4 / Content Credentials.
- [x] Cover MCP 2026-07-28, A2A, OAuth RAR, and current NIST agent identity/authorization work.
- [ ] Publish machine-readable mappings after the canonical Activity Record stabilizes.
- [ ] Prototype an OpenTelemetry-to-Receipt adapter.
- [ ] Prototype an MCP evidence adapter that separates descriptive identity from authenticated identity.
- [ ] Evaluate optional C2PA attestation references for content-producing workflows.

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

**Goal:** Allow people outside the project to challenge the design.

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
