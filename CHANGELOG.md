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

### Dependency refresh after security hardening

- update immutable GitHub Actions pins after Dependabot review and full green CI: checkout 7.0.1, setup-python 7.0.0, and upload-artifact 7.0.1;
- advance the supported `cryptography` range to `>=50.0.1,<51` and the exact CI lock to 50.0.1 after the DSSE, security, AR-P003, and aggregate reproducibility checks passed;
- correct the dependency-snapshot metadata date to 2026-09-19 and record the tested dependency/action versions in machine-readable continuity state.

### AR-P003 freeze-manifest v0.2 integrity hardening

- replace the hard-coded abbreviated protocol version in the manifest utility with the exact version read from the bound protocol file;
- bind the manifest to protocol path, SHA-256, and frozen-state flag;
- add sorted artifact-set SHA-256 and deterministic `freeze_content_id` independent of generation timestamp;
- reject duplicate artifact paths and support a final-freeze fail-closed `--require-protocol-frozen` mode;
- add a machine-readable manifest schema and adversarial/self-consistency tests;
- keep the freeze-manifest readiness gate at `prepared` because no final frozen artifact set exists.

### Continuity-state version drift correction

- synchronize the machine-readable continuity state with reproducibility suite v0.10 and reviewer-response contract v0.4;
- explicitly record automated leakage audit and bound manual case review as prepared development controls whose final-corpus executions remain not run;
- strengthen the continuity guard to reject silent drift in reviewer bundle/response contract versions, reproducibility version, and leakage/manual-review evidence state;
- derive current reproducibility and runner-contract versions from their authoritative source files rather than duplicating those expected values inside the guard;
- preserve historical benchmark results and human-evidence gates unchanged.

### AR-P003 bound manual case-review guard

- add a machine-readable analysis-side review record for semantic leakage, realism, framing neutrality, answer-option quality, and accept/revise/drop disposition;
- bind the manual review to the exact leakage-audit file and corpus build hash;
- require a complete review to cover every audited case and reject completion while any automated high-risk leakage flag remains;
- add a deliberately `not_tested` checked-in template, validator self-tests, CI coverage, and reproducibility-suite coverage;
- keep the leakage-validation gate at `prepared` until a real sealed corpus has both a clean audit and completed human methodology review.

### AR-P003 leakage/presentation audit hardening

- add an analysis-side pre-freeze audit over generated reviewer bundles plus hidden gold;
- fail closed when the shared reviewer evidence drifts across control/Receipt presentations for the same case;
- flag literal gold incident labels in control evidence and report literal gold action/source labels for human review;
- flag non-empty answer-option sets that exactly equal the gold set;
- quantify Receipt presentation expansion relative to the same shared evidence and surface large expansion as a review signal;
- add a machine-readable report schema, deterministic self-test, CI coverage, and aggregate reproducibility coverage;
- keep the leakage-validation gate at `prepared`, not `complete`, until the final sealed corpus is audited and manually reviewed.

### AR-P003 methodology decision ledger

- preserve material differences between the current executable v0.3 draft and the earlier project research-review recommendations instead of silently reconciling them;
- add a machine-readable ledger covering comparison conditions, primary endpoint, timing clock, misleading-Receipt challenge architecture, reviewer population, and meaningful effect/precision target;
- add a validator that requires unique decisions/candidates, evidence-linked rationale for selected choices, protocol-version agreement, and complete pre-freeze methodology resolution before a frozen protocol is permitted;
- add comparison-condition design as an explicit freeze-readiness gate;
- wire the ledger into CI, aggregate reproducibility, protocol metadata, freeze-readiness evidence, continuity, and the remaining-gates dashboard;
- keep every listed methodology choice unresolved in this update; no human-study or favorable-outcome claim is created.

### AR-P003 crossed reviewer × case planning

- add a deterministic Monte Carlo planner that uses the repository's balanced reviewer/case assignment rather than treating reviewer-case observations as independent;
- simulate binary outcomes with explicit reviewer and case random intercepts;
- estimate the condition contrast with additive two-way cluster-robust covariance (reviewer + case - reviewer/case intersection);
- report simulated marginal performance, risk-difference variability, median cluster-robust SE, rejection-rate sensitivity, Monte Carlo error, and assignment diagnostics;
- add an illustrative scenario grid centered on the earlier 108 reviewer / 72 case / 24 cases-per-reviewer planning proposal without freezing those counts or the example effect/variance assumptions;
- add CI and aggregate reproducibility coverage;
- keep crossed-design readiness at `prepared`, not `complete`, until the primary endpoint/effect target and variance assumptions are frozen.

### Remaining-gates dashboard

- add a concise operational dashboard separating repository-complete engineering work from owner/admin, human-study, independent-reproduction, production-trust, realistic-workflow, and commercialization gates;
- link each actionable repository gate to its tracked GitHub issue;
- make explicit that additional technical activity cannot substitute for customer validation, human evidence, external reproduction, or repository-admin settings;
- define the change-control sequence for updating a gate without silently upgrading adjacent evidence classes.

### License-governance preflight

- inventory direct Python dependencies, external GitHub Action repositories, the exact transitive lock-package name snapshot, and the DSSE reference implementation;
- record observed upstream license files for the direct dependencies/actions without treating the inventory as legal clearance;
- add a repository license-decision preflight covering code, documentation, synthetic fixtures, future human-study material, and cross-lane competition reuse;
- add a deterministic drift check so direct requirements/workflow Action repositories cannot silently change without updating the inventory;
- keep the repository's actual license status as **not selected** and preserve issue #44 as an owner decision gate;
- include the preflight in CI and the aggregate reproducibility suite.

### CodeQL advanced setup and continuity refresh

- add and verify a separate pinned CodeQL advanced-setup workflow for Python and JavaScript/TypeScript;
- keep the primary validation workflow read-only while granting the CodeQL workflow only the required `security-events: write` in addition to `contents: read`;
- extend the repository security smoke test to enforce CodeQL Action pinning, scoped permissions, checkout credential hardening, timeout, and language coverage;
- record successful pull-request and post-merge `main` CodeQL runs without claiming that the uninspectable alert inventory is empty;
- update machine-readable continuity so CodeQL default setup is no longer treated as a pending task;
- retain main ruleset, private vulnerability reporting, Dependabot security settings, security notifications, and alert inspection as explicit manual/admin gates.

### External reproduction handoff

- add a public clean-room handoff for independent reproduction attempts;
- require exact commit/environment recording, exact-lock installation, aggregate-suite execution, and preservation of favorable or unfavorable outcomes;
- separate ordinary reproducibility findings from sensitive security reports and prohibit participant/hidden-analysis/secrets in public reports;
- document that public repository visibility does not imply broad reuse rights while the explicit license decision remains open;
- keep actual independent reproduction as an external gate that project-authored documentation cannot satisfy.

### Repository security hardening

- add weekly Dependabot version-update configuration for pip dependencies and GitHub Actions;
- add CODEOWNERS metadata for default and security/evidence-sensitive paths;
- keep the primary validation workflow at `contents: read`, disable checkout credential persistence, apply a 20-minute job timeout, and cancel obsolete in-progress runs for the same ref;
- add a deterministic repository security smoke test and include it in the aggregate reproducibility suite;
- tighten the AR-P003 offline runner CSP to deny-by-default network/resource loading while retaining only required inline script/style execution;
- add bounded reviewer-bundle/response/analysis cardinality and content sizes plus browser-side file/nesting/resource guards;
- document manual GitHub-admin gates for main-branch ruleset/protection, CodeQL default setup, private vulnerability reporting, and Dependabot security alerts/updates;
- preserve the boundary that repository hardening is not a production security audit or compliance claim.

### AR-P003 exact assignment binding

- bump development reviewer-bundle and response-export contracts to v0.2;
- include the exact assignment version and SHA-256 digest in reviewer bundles and response exports;
- require the exact frozen assignment when joining reviewer responses to hidden analysis labels;
- reject reviewer IDs absent from the assignment, missing/extra cases, case-order drift, edited control/Receipt labels, stratum disagreement, wrong assignment version/hash, and incomplete sessions;
- treat the frozen assignment as the analysis-side source of truth for condition allocation rather than trusting a response-export field;
- extend unit/integration tests and protocol/runner documentation while keeping the human study unfrozen.

### Repository reviewer/contributor health

- add a pull-request template that requires evidence-boundary, validation, privacy, frozen-history, and third-party provenance checks;
- add a dedicated reproducibility issue form for independent reproduction reports and undocumented setup mismatches;
- add a research security policy that separates non-sensitive bug reporting from sensitive vulnerability/participant-data handling;
- add CITATION.cff metadata so outside reviewers can cite the repository and exact commit they used;
- link the new reviewer/contributor resources from the README and reproducibility documentation.

### Continuity after pipeline hardening

- advance the machine-readable continuity snapshot to v0.2;
- record the development bundle builder, gold-option representability guard, and end-to-end AR-P003 integration smoke test;
- record the pinned CPython/dependency/Actions reproducibility profile and CI report artifact;
- record that contribution/data-safety guidance exists while the explicit repository-license decision remains open;
- extend the continuity guard so later changes to the reproducibility profile or licensing state require an explicit continuity update.

### Reproducibility and study-pipeline hardening

- pin CI to CPython 3.12.14 and an exact tested dependency snapshot while retaining `requirements.txt` as the supported-range declaration;
- pin GitHub Actions dependencies to exact commit SHAs and publish the machine-readable reproducibility report as a CI artifact;
- add a root `.gitignore` covering Python/editor noise plus common AR-P003 reviewer, hidden-analysis, response, scorer-input, and private local output paths;
- fail reviewer-bundle construction when a hidden gold set-valued answer cannot be expressed by the visible answer options;
- emit analysis-side answer-option diagnostics so exact-gold option sets and distractor counts can be reviewed before freeze;
- add an end-to-end synthetic AR-P003 integration test from seeded assignment through bundle build, reviewer response, hidden-label merge, and scoring;
- add contribution/data-safety guidance and explicitly document that no repository license has yet been selected rather than silently assigning one.

### AR-P003 v0.3 reviewer-bundle build pipeline

- connect seeded reviewer/case assignments and linted case-package manifests to the development offline runner;
- require assignment hidden-stratum metadata to agree with each case manifest before packaging;
- emit control bundles with shared evidence only and Receipt bundles with the same evidence plus the Receipt;
- keep gold reconstruction and hidden strata in a separate analysis bundle that is never reviewer-facing;
- require configured gold files to already be declared analysis-only in the case package;
- emit a SHA-256 build manifest for assignment/config inputs and generated reviewer/analysis artifacts;
- refuse silent output-directory overwrite and fail on non-UTF-8 evidence in the current text-only runner profile;
- add deterministic self-test, CI, and aggregate reproducibility coverage.

### Browser-smoke coverage for pre-case gates

- extend the manual browser/device smoke schema to require explicit comprehension-gate and practice-gate flow checks;
- update the checked-in smoke template with both new checks as `not_tested`;
- keep issue #38 open until these and the existing browser/accessibility/timing checks are performed in real target environments.

### AR-P003 untimed structured practice case

- add one fixed synthetic practice reconstruction after the comprehension gate and before the first timed study case;
- use the same structured action/source/incident/authorization/verification/missing-evidence concepts as the study interface;
- keep practice untimed and start session/case timing only after a correct response;
- record only practice version, attempt count, and pass timestamp;
- bump the development response export to v0.4 and require practice metadata;
- reject scoring-side merges that lack valid practice-gate evidence;
- keep practice answers outside scorer input and human-study outcome data;
- document that final training content remains unfrozen and must be checked for coaching effects.

### AR-P003 pre-case comprehension gate

- add a neutral three-question instruction check before the first timed case;
- require reviewers to understand Receipt/source-evidence conflict handling, private chain-of-thought exclusion, and pause/visibility timing behavior;
- start session/case timing only after the comprehension gate is passed;
- record only gate version, attempt count, and pass timestamp in reviewer response exports;
- bump the development response-export schema to v0.3 and require comprehension metadata;
- reject analysis-side merges that lack valid comprehension-gate evidence;
- extend runner validation and end-to-end pipeline tests.

### AR-P003 freeze-readiness and smoke-evidence guards

- add a machine-readable v0.3 freeze-readiness state for all major preregistration, corpus, browser, analysis, ethics, assignment, timing, and freeze-manifest gates;
- distinguish pending/prepared/complete/not-applicable so engineering preparation cannot silently become a completed evidence gate;
- reject ready-for-freeze or frozen status when required gates remain unresolved;
- cross-check readiness protocol version/frozen state against `protocol.json`;
- add a structured manual browser/device smoke-record schema that binds results to exact runner commit/hash and records environment, per-check status, and defects;
- keep the checked-in smoke record deliberately incomplete/not-run so CI cannot be misread as browser evidence;
- add CI and aggregate reproducibility coverage.

### AR-P003 v0.3 development offline runner

- add a self-contained offline reviewer interface with no external scripts, hosted APIs, telemetry, or network calls;
- replace raw JSON answer editing with structured action/source/incident/authorization/verification/missing-evidence/confidence controls;
- record both wall and active timing plus manual pause, page visibility, and technical-interruption state;
- insert a safe intermission between cases so breaks do not contaminate the next case timer;
- keep gold labels, challenge strata, Receipt-state labels, and analysis-only metadata outside the reviewer-facing bundle;
- add separate reviewer-bundle, response-export, and hidden-analysis schemas plus an analysis-side merge utility;
- require explicit active-vs-wall timing choice when preparing scorer input rather than silently choosing after outcomes;
- add static offline/no-network checks, bundle/response validation, merge tests, CI coverage, and aggregate reproducibility coverage;
- keep the runner explicitly development-only until browser/device testing, endpoint/timing rules, ethics determination, corpus, assignment, and analysis are frozen.

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
