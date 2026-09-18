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
- expand the public repository suite to 21 synthetic fixtures;
- record expected invariant failures for negative fixtures;
- validate the JSON Schema itself before running fixtures;
- gate semantic invariant evaluation behind structural validity so malformed object shapes cannot crash the validator;
- retain the private-reasoning scan as a defensive diagnostic even when structure is invalid;
- add malformed-authority and offset-naive timestamp regression fixtures;
- keep the GitHub Actions validation workflow as the public smoke test.

### Canonical Activity Record

- add a candidate canonical Activity Record JSON Schema;
- add normalized actor, source, event, authority, verification, incident, and integrity structures;
- add explicit source/event materiality flags;
- add deterministic `derive_receipt.py` transformation;
- add a project-local deterministic JSON serialization + SHA-256 record binding;
- add synthetic canonical-record and exact expected derived-Receipt fixtures;
- revalidate the derived Receipt against the public Receipt schema and semantic invariants in CI.

### Integrity / attestation research

- document the current SHA-256 record binding as a project-local, non-authenticated content digest;
- add self-tests showing dictionary insertion order does not change the digest under the project serializer;
- add self-tests showing non-material record changes still change the record binding while leaving the visible Receipt projection otherwise unchanged;
- add self-tests showing material record changes alter both the binding and the visible Receipt projection;
- document why the current serializer is **not** claimed as RFC 8785 / JCS;
- identify DSSE / in-toto-style external envelopes as the leading future attestation direction while deferring signing code until signer/key/trust semantics are defined.

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
- preserve OTLP Unix-nanosecond timestamp precision when producing RFC 3339 record timestamps;
- validate OpenTelemetry trace/span identifier widths and reject all-zero identifiers;
- add CI coverage and a detailed adapter design note.

### Machine-readable interoperability crosswalk

- add a versioned JSON crosswalk for OpenTelemetry GenAI, MCP 2026-07-28, W3C PROV, OAuth RAR, C2PA 2.4, and A2A;
- add a JSON Schema for mapping artifacts;
- validate every canonical target path against the current Activity Record schema;
- require implemented-adapter profiles to reference repository adapter files;
- prevent self-reported descriptive identity such as MCP client/server metadata or an A2A Agent Card from being directly promoted into security-sensitive identity targets;
- require selected tool payload/credential mappings to remain excluded;
- add CI coverage and documentation for mapping-version semantics.

### AR-P003 assignment hardening

- replace the development-only greedy condition allocator after testing exposed possible reviewer-level 4/2 splits for six-case workloads;
- use deterministic balanced bipartite edge coloring after case selection;
- guarantee control-vs-Receipt condition imbalance of at most one for every reviewer and every case;
- preserve exact 50/50 splits for even-degree reviewers/cases;
- add reviewer-, case-, and stratum-level condition diagnostics;
- add mixed-strata, even-degree, odd-degree, and deterministic-repeat self-tests;
- record that no confirmatory human assignment or dataset was frozen under the superseded development allocator.

### AR-P003 sample-size / precision planning

- add a development-only planner for two-group binary endpoints, standardized continuous endpoints, and confidence-interval precision;
- support explicit design-effect and unusable-observation inflation rather than silently treating reviewer-case observations as independent;
- add rough reviewer-equivalent workload translation while labeling it as non-power arithmetic;
- publish an illustrative sensitivity grid showing how required observations change with assumed effect size;
- add deterministic self-tests and CI coverage;
- keep the final sample-size/precision milestone open until the reviewer population, primary endpoint/effect target, variance/clustering assumptions, allocation, and stopping rule are frozen.

### AR-P003 corpus-preparation tooling

- add a development case-package JSON Schema that structurally encodes the same-evidence-plus-Receipt condition contract;
- add a linter that keeps reviewer-facing evidence/Receipt files separate from analysis-only gold files;
- reject absolute/traversing/missing case-package paths and reviewer/analysis file overlap;
- require stale/incomplete/conflicting strata to use matching declared Receipt states;
- scan exact prespecified forbidden reviewer markers across reviewer-facing files;
- emit SHA-256/size reports for linked case files to support later freeze preparation;
- add adversarial self-tests and CI coverage;
- add a protocol-level requirement for case-package lint/leakage scanning before confirmatory freeze.

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
