# Changelog

This changelog tracks public candidate-schema and validation changes for the AI Activity Receipt research repository.

The project is pre-commercial research. Version labels below describe repository artifacts, not standards releases.

## candidate-v0.2 — 2026-09-18

### Schema

- require `authority.valid_from` as well as `valid_until`;
- require `event_id` and `occurred_at` for every material action;
- add optional `authorization_decided_at`;
- require `integrity.generated_at`;
- retain closed-object validation to reject undeclared fields.

### Semantic validation

- require completed consequential actions to be approved and in delegated scope;
- require prior authorization-decision time for completed consequential actions;
- validate material-action timing against the authority window;
- require linked incidents for materially blocked/failed actions;
- require confirmed verification to cite evidence;
- reject inverted authority windows and Receipt generation times that precede represented activity;
- reject unresolved verification and incident references;
- reject duplicate material-source IDs and material-action event IDs;
- enforce the current direct-delegation profile (`authority.delegate == system.agent_id`);
- preserve private-reasoning exclusion diagnostics.

### Reproducibility

- replace the hard-coded three-fixture list with `examples/fixture-manifest.json`;
- expand the public repository suite to 19 synthetic fixtures;
- record expected invariant failures for negative fixtures;
- validate the JSON Schema itself before running fixtures;
- keep the GitHub Actions validation workflow as the public smoke test.

### Canonical Activity Record

- add a candidate canonical Activity Record JSON Schema;
- add normalized actor, source, event, authority, verification, incident, and integrity structures;
- add explicit source/event materiality flags;
- add deterministic `derive_receipt.py` transformation;
- add a project-local deterministic JSON serialization + SHA-256 record binding;
- add synthetic canonical-record and exact expected derived-Receipt fixtures;
- revalidate the derived Receipt against the public Receipt schema and semantic invariants in CI.

### MCP adapter

- add a candidate MCP 2026-07-28 `tools/call` capture -> Canonical Activity Record adapter;
- validate basic protocol/header/body capture consistency;
- keep self-reported `clientInfo` / `serverInfo` out of authenticated identity decisions;
- keep authorization, materiality, and consequentiality in a separate sidecar;
- add exact synthetic MCP capture -> canonical-record -> Receipt fixtures;
- verify that successful execution without separate approval evidence remains `unknown` and fails the consequential-action Receipt invariant;
- verify that tool arguments/results and self-reported implementation names are not copied into the canonical record;
- add CI coverage and an adapter design note.

### OpenTelemetry adapter

- add a candidate OTLP/JSON GenAI -> Canonical Activity Record adapter;
- extract trace, agent, provider/model, tool-operation, data-source, and error evidence from selected OpenTelemetry GenAI attributes;
- keep authority, materiality, and consequentiality in a separate sidecar rather than inferring them from telemetry;
- add exact synthetic OTLP -> canonical-record -> Receipt fixtures;
- verify that successful telemetry without authorization evidence remains `unknown` and fails the consequential-action Receipt invariant;
- verify that opt-in tool arguments/results are not copied into the canonical record;
- add CI coverage and a detailed adapter design note.

### Research

- add a dated interoperability research snapshot covering W3C PROV, OpenTelemetry GenAI, C2PA 2.4, MCP 2026-07-28, A2A, OAuth Rich Authorization Requests, and relevant NIST agent identity/authorization work;
- add an AR-P003 v0.3 preregistration draft using a fresh sealed corpus, randomized balanced incomplete-block assignment, explicit stale/incomplete/conflicting Receipt strata, and claim gates;
- add a deterministic component-level scorer with synthetic self-tests;
- add a JSON Schema for analysis-side response records;
- add a seeded balanced assignment generator with deterministic self-tests;
- add a neutral reviewer-instructions draft;
- add a SHA-256 freeze-manifest utility for future preregistration/corpus/scorer freezing.

## candidate-v0.1 — 2026-09

Initial public candidate schema, validator, illustrative Receipt, basic valid/invalid fixtures, validation record, invariant notes, roadmap, and GitHub Actions smoke test.
