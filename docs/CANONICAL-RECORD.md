# Canonical Activity Record — Candidate v0.1

> **Status:** Candidate, non-normative engineering profile. This is a synthetic prototype for deterministic Receipt derivation, not a standards-conformance or production-readiness claim.

The AI Activity Receipt architecture separates three layers:

1. **Evidence substrate** — provider logs, traces, tool events, authorization records, source records, verification evidence, and other underlying artifacts.
2. **Canonical Activity Record** — a normalized machine-oriented record preserving actors, authority, sources, events, verification, incidents, and lineage.
3. **Activity Receipt View** — a compact human-facing representation derived from the canonical record.

Candidate record v0.1 makes the second-to-third-layer transition executable.

## Files

- `activity-record.schema.json` — candidate canonical-record JSON Schema.
- `derive_receipt.py` — deterministic derivation and validation utility.
- `examples/canonical-record.json` — synthetic source record.
- `examples/derived-receipt.json` — exact expected Receipt generated from that record.
- `activity-receipt.schema.json` — current candidate Receipt schema.

## Record identity

The canonical record requires:

- `record_id`;
- `record_schema_version`;
- `trace_id`;
- acting-system identity/version;
- normalized actors;
- delegated authority;
- sources;
- events;
- verification;
- incidents;
- integrity-generation metadata.

The record is intended to be richer than the Receipt. The Receipt should select and normalize **material** information rather than becoming another raw log.

## Materiality profile

Candidate record v0.1 uses explicit `material` booleans on:

- sources;
- events.

The derivation utility includes only material sources and material events in the Receipt.

A material event cannot reference a source marked non-material under this profile because the resulting Receipt would contain an unresolved provenance reference.

Incidents are currently treated as Receipt-relevant records. If an incident has an `event_id`, candidate v0.1 requires that event to be material. A future record version may add explicit incident materiality if realistic workflows require a larger incident substrate.

## Actor and delegation references

The record includes an `actors` registry.

The derivation validator requires:

- `system.agent_id` to resolve to an actor;
- `authority.principal` to resolve to an actor;
- `authority.delegate` to resolve to an actor;
- every event `actor_id` to resolve to an actor.

The current public Receipt uses a **direct-delegation profile**, so candidate record v0.1 also requires:

```text
authority.delegate == system.agent_id
```

This is deliberately narrow. It should be replaced or extended explicitly when multi-agent delegation chains, service accounts, organizations, or subagents are represented.

## Deterministic derivation

Run:

```bash
python derive_receipt.py examples/canonical-record.json
```

or:

```bash
python derive_receipt.py \
  examples/canonical-record.json \
  --output /tmp/derived-receipt.json
```

The built-in deterministic test is:

```bash
python derive_receipt.py --self-test
```

The self-test requires the derived value to match `examples/derived-receipt.json` exactly and then validates the result against the current Receipt schema and semantic invariant checker.

It also checks integrity behavior explicitly: recursive dictionary insertion-order changes do not alter the project-local digest; a non-material record mutation changes the record binding without otherwise changing the visible Receipt projection; and a material event mutation changes both the binding and the visible Receipt projection.

## Record hash profile

Candidate v0.1 calculates:

```text
sha256(
  UTF-8(
    JSON(record,
         sort_keys=true,
         separators=(",", ":"),
         ensure_ascii=false)
  )
)
```

The Receipt stores the resulting value as both:

- `integrity.record_hash`;
- `integrity.derived_from_record_hash`.

This is a **project-local deterministic serialization profile**. It is not presented as RFC 8785 JSON Canonicalization Scheme conformance.

The current record does not store its own hash inside itself, avoiding a self-referential hash field.

The current digest is a **content binding, not an authenticated attestation**. It does not prove signer identity, key ownership, non-repudiation, or that the underlying evidence is true. The project's current attestation direction is documented in [ATTESTATION.md](ATTESTATION.md). That design note also explains why the present serializer must not be described as RFC 8785 / JCS and why an established external envelope such as DSSE/in-toto is preferable to inventing custom signature fields.

If `integrity.previous_record_hash` exists on the canonical record, derivation copies it into the Receipt to preserve candidate lineage.

## Generated timestamp

For deterministic derivation, Receipt `integrity.generated_at` is taken from the canonical record's `integrity.generated_at` rather than using the wall clock at derivation time.

This means repeated derivation of the same record produces the same Receipt bytes after ordinary pretty-printing choices are normalized by the comparison logic.

## Semantic checks before derivation

The current derivation utility rejects:

- duplicate actor IDs;
- duplicate source IDs;
- duplicate event IDs;
- unknown actor references;
- unknown source references;
- unknown verification evidence references;
- unknown incident event references;
- direct-delegation mismatch;
- material events outside the authority time window;
- completed consequential actions without approved authorization;
- completed consequential actions outside authority.scope;
- missing or post-action authorization decision time for completed consequential actions;
- approved/completed operations that are explicitly prohibited;
- materially blocked/failed actions without a linked incident;
- confirmed verification without evidence references;
- material events that depend on non-material sources;
- verification evidence not represented in the material Receipt view;
- incident references to non-material events.

These pre-derivation checks intentionally mirror the corresponding Receipt-level governance invariants for the material view. The derived Receipt is still validated again using the public Receipt JSON Schema and executable invariant checker, providing two consistency layers rather than relying on the projection step to discover a bad canonical record.

## Evidence symmetry

Deterministic derivation helps enforce a narrow technical form of evidence symmetry:

- Receipt fields are copied or normalized from the canonical record;
- material events and sources are selected from registered record objects;
- the Receipt hash binds the view to the exact source record used for derivation.

This does **not** prove that the canonical record itself faithfully captured every raw log or real-world event. Evidence-substrate ingestion and source-to-record fidelity remain separate problems.

### External evidence index binding

The standalone external evidence-reference prototype now binds its index to the exact canonical record using the same project-local deterministic JSON + SHA-256 profile as Receipt derivation.

This lets an external evidence index prove which exact record bytes-under-profile it was prepared for, while keeping the index outside candidate-record-v0.1. It is still only a content binding; signer identity and authenticated attestation remain separate work.

See [C2PA-EVIDENCE-REFERENCES.md](C2PA-EVIDENCE-REFERENCES.md).

## Synthetic heterogeneous workflow pilot

A development-only pilot now exercises this derivation model across six synthetic paths: four direct canonical records plus the OpenTelemetry GenAI and MCP adapters.

See [WORKFLOW-PILOT.md](WORKFLOW-PILOT.md).

The pilot broadens engineering coverage across success, failure, blocking, pending actions, incident handling, verification variants, materiality filtering, and multiple ingestion paths. It remains synthetic and does not replace realistic-workflow testing.

## What this establishes

If the self-test and CI pass, the repository demonstrates that:

- one published synthetic canonical record conforms to the candidate record schema;
- the derivation algorithm produces the published expected Receipt deterministically;
- the derived Receipt conforms to the current candidate Receipt schema and implemented semantic invariants;
- the Receipt contains a SHA-256 binding to the exact parsed canonical record under the project-local serialization profile.

## What this does not establish

This prototype does not establish:

- cryptographic signing or non-repudiation;
- tamper-proof storage;
- RFC 8785/JCS conformance;
- complete capture of provider logs;
- correctness of the underlying evidence;
- standards conformance;
- safety or regulatory compliance;
- human audit benefit.

Those require separate implementation and evaluation.

## Next record work

The strongest next technical steps are:

- add explicit evidence-substrate references and ingestion provenance;
- decide how multi-agent delegation chains are represented;
- define signer identity, key-management, payload-type, trust, revocation, and freshness policy before implementing the documented attestation-envelope direction;
- extend the existing OpenTelemetry and MCP adapters to preserve richer evidence-substrate references;
- evaluate optional C2PA references for content-producing events;
- test derivation on heterogeneous realistic workflow traces.
