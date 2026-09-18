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

### Continuity synchronization

- add a dated cross-source project continuity snapshot covering frozen benchmark history, current engineering profiles, claim gates, cross-project boundaries, and open external/human gates;
- publish the frozen AR-P003 v0.2.3 C1 auxiliary baseline separately from v0.3 development, including the 80/80 ceiling result, unavailable timing, and post-C1 methodology limitations;
- add a machine-readable continuity state and guard that fails if the historical freeze ID/counts, current draft/public-profile state, protected claim gates, or ARC/Julia lane boundaries silently drift;
- run the continuity guard directly in CI and through the one-command reproducibility suite;
- keep business correspondence, standards feedback, and competition work as context/evidence boundaries rather than technical validation claims.

### Aggregate reproducibility runner

- add a one-command runner for the current public deterministic/synthetic validation stack;
- continue through all checks and return non-zero if any fail;
- emit a machine-readable JSON report with per-check command, exit status, stdout/stderr, Python version, and explicit evidence boundary;
- hash the important scripts, schemas, fixtures, protocol artifacts, requirements, and CI workflow with SHA-256 so the report identifies the artifact set actually exercised;
- run the aggregate reproduction path in CI in addition to the individually named steps;
- document that this prepares for, but does not itself satisfy, independent external reproduction.

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

### candidate-record-v0.2 multi-hop profile

- add a versioned future canonical-record research schema with ordered delegation hops;
- add candidate-receipt-v0.3 with compact delegation path and evidence-state fields;
- compute effective scope by intersection, prohibitions by union, and time window by intersection;
- require complete native chains to preserve hop decision/evidence data and active state;
- add loss-aware migration from candidate-record-v0.1 that explicitly marks missing historical delegation-decision time instead of inventing it;
- require migrated Receipts to preserve the prior human-visible core;
- add ten adversarial multi-hop/migration tests and CI coverage;
- leave promotion of v0.2 into the public canonical schema path as a separate decision.

### DSSE protocol-conformance hardening

- check the prototype against upstream DSSE Protocol 1.0.2 and its published `HelloWorld` PAE vector;
- accept both standard and URL-safe base64 encodings as required by DSSE;
- decode the payload once and pass the same authenticated bytes to the application parser, avoiding a second payload extraction after verification;
- keep the local requirement for `keyid` explicitly scoped as an application trust-policy profile rather than a claim that DSSE itself requires it;
- extend CI/self-test coverage for the upstream PAE vector and URL-safe envelopes.

### DSSE research signing / verification prototype

- add a constrained DSSE v1 envelope schema and exact PAE implementation;
- add Ed25519 signing and verification using ephemeral in-memory test keys only;
- enforce the machine-readable signer/trust policy separately from signature mathematics;
- verify Activity Record schema/semantics, deterministic Receipt derivation, and exact record/Receipt binding after signature verification;
- demonstrate that JSON formatting changes can preserve the project-local parsed-record digest while invalidating the exact-byte DSSE signature;
- reject unknown key IDs, wrong keys, payload/signature/type mutation, malformed envelopes, duplicate same-key signatures, signed invalid records, mismatched Receipts, and expired signers;
- add CI coverage and keep production signing separately gated on real identity/key/revocation infrastructure.

### Attestation trust-policy definition

- define the project-local Activity Record DSSE payload-type URI and exact-payload-byte semantics;
- add machine-readable signer roles, trusted signer identities, verification-material references, key-lifecycle requirements, signature thresholds, and revocation behavior;
- require DSSE `keyid` to remain a lookup hint rather than authenticated identity;
- keep cryptographic signature validity separate from action authorization;
- reject test-only identities in production policies and require active production signers to carry revocation/status references;
- add one valid research policy plus ten adversarial policy mutations and CI coverage;
- clear the research design prerequisites for a future DSSE prototype while keeping production signing gated on real identity/key/revocation infrastructure.

### External evidence-index record binding

- add an explicit `record_binding` object to the standalone external evidence-reference profile;
- bind the index to the exact canonical Activity Record with the same project-local deterministic JSON + SHA-256 profile used by Receipt derivation;
- require validator-side recomputation rather than trusting the stored digest;
- add adversarial tests for a forged digest and a canonical record changed after the index was created;
- keep this as a standalone research artifact rather than silently changing candidate-record-v0.1.

### C2PA and external evidence-reference evaluation

- evaluate C2PA 2.4 content provenance, `c2pa.ai-disclosure`, and `c2pa.repository-receipt` as optional external evidence rather than fields to copy into candidate-record-v0.1;
- add a standalone generic external evidence-reference JSON Schema, synthetic C2PA-oriented example, semantic validator, and adversarial self-tests;
- require evidence references to identify the canonical subject they support and separate location/binding from explicit validation state;
- require `state = valid` to name a validator and validation time rather than treating a URI as proof of successful validation;
- keep repository-specific C2PA proof bodies outside the candidate index;
- mark the C2PA evaluation milestone complete while leaving future canonical-schema/evidence-index integration versioned and open.

### Heterogeneous workflow derivation pilot

- add four synthetic direct canonical-record workflows covering research/email success, document upload failure, blocked administrative submission, and pending publication;
- combine those with the existing OpenTelemetry GenAI and MCP adapter paths for six derivation cases;
- require deterministic record-to-Receipt derivation and schema/invariant validity for every case;
- assert expected material operations, sources, incidents, verification state, and non-material filtering;
- require aggregate coverage of completed/failed/blocked/pending execution, approved/denied/unknown/not-required authorization, major incident types, and four verification states;
- add CI coverage while keeping realistic heterogeneous workflow testing explicitly open.

### Canonical-record invariant parity

- enforce key Receipt governance rules on the canonical material event set **before** derivation;
- reject completed consequential events without approved authorization, in-scope operation, and prior authorization-decision time;
- reject approved/completed prohibited operations and material events outside the authority window;
- require linked incidents for materially blocked/failed events and evidence references for confirmed verification;
- add deterministic adversarial self-tests for denied completion, scope violation, late/missing authorization, prohibited completion, missing incident, authority-window violation, and evidence-free confirmation;
- retain post-derivation Receipt validation as a second consistency layer.

### Delegation-chain executable prototype

- add a standalone JSON Schema and valid example for the future multi-hop delegation design;
- add an executable validator for continuity, cycles, scope amplification/intersection, time-window intersection, decision ordering, actor resolution, active-hop state, effective action scope, and action-authorization timing;
- add one valid and ten adversarial deterministic self-test cases;
- report the computed actor path, effective scope, and effective delegation window for valid chains;
- add CI coverage under a separate `research/` prototype path so candidate-record-v0.1 remains unchanged.

### Multi-agent delegation design

- define a future versioned multi-hop delegation-chain model while keeping candidate-record-v0.1 as the direct-delegation profile;
- specify continuity, acyclicity, no-authority-amplification, scope intersection, time-window intersection, prior-decision, actor-resolution, and revocation/expiry invariants;
- distinguish delegation provenance from current authorization evidence;
- map W3C PROV `actedOnBehalfOf` and OAuth Token Exchange RFC 8693 concepts into the design without treating either as complete authorization proof;
- add RFC 8693 to the machine-readable interoperability crosswalk, including current actor, scope/time evidence, nested historical actor chains, `may_act`, and raw-token exclusion;
- defer schema implementation to a versioned future record/Receipt profile rather than changing candidate-record-v0.1 in place.

### Cross-adapter normalization parity

- add a synthetic OpenTelemetry/MCP parity harness that aligns identity/authority context and compares the derived substrate-independent governance/action projection;
- require matching normalized operation, status, authorization, consequentiality, authority, identity, and verification semantics while preserving protocol-specific trace/time/provenance differences;
- add a negative parity case proving that successful MCP execution without separate approval evidence remains `unknown` and breaks parity with an authorized OpenTelemetry action;
- add CI coverage and interoperability/validation documentation without claiming general protocol conformance.

### Adapter integrity hardening

- harden MCP capture parsing against duplicate case-insensitive routing headers, non-JSON-RPC-2.0 envelopes, malformed sidecar container shapes, dangling request-ID governance entries, and arbitrary-value identifier stringification;
- harden OpenTelemetry ingestion against duplicate semantic attributes, duplicate span IDs, inverted span times, unsupported timestamp magnitudes, malformed sidecar containers, dangling span-keyed evidence, and unresolved material-source/source-role references;
- fail closed on these malformed/stale capture states rather than silently ignoring or coercing them;
- expand adapter self-tests and documentation while preserving the boundary that internal consistency is not authentication or source-truth verification.

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
