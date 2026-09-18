# Heterogeneous Workflow Derivation Pilot — Synthetic v0.1

> **Status:** Development-only synthetic pilot.  
> **Snapshot:** 2026-09-18  
> This is not a human study, production deployment, or claim of real-world workflow fidelity.

The repository now exercises the Canonical Activity Record -> Activity Receipt pipeline across several different synthetic workflow shapes instead of relying only on one canonical happy-path fixture.

## Included cases

The pilot includes four direct Canonical Activity Records plus the two existing protocol-adapter paths.

### Direct canonical records

1. **Research -> analysis -> email**
   - material research sources;
   - one deliberately non-material cache event;
   - completed consequential email;
   - confirmed verification.

2. **Document analysis -> failed upload**
   - document source with URI/hash metadata;
   - completed read/analysis;
   - approved but failed consequential upload;
   - linked `tool_failure` incident;
   - failed verification.

3. **Administrative form -> denied/blocked submit**
   - form source;
   - completed read;
   - denied and blocked consequential submit;
   - linked `blocked_unauthorized_action` incident;
   - pending verification.

4. **Report creation -> pending publication**
   - source-backed report creation;
   - consequential publication remains pending;
   - authorization remains unknown;
   - uncertain verification.

### Adapter paths

5. Existing synthetic OpenTelemetry GenAI -> Canonical Record -> Receipt flow.
6. Existing synthetic MCP 2026-07-28 -> Canonical Record -> Receipt flow.

## What the pilot checks

For every case, the pilot requires:

- canonical-record schema validity;
- canonical-record semantic validity;
- deterministic Receipt derivation;
- derived Receipt schema validity;
- derived Receipt invariant validity.

The direct-record cases also assert expected:

- material operation sequence;
- material source IDs;
- incident classifications;
- verification state;
- exclusion of declared non-material events from the Receipt.

Across the full six-case set, the pilot requires coverage of:

- execution states: `completed`, `failed`, `blocked`, `pending`;
- authorization states: `approved`, `denied`, `unknown`, `not_required`;
- incidents: `tool_failure`, `blocked_unauthorized_action`;
- verification states: `confirmed`, `failed`, `pending`, `uncertain`;
- direct canonical-record ingestion;
- OpenTelemetry GenAI adaptation;
- MCP adaptation.

## Reproduce

Run:

```bash
python research/workflow_pilot.py
```

The command prints a JSON summary for all six synthetic cases and fails if any record, derivation, Receipt, or expected coverage condition fails.

## Why this matters

A single example can accidentally encode assumptions that only work for one workflow. This pilot exercises several materially different combinations:

- successful consequential action;
- failed consequential action;
- denied/blocked action;
- pending consequential action;
- confirmed/failed/pending/uncertain verification;
- material/non-material filtering;
- source-backed and adapter-produced records.

That gives the project a stronger engineering signal before moving to genuinely heterogeneous real-world or independently produced traces.

## Evidence boundary

Passing this pilot demonstrates **synthetic workflow diversity and deterministic consistency only**.

It does not establish:

- complete or accurate real-world capture;
- production observability;
- authorization authenticity;
- interoperability conformance;
- human audit benefit;
- safety or regulatory compliance.

The roadmap item for testing **realistic heterogeneous workflow traces** therefore remains open. This synthetic pilot is a preparatory milestone, not a substitute for that work.
