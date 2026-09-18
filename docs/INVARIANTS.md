# AI Activity Receipt — Candidate Invariants

This document defines candidate semantic invariants for the **AI Activity Receipt** project.

> **Status:** Candidate, non-normative research specification. These rules are under development and may change with new schema versions and validation work.

The JSON Schema defines whether a Receipt has an acceptable **structure**.

These invariants address relationships and governance rules that ordinary JSON Schema validation may not be able to establish on its own.

---

## Why invariants are separate from the schema

A Receipt can be structurally valid while still being semantically inconsistent.

For example, a Receipt might contain:

- a completed consequential action with denied authorization;
- a source reference that was never registered;
- an incident referring to a nonexistent event;
- an authorization that expired before an action occurred;
- a verification claim unsupported by evidence.

The candidate invariants below are intended to detect those conditions.

The current `validate_receipts.py` checker implements an executable subset: **INV-02, INV-03, INV-04, INV-05, INV-07, INV-08, and INV-14**. Structural parts of INV-01 are also enforced by the JSON Schema. Other invariants remain documented research requirements until executable checks are added.

---

## INV-01 — Identity completeness

Every Receipt must identify:

- the Receipt;
- the underlying trace or run;
- the Receipt version;
- the record/schema version;
- the acting agent or system;
- the relevant principal/delegator.

Identifiers should remain stable enough to connect the Receipt to its supporting record and evidence.

### Failure examples

- missing `receipt_id`;
- missing `trace_id`;
- unknown acting agent;
- Receipt version omitted.

---

## INV-02 — Registered material sources

Every source referenced by a material action, result, verification record, or other material claim must correspond to a registered source in the underlying evidence model.

A Receipt must not create provenance by merely naming a source that does not exist in the supporting evidence.

### Candidate rule

If an identifier occurs in `source_refs`, it must resolve to a known source record.

### Failure example

```text
material_action.source_refs = ["src-99"]
```

when no material source with `source_id = "src-99"` exists.

---

## INV-03 — Authorized consequential completion

A consequential action may be recorded as `completed` only when the Receipt preserves evidence that the action was authorized and within delegated scope.

### Candidate rule

For any material action where:

```text
consequential = true
status = "completed"
```

the action must have:

- `authorization = "approved"`; and
- an `operation` included in `authority.scope`.

### Failure examples

- completed email send with `authorization = "denied"`;
- completed payment when `payment` is not in the delegated scope.

---

## INV-04 — Prohibited actions cannot be approved completions

An operation explicitly listed in `authority.prohibited` must not simultaneously be represented as an approved, successfully completed action under the same authority record.

### Failure example

```text
authority.prohibited = ["send_email"]
operation = "send_email"
authorization = "approved"
status = "completed"
```

---

## INV-05 — Material failures preserve incident evidence

Blocked or failed activity that is materially relevant to the run should remain visible rather than being silently dropped.

### Candidate rule

A blocked or failed action that is consequential, or that was denied authorization, should be accompanied by at least one incident record.

### Failure examples

- consequential tool execution failed but `incidents` is empty;
- unauthorized action was blocked but no incident was preserved.

---

## INV-06 — Authority timing is respected

A delegated action must occur within the authority window that applies to it.

### Candidate rule

Where timestamps are available:

- an action must not precede `authority.valid_from`;
- an action must not occur after `authority.valid_until`;
- expired authority must not be treated as active approval.

This rule is currently documented but not yet automated by the repository validator because the candidate action object does not yet require an action timestamp.

---

## INV-07 — Verification evidence resolves

A verification claim must point to evidence that can actually be resolved.

### Candidate rule

Every identifier in `verification.evidence_refs` must resolve to known evidence represented by the Receipt or its supporting record.

The current validator accepts registered material source IDs and material-action event IDs as resolvable candidate evidence.

### Failure example

```text
verification.evidence_refs = ["event-missing"]
```

when no corresponding evidence exists.

---

## INV-08 — Incident references resolve

When an incident names an `event_id`, that identifier must resolve to a material action or event in the supporting record.

### Failure example

An incident cites `event-44` but no such event exists.

---

## INV-09 — Delegation is internally consistent

The authority record should identify who delegated authority and to whom it was delegated, and those identities should be consistent with the acting system represented by the Receipt.

### Candidate rule

- `authority.principal` identifies the delegating principal;
- `authority.delegate` identifies the delegated actor;
- the acting system should be compatible with the recorded delegate or with an explicitly documented delegation chain.

This is currently a documented requirement pending a richer actor/delegation model.

---

## INV-10 — Integrity lineage is explicit

A derived Receipt should preserve integrity links sufficient to determine which canonical record it was derived from.

### Candidate rule

- `integrity.record_hash` identifies the relevant record state;
- `integrity.derived_from_record_hash` binds the Receipt to its source record;
- where sequential record versions exist, `previous_record_hash` should preserve lineage.

Hash fields support tamper detection and traceability; they do not by themselves prove that the underlying facts are true.

---

## INV-11 — Material event identity is stable

Material events should have stable identifiers when other records depend on them.

### Candidate rule

If an action is referenced by verification, incident, or other evidence, its `event_id` should be unique within the relevant trace and should not be silently reassigned to a different event.

This requirement is documented but not yet fully automated.

---

## INV-12 — Evidence symmetry

A normal Receipt must not contain material facts that cannot be derived from the same underlying evidence available to the corresponding control condition or canonical record.

The Receipt may summarize, normalize, or index evidence. It must not invent new evidence merely to make the run easier to audit.

This invariant is especially important for comparative evaluation such as AR-P003.

---

## INV-13 — Uncertainty is preserved

Unknown, pending, conflicting, missing, or uncertain evidence should remain represented as such.

A Receipt should not convert incomplete evidence into unwarranted certainty.

### Candidate examples

- use `verification.state = "pending"` when verification has not completed;
- preserve an unresolved incident rather than silently treating it as cleared;
- do not infer approval solely from the fact that an action completed.

---

## INV-14 — Private reasoning is excluded

Private chain-of-thought, hidden scratchpads, or equivalent private reasoning traces are outside the Activity Receipt model.

### Candidate rule

The Receipt must not include fields such as:

- `chain_of_thought`;
- `chain-of-thought`;
- `hidden_reasoning`;
- `private_reasoning`;
- `reasoning_trace`;
- `scratchpad`.

Auditability should come from observable actions, authority, evidence, verification, and incident records rather than hidden reasoning.

---

## Validator scope

The repository validator deliberately separates:

1. **JSON Schema validation** — structural requirements; and
2. **semantic invariant checking** — relationships that require logic beyond ordinary schema validation.

Current executable semantic checks cover:

- registered source references;
- approved/in-scope consequential completion;
- prohibited-action contradictions;
- incident preservation for material failures;
- resolvable verification references;
- resolvable incident references;
- private-reasoning exclusion.

A fixture can therefore be:

- structurally valid and semantically valid;
- structurally valid and intentionally semantically invalid; or
- structurally invalid.

The repository's invalid authorization fixture is intentionally in the second category so the semantic checker can demonstrate rejection of a structurally valid but governance-inconsistent Receipt.

---

## Research boundary

These invariants are engineering rules for an evolving research artifact.

Passing them does **not** establish:

- legal or regulatory compliance;
- safety certification;
- correctness of the underlying evidence;
- real-world audit effectiveness;
- standards conformance;
- commercial fitness.

They are intended to make the candidate representation more internally consistent, testable, and falsifiable.
