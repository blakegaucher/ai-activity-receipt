# AI Activity Receipt — Terminology and Field Semantics

This document defines the working vocabulary used by the **AI Activity Receipt** project.

> **Status:** Candidate, non-normative research terminology. Names and semantics may change as the schema and evaluation program evolve.

The goal is to keep the public README, JSON Schema, invariant specification, fixtures, and validation work aligned without implying legal, regulatory, or standards-defined meanings where none are claimed.

---

## Core concepts

### Evidence substrate

The underlying evidence from which an Activity Record or Receipt is derived.

Examples may include:

- application logs;
- tool-call traces;
- authorization records;
- source/provenance records;
- human approval events;
- verification evidence;
- incident records.

The Receipt is not intended to replace this evidence.

### Canonical Activity Record

A normalized machine-oriented representation of the relevant activity, identities, authority, provenance, actions, verification, incidents, and integrity links.

The long-term design direction is for a human-facing Receipt to be deterministically derived from this record.

### Activity Receipt

A compact, inspectable representation of consequential AI-agent activity.

A Receipt is intended to answer questions such as:

- what system acted;
- under whose authority;
- what actions occurred;
- what evidence materially supported the activity;
- what verification state was reached;
- what incidents or blocked actions occurred.

A Receipt is not a claim that the underlying activity was correct, safe, lawful, or effective.

### Receipt view

The human-facing presentation derived from the underlying record.

A view may omit non-material detail for readability, but it should not invent material facts.

---

## Identity and version fields

### `receipt_id`

Stable identifier for a particular Activity Receipt.

It should distinguish the Receipt from other Receipts and allow references back to it.

### `trace_id`

Identifier connecting the Receipt to the underlying run, trace, or activity episode.

### `record_schema_version`

Version identifier for the machine-record/schema representation from which the Receipt is derived or against which it is interpreted.

### `receipt_version`

Version identifier for the Receipt representation itself.

A schema or semantic change should be reflected through explicit versioning rather than silently changing the meaning of an existing version.

### `system.agent_id`

Identifier for the acting AI system or agent represented by the Receipt.

### `system.version`

Version identifier for that system or agent configuration.

Optional provider/model fields may add context but do not replace the stable system identity.

---

## Authority and delegation

### Principal

The human, organization, or other authorized actor that delegates authority.

Represented by `authority.principal`.

### Delegate

The actor to which authority is delegated.

Represented by `authority.delegate`.

In simple cases this may directly correspond to the acting agent. Richer delegation chains remain future work.

### Scope

The operations the delegate is permitted to perform under the recorded authority.

Represented by `authority.scope`.

A completed consequential action should not be treated as authorized merely because it succeeded technically; the operation also needs to fall within scope.

### Prohibited operations

Operations explicitly excluded from the delegated authority.

Represented by `authority.prohibited`.

### Authority window

The time interval during which an authority grant is intended to be valid.

Candidate fields:

- `authority.valid_from`;
- `authority.valid_until`.

The current public schema allows these timestamps, but the public semantic validator does not yet enforce action-time comparisons because material actions do not yet require their own timestamp.

---

## Provenance

### Material source

A source that materially supports the result, action, verification, or reconstruction of the activity.

Represented in `material_sources`.

### `source_id`

Stable identifier for a registered material source.

### Source role

A description of how a source relates to the activity, such as supporting a result.

Represented by `material_sources[].role`.

### Source reference

A reference from a material action to a registered material source.

Represented by `material_actions[].source_refs`.

A source reference should resolve to a known `source_id`.

### Evidence symmetry

The research rule that a normal Receipt should not introduce material evidence unavailable from the corresponding underlying evidence set.

The Receipt may organize evidence; it should not manufacture evidence.

---

## Actions

### Material action

An operation important enough to preserve for later inspection.

Represented in `material_actions`.

### Operation

The type of action attempted or performed, represented by `operation`.

Examples may include reading data, analyzing content, sending a message, or invoking an external tool.

### Status

The observed execution state of a material action.

Current candidate values are:

- `completed`;
- `blocked`;
- `failed`;
- `pending`;
- `unknown`.

Status describes what happened operationally. It does not by itself establish authorization.

### Authorization

The recorded authorization state associated with an action.

Current candidate values are:

- `approved`;
- `denied`;
- `not_required`;
- `unknown`.

### Consequential action

An action marked as materially significant enough that authorization and downstream effects warrant explicit inspection.

Represented by `consequential: true`.

The candidate validator requires completed consequential actions to have approved authorization and to fall within delegated scope.

### `event_id`

Stable identifier for a material action/event when other records need to reference it.

Incident and verification references should resolve to known evidence/event identifiers.

---

## Verification

### Verification

The explicit state of checking, confirming, or otherwise evaluating the relevant result or activity.

Represented by the `verification` object.

### Verification state

Current candidate values are:

- `not_required`;
- `pending`;
- `confirmed`;
- `failed`;
- `uncertain`.

These values should preserve uncertainty rather than imply certainty that the evidence does not support.

### Verification evidence reference

Identifier pointing to evidence used for verification.

Represented by `verification.evidence_refs`.

The current validator treats registered source IDs and material-action event IDs as resolvable candidate evidence.

---

## Incidents

### Incident

A preserved record of materially relevant blocked, failed, unauthorized, inconsistent, or otherwise noteworthy activity.

Represented in `incidents`.

An incident record is evidence that a noteworthy condition was preserved; it is not automatically a claim of harm.

### Incident type

Candidate classification label stored in `incidents[].type`.

### Incident event reference

Optional `event_id` linking an incident to a material action/event.

When present, it should resolve to an existing event.

### Mitigation

Optional description of a response to the incident.

Represented by `incidents[].mitigation`.

---

## Integrity and derivation

### `record_hash`

Candidate hash identifier for the relevant record state.

The public schema currently requires a value beginning with `sha256:`.

### `previous_record_hash`

Optional link to a previous record state.

This supports lineage in append-oriented or versioned records.

### `derived_from_record_hash`

Hash reference binding a Receipt to the record state from which it was derived.

### `generated_at`

Timestamp indicating when the represented artifact was generated.

Hash links can support tamper detection and lineage. They do not prove that the underlying evidence is factually correct.

---

## Validation terminology

### Structurally valid

A JSON document that satisfies the current candidate JSON Schema.

Structural validity does not guarantee semantic consistency.

### Semantically valid

A structurally valid Receipt that also satisfies the semantic invariants implemented by the current validator.

Because the invariant set is still developing, "semantically valid" means valid under the **implemented candidate checks**, not universally valid for every possible governance rule.

### Fixture

A synthetic test Receipt with a prespecified expected outcome.

The repository includes:

- an illustrative sample Receipt;
- a valid completed-authorized-action fixture;
- an intentionally invalid completed-with-denied-authorization fixture.

### Intentionally invalid fixture

A fixture designed to pass structural validation while violating one or more semantic invariants.

This is useful for demonstrating that schema validation alone is insufficient.

### Candidate

A design element under active research and subject to revision.

### Non-normative

Not presented as a formal standard, certification requirement, legal rule, or binding external specification.

---

## Private reasoning

### Private reasoning / chain-of-thought

Hidden internal reasoning, scratchpads, or equivalent private deliberation.

These are intentionally outside the Activity Receipt model.

The project aims to make activity inspectable through observable actions, authority, provenance, verification, incidents, and integrity links rather than requiring disclosure of private chain-of-thought.

---

## Evidence boundary

Terms in this repository describe an evolving research representation.

They do not by themselves establish:

- legal compliance;
- regulatory compliance;
- safety certification;
- standards conformance;
- factual correctness of source evidence;
- improved human productivity;
- improved audit speed;
- commercial effectiveness.

Those questions require separate evidence and evaluation.
