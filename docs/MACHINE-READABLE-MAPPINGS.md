# Machine-Readable Interoperability Crosswalk — Candidate v0.1

> **Status:** Non-normative research artifact.  
> **Snapshot:** 2026-09-18  
> These mappings do not claim standards conformance, certification, authenticated identity, or implementation completeness.

The repository now publishes a machine-readable version of the interoperability crosswalk:

- `mappings/interoperability-v0.1.json`
- `mappings/interoperability-map.schema.json`
- `mappings/validate_mappings.py`

The goal is to make interoperability assumptions inspectable and testable instead of leaving them only in prose.

## What a mapping means

Each mapping records:

- the external source/profile;
- the source field or concept;
- the current candidate decision:
  - `map` — normalized into a canonical-record field;
  - `support` — useful evidence for a canonical field but not sufficient by itself;
  - `exclude` — intentionally not copied into the record;
  - `no_equivalent` — no dedicated current record field;
- the evidence class;
- the canonical target path when one exists;
- any transformation;
- a boundary note.

A mapping does **not** mean that the external source and AI Activity Receipt are semantically identical.

## Profiles currently represented

Candidate v0.1 includes:

- OpenTelemetry OTLP + developing GenAI semantic conventions;
- MCP 2026-07-28;
- W3C PROV / PROV-O;
- OAuth 2.0 Rich Authorization Requests (RFC 9396);
- C2PA 2.4;
- the current A2A development specification.

OpenTelemetry and MCP are marked `implemented_adapter` because this repository contains synthetic adapters for them. The other profiles remain research mappings.

## Canonical-target validation

The mapping validator resolves every `target_path` against `activity-record.schema.json`.

For example:

```text
events[].operation
sources[].source_id
authority.scope
system.agent_id
```

If a future record-schema change removes or renames one of those fields, the mapping test fails until the crosswalk is updated.

That turns schema drift into a visible CI failure.

## Safety-oriented semantic checks

The validator includes two deliberately conservative mapping rules.

### Self-reported identity cannot become security identity

Mappings based on self-reported descriptive metadata such as MCP `clientInfo`, `serverInfo`, or an A2A Agent Card cannot directly populate:

- `system.agent_id`;
- `authority.principal`;
- `authority.delegate`.

Authenticated identity must come from separate evidence.

### Sensitive content remains excluded

Known sensitive payload/credential sources such as:

- OpenTelemetry tool arguments/results;
- MCP tool arguments/result content;
- access tokens;
- refresh tokens;
- client secrets;

must remain marked `exclude`.

This is intentionally narrower than a complete data-loss-prevention system. It protects the specific content-minimization rules already adopted by the project.

## Adapter coupling

Profiles marked `implemented_adapter` must reference an adapter file that actually exists in the repository.

Current examples:

```text
opentelemetry-genai -> adapters/otel_genai.py
mcp-2026-07-28     -> adapters/mcp_2026.py
```

If the path disappears or is renamed without updating the mapping artifact, CI fails.

## Reproducible test

Run:

```bash
python mappings/validate_mappings.py
```

The self-test verifies:

1. the mapping document conforms to its JSON Schema;
2. every canonical target path resolves against the current Activity Record schema;
3. profile and mapping identifiers are unique;
4. implemented-adapter paths resolve;
5. self-reported descriptive identity cannot be promoted into security-sensitive identity fields;
6. sensitive payload/credential mappings cannot be changed from `exclude` without failing;
7. the declared record-schema profile matches the canonical schema profile.

## Why this is useful

A prose crosswalk is good for explanation, but it is easy for prose and code to drift apart.

The machine-readable artifact gives the project a place to record and test decisions such as:

- which external identifiers are copied;
- which values are normalized;
- which sources are merely supporting evidence;
- what is intentionally excluded;
- which concepts have no current equivalent;
- which mappings have executable adapters.

This should make later adapter/version changes easier to review.

## Versioning rule

The mapping file is versioned separately from the Activity Record and Receipt schemas.

A mapping update should change the mapping version when it changes externally visible semantics, such as:

- adding a new source profile;
- changing a source-to-target relationship;
- changing a transformation;
- changing an exclusion rule;
- adopting a new external specification revision.

Editorial note changes alone do not necessarily require a new mapping version.

## Known limitations

Candidate v0.1 does not:

- prove external standards conformance;
- validate source documents over the network during CI;
- execute third-party conformance suites;
- authenticate any external identity;
- prove that an adapter captured every relevant event;
- model every field in the referenced specifications;
- express a complete ontology;
- replace the detailed prose interoperability notes.

The machine-readable crosswalk is a testable research index, not a standards certificate.

## Current design conclusion

The crosswalk supports the project's existing architectural separation:

1. **observed execution**;
2. **descriptive identity**;
3. **authenticated identity**;
4. **authorization evidence**;
5. **provenance/source evidence**;
6. **verification/incidents**;
7. **integrity/attestation**.

External protocols can contribute evidence to one or more of those layers without being treated as interchangeable.
