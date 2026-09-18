# AI Activity Receipt — Candidate Invariants

This document defines candidate semantic invariants for the **AI Activity Receipt** project.

> **Status:** Candidate, non-normative research specification. These rules are under development and may change with new schema versions and validation work.

The JSON Schema defines whether a Receipt has an acceptable **structure**.

These invariants address relationships and governance rules that ordinary JSON Schema validation may not be able to establish on its own.

The current public validator implements an executable subset of the rules below. Candidate-v0.2 strengthens that subset with explicit action timing, authorization-decision timing, direct-delegation consistency, stable event identity, linked incident evidence, and stronger verification checks.

---

## Validation ordering

The executable validator treats structural validation as the prerequisite for ordinary semantic-invariant evaluation. Semantic rules assume the object shapes defined by the candidate JSON Schema and therefore are not run against arbitrary malformed structures.

One defense-in-depth exception remains: private-reasoning field names are scanned even when structural validation fails, so an excluded field can still be surfaced as a diagnostic.

This ordering means a structurally invalid Receipt is rejected at the schema layer rather than producing misleading semantic failures or implementation type errors.

---

## Why invariants are separate from the schema

A Receipt can be structurally valid while still being semantically inconsistent.

For example, a Receipt might contain:

- a completed consequential action with denied authorization;
- a source reference that was never registered;
- an incident referring to a nonexistent event;
- an action that occurred outside its authority window;
- a verification claim unsupported by evidence;
- duplicate event identifiers that make later references ambiguous.

The candidate invariants below are intended to detect those conditions.

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

### Current enforcement

The candidate JSON Schema requires the core identity/version fields. The semantic validator assumes those structural requirements have been checked.

---

## INV-02 — Registered and unambiguous material sources

Every source referenced by a material action, result, verification record, or other material claim must correspond to a registered source in the supporting evidence model.

A Receipt must not create provenance by merely naming a source that does not exist in the supporting evidence.

### Candidate rules

- Every identifier in `material_actions[].source_refs` must resolve to a registered `material_sources[].source_id`.
- A `source_id` must not be duplicated within one Receipt.

### Failure examples

- `source_refs = ["src-99"]` when no `src-99` exists.
- Two different material-source objects both use `source_id = "src-A"`.

**Executable in candidate-v0.2:** yes.

---

## INV-03 — Authorized consequential completion

A consequential action may be recorded as `completed` only when the Receipt preserves evidence that the action was authorized, within delegated scope, and authorized before execution.

### Candidate rules

For any material action where:

```text
consequential = true
status = "completed"
```

the action must have:

- `authorization = "approved"`;
- an `operation` included in `authority.scope`;
- `authorization_decided_at` recorded;
- an authorization-decision time that is not later than `occurred_at`.

### Failure examples

- completed email send with `authorization = "denied"`;
- completed payment when `payment` is outside delegated scope;
- approval timestamp that occurs after the action.

**Executable in candidate-v0.2:** yes.

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

**Executable in candidate-v0.2:** yes.

---

## INV-05 — Material failures preserve linked incident evidence

Blocked or failed activity that is materially relevant to the run should remain visible rather than being silently dropped.

### Candidate rule

A blocked or failed action that is consequential, or that was denied authorization, must have a corresponding incident record. When the action has an `event_id`, the incident should link to that event.

### Failure examples

- consequential tool execution failed but no incident is preserved;
- unauthorized action was blocked but no incident links to the blocked event.

**Executable in candidate-v0.2:** yes.

---

## INV-06 — Authority timing is respected

A material action must occur inside the recorded authority window.

### Candidate rules

- `occurred_at` must not precede `authority.valid_from`;
- `occurred_at` must not occur after `authority.valid_until`.

Candidate-v0.2 requires `valid_from`, `valid_until`, and an `occurred_at` timestamp for every material action, which makes this invariant directly testable.

### Failure examples

- an action occurs before delegation begins;
- an action occurs after authority expires.

**Executable in candidate-v0.2:** yes.

---

## INV-07 — Verification evidence exists and resolves

A verification claim must point to evidence that can actually be resolved.

### Candidate rules

- `verification.state = "confirmed"` requires at least one `evidence_ref`;
- every identifier in `verification.evidence_refs` must resolve to evidence represented by the Receipt or supporting record.

The current public validator accepts registered material-source IDs and material-action event IDs as candidate resolvable evidence.

### Failure examples

- verification is `confirmed` with no evidence reference;
- verification cites `event-missing` when no such event exists.

**Executable in candidate-v0.2:** yes.

---

## INV-08 — Incident references resolve

When an incident names an `event_id`, that identifier must resolve to a material action/event in the supporting record.

### Failure example

An incident cites `event-44` but no such event exists.

**Executable in candidate-v0.2:** yes.

---

## INV-09 — Delegation is internally consistent

The authority record should identify who delegated authority and to whom it was delegated, and those identities should be consistent with the acting system represented by the Receipt.

### Candidate-v0.2 direct-delegation profile

The current public schema represents one acting system and one direct delegate. Under that simplified profile:

```text
authority.delegate == system.agent_id
```

Richer delegation chains, subagents, organizations, service accounts, and on-behalf-of relationships remain future work and should receive an explicit representation rather than silently overloading this rule.

**Executable in candidate-v0.2:** yes, for the direct-delegation profile.

---

## INV-10 — Integrity lineage is explicit

A derived Receipt should preserve integrity links sufficient to determine which canonical record it was derived from.

### Candidate fields

- `integrity.record_hash`;
- `integrity.previous_record_hash`;
- `integrity.derived_from_record_hash`;
- `integrity.generated_at`.

### Boundary

The current validator checks structural presence/format for required integrity fields. It does **not** recompute a canonical-record hash because the public Receipt fixture does not include the full canonical record bytes needed for cryptographic verification.

**Executable in candidate-v0.2:** structural only.

---

## INV-11 — Material event identity is stable

Material events should have stable and unambiguous identifiers when other records depend on them.

### Candidate rules

- candidate-v0.2 requires `event_id` for each material action;
- duplicate material-action `event_id` values are invalid within one Receipt.

### Failure example

Two actions both use `event_id = "event-7"`.

**Executable in candidate-v0.2:** yes.

---

## INV-12 — Evidence symmetry

A normal Receipt must not contain material facts that cannot be derived from the same underlying evidence available to the corresponding control condition or canonical record.

The Receipt may summarize, normalize, or index evidence. It must not invent new evidence merely to make the run easier to audit.

This invariant is especially important for comparative evaluation such as AR-P003.

### Boundary

Evidence symmetry cannot be established from one Receipt in isolation; it requires comparing the Receipt with its source evidence/canonical record.

**Executable in candidate-v0.2:** not from the standalone Receipt.

---

## INV-13 — Uncertainty is preserved

Unknown, pending, conflicting, missing, or uncertain evidence should remain represented as such.

A Receipt should not convert incomplete evidence into unwarranted certainty.

### Candidate examples

- use `verification.state = "pending"` when verification has not completed;
- preserve an unresolved incident rather than silently treating it as cleared;
- do not infer approval solely from the fact that an action completed.

The confirmed-verification evidence requirement in INV-07 provides one executable guard against unwarranted certainty, but the broader INV-13 rule requires contextual evidence.

**Executable in candidate-v0.2:** partial.

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

Candidate-v0.2 uses closed objects (`additionalProperties: false`) for the published schema, so an unexpected private-reasoning field is structurally rejected. The semantic validator also scans recursively as a defense-in-depth diagnostic.

**Executable in candidate-v0.2:** yes as structural rejection, plus semantic diagnostic.

---

## INV-15 — Generation time follows represented activity

A Receipt must not claim to have been generated before the activity or authorization decision that it represents.

### Candidate rules

- `integrity.generated_at` must not precede a represented material action's `occurred_at`;
- when `authorization_decided_at` is present, it must not occur after `integrity.generated_at`.

This is a record-coherence rule. It does not prove that source clocks were synchronized or accurate.

### Failure examples

- a Receipt generated at 15:25 contains a material action recorded at 15:30;
- a Receipt generated at 15:25 contains an authorization decision recorded at 15:26.

**Executable in candidate-v0.2:** yes.

---

## Candidate-v0.2 validator coverage

The public validator now checks:

- **INV-02** registered and unique material-source IDs;
- **INV-03** approved, in-scope, prior authorization for completed consequential actions;
- **INV-04** prohibited-action contradictions;
- **INV-05** linked incident preservation for material blocked/failed actions;
- **INV-06** authority-window coherence and action timing against that window;
- **INV-07** confirmed verification evidence and resolvable verification references;
- **INV-08** resolvable incident references;
- **INV-09** direct-delegation consistency;
- **INV-11** unique material-action event IDs;
- **INV-14** private-reasoning exclusion;
- **INV-15** generation-time coherence.

The schema also enforces the structural parts of **INV-01**, required timing fields used by **INV-06**, required event identity for **INV-11**, and required integrity fields for **INV-10**.

The repository fixture manifest records expected structural/semantic outcomes and expected invariant failures so a fixture cannot silently pass for the wrong reason.

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
