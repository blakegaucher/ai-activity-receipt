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
