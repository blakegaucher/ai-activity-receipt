# Validation Record

This document summarizes the current validation state of the **AI Activity Receipt** project.

> **Important:** Current evidence is synthetic and technical. Nothing documented here establishes real-world productivity improvement, safety improvement, legal compliance, standards conformance, or commercial effectiveness.

---

## AR-P003 v0.3 assignment-bound response integrity

**Status:** Synthetic engineering integrity check

Reviewer bundles now carry the exact assignment version and SHA-256 digest used to build them. The offline runner copies the binding into response exports, and the analysis-side merge requires the exact assignment file before producing scorer input.

Automated tests reject wrong assignment digests, wrong assignment versions, reviewer/case/order mismatches, reviewer-edited condition labels, hidden-stratum mismatches, and incomplete sessions.

This makes the frozen assignment authoritative for condition allocation rather than trusting a reviewer-editable export field. It does not authenticate the human reviewer or turn the pipeline into a production cryptographic trust system.

---

## AR-P003 v0.3 pipeline integration and privacy hardening

**Status:** Synthetic engineering integration test

The development pipeline now has an end-to-end smoke test spanning seeded assignment generation, case-package lint/build, condition-specific reviewer bundles, reviewer-side response structure, hidden-label merge, and the existing scorer.

The bundle builder also rejects any case whose set-valued gold answer cannot be represented by the visible material-action, material-source, or incident options. It records counts of gold, visible, and non-gold options for pre-freeze leakage review.

Common local reviewer bundles, hidden analysis material, response exports, scorer inputs, and private study-data directories are ignored by Git by default.

These controls reduce interface mismatch and accidental-publication risk. They do not establish that answer options are unbiased, that private files cannot be leaked by other means, or that the future human study is valid.

---

## AR-P003 v0.3 methodology decision-ledger guard

**Status:** Development governance control; no methodology choice is frozen

The current executable v0.3 draft and the earlier project research review contain material differences in comparison conditions, primary endpoint, timing semantics, and misleading-Receipt challenge design.

The repository now preserves those alternatives in a machine-readable decision ledger together with unresolved reviewer-population and meaningful-effect/precision choices. The validator requires protocol-version agreement, unique decision/candidate identifiers, evidence-linked rationale for any selected choice, and complete resolution of every pre-freeze methodology decision before a frozen protocol is permitted.

The freeze-readiness model now includes comparison-condition design as an explicit gate, so the existing two-condition implementation cannot silently become the confirmatory design merely because code already exists.

The checked-in methodology state remains `development_unresolved`. This adds preregistration discipline only; it does not select a method or add human evidence.

---

## AR-P003 v0.3 freeze-readiness guard

**Status:** Development governance control; current study remains not ready/frozen

The repository now publishes a machine-readable freeze-readiness state covering comparison-condition design, reviewer population, primary endpoint(s), effect/precision target, reviewer × case planning, sample allocation/stopping, sealed corpus, leakage validation, challenge strata, browser smoke evidence, reviewer instructions, assignment, timing/exclusions, scorer/analysis plan, ethics determination, and final freeze manifest.

The validator distinguishes `pending`, `prepared`, `complete`, and `not_applicable`. It rejects `complete`/`not_applicable` gates without evidence references, rejects `ready_for_freeze` while any pre-freeze gate is unresolved, rejects `frozen` while any gate is unresolved, and cross-checks the machine-readable protocol's version/frozen state.

The checked-in current state is deliberately `development_not_ready`.

Freeze readiness now also cross-checks the methodology ledger. A freeze gate that corresponds to an unresolved methodology decision cannot be marked resolved, and neither `ready_for_freeze` nor `frozen` may coexist with unresolved required methodology decisions. This closes the gap where readiness metadata and methodology metadata could otherwise drift independently.

A separate browser-smoke record schema/validator requires a real environment-specific record before browser validation can be claimed. The checked-in example is explicitly incomplete/not-run and cannot pass as completed smoke evidence.

This is continuity/preregistration discipline only. It does not make the missing methodology, ethics, corpus, browser, or human evidence decisions.

---

## AR-P003 freeze-manifest v0.2 self-test

**Status:** Development freeze-integrity tooling; no final confirmatory manifest exists

The freeze-manifest utility now binds the exact `protocol.json` version and SHA-256 instead of emitting a hard-coded abbreviated protocol version.

The self-test verifies:

- manifest JSON Schema validity;
- exact protocol version/hash binding;
- deterministic `freeze_content_id` independent of generation timestamp;
- artifact-byte changes alter artifact-set and freeze IDs;
- protocol changes alter the freeze ID;
- duplicate artifact paths are rejected;
- `--require-protocol-frozen` rejects an unfrozen protocol and accepts a synthetic frozen one.

This improves freeze integrity only. It does not resolve any preregistration, ethics, browser, corpus, analysis, or human-evidence gate.

---

## AR-P003 v0.3 manual case-methodology review guard

**Status:** Development QA workflow prepared; no sealed-corpus manual review completed

The repository now includes a structured analysis-side manual review record and validator for the final candidate corpus.

A review marked `complete` must:

- bind to the exact leakage-audit JSON by SHA-256;
- match the leakage audit's build-manifest SHA-256;
- cover exactly every audited case ID;
- bind to an audit with no unresolved automated high-risk cases;
- mark semantic leakage as `pass`;
- mark realism, framing neutrality, and answer-option quality as `acceptable`;
- mark each case decision `accept`.

The checked-in example is explicitly `not_tested` and cannot satisfy a complete-review requirement.

This turns the required human pre-freeze case review into a reproducible control without pretending that a template or self-test is evidence that the final corpus has been reviewed.

---

## AR-P003 v0.3 leakage/presentation audit smoke test

**Status:** Development-only pre-freeze methodology tooling

The repository now includes `benchmark/arp003_v0_3/audit_leakage.py` and `leakage-audit.schema.json`. The analysis-side audit consumes generated reviewer bundles, hidden gold labels, and the build manifest after packaging.

It checks that reviewer evidence is byte-equivalent across control/Receipt presentations for the same case, reports literal gold action/source/incident labels visible in the shared evidence, treats literal gold incident labels as high-risk because v0.2.3 exposed incident classes verbatim, reports answer-option sets that exactly equal the gold set, and quantifies Receipt presentation expansion relative to the shared evidence.

The audit self-test requires an intentionally leaked incident label to be flagged and rejects cross-presentation evidence drift.

Passing the audit does **not** prove absence of semantic leakage, framing effects, ecological-validity problems, or other human-study bias. Final sealed cases still require human pre-freeze review, and any high-risk flag must be resolved or explicitly justified before the leakage gate can be complete.

---

## AR-P003 methodology impact-map consistency check

**Status:** Development decision-support validation; no methodology selected

The repository now publishes a machine-readable impact map that covers every current candidate in the AR-P003 v0.3 methodology ledger. For each candidate it records the implementation class, artifacts that would change, and work that must be completed before execution.

The validator requires exact candidate coverage in both directions: every ledger candidate must appear exactly once in the impact map, and the impact map may not invent candidates absent from the ledger.

The earlier research review's proposed effect/guardrail thresholds (+5pp supported-completion benefit, 3pp accuracy noninferiority margin for a separate speed claim, +2pp maximum critical-false-clearance increase) are now preserved as an unresolved ledger candidate and explicitly remain non-normative decision assumptions.

This check reduces silent methodology drift. It does not choose a condition design, endpoint, timing clock, challenge architecture, reviewer population, or effect target.

---

## AR-P003 v0.3 offline runner smoke test

**Status:** Development instrumentation only; not a frozen human-study instrument

The repository now includes a self-contained browser runner, reviewer-bundle/response schemas, a hidden analysis schema, static offline/no-network checks, and an analysis-side response merge utility.

The runner now requires a pre-case comprehension gate before the first timed case. The gate checks neutral instruction understanding, records version/attempt count/pass time, and is rejected by the analysis merge if absent. It is instrument metadata rather than a scored endpoint.

The runner also requires an untimed structured practice reconstruction after the comprehension check. Study timing starts only after a correct practice answer. Response exports retain only practice version/attempt count/pass time; the practice answer is excluded from scorer input and the analysis merge rejects missing practice-gate metadata.

The runner records wall and active case time, manual pause/resume, browser hidden/visible events, technical issues, and inserts an untimed intermission between submitted cases. Reviewers use structured response controls rather than editing raw JSON.

Gold labels, hidden challenge strata, Receipt-state labels, and analysis-only metadata are excluded from reviewer-facing bundles and are joined only after response export. The merge utility requires an explicit `--timing active|wall` choice before scorer-compatible JSONL is produced.

Current automated tests verify schema/semantic separation, duplicate IDs, timing consistency, static no-network markers, hidden-analysis joins, protocol mismatch rejection, and compatibility with the existing scoring-record schema.

These checks do not establish browser/device compatibility, study validity, ethics approval, case realism, statistical power, or human benefit.

---

## Historical AR-P003 v0.2.3 auxiliary baseline

**Status:** Frozen historical synthetic benchmark; preserved separately from current v0.3 development

The earlier AR-P003 v0.2.3 corpus has freeze ID `8a381f4ae20a5f6824e513c7f96920fdf3cfe6b00b0b8d301127f5e0b659d0fd`.

C1, an auxiliary AI reviewer, completed all 80 frozen episodes: 40 control and 40 Receipt + raw logs. Every frozen non-timing endpoint was 100% in both conditions; timing was unavailable for all 80.

The result supports contract interpretability to that auxiliary AI reviewer. It does not demonstrate a Receipt accuracy advantage because the control condition was also at ceiling, and it cannot establish a speed or human-audit benefit because wall-clock timing/human evidence were absent.

A post-C1 methodology audit identified label leakage, presentation asymmetry, fixed class order, timing/runner limitations, JSON-entry burden, lack of bad-Receipt robustness, and a limited remaining human-reviewer design. The historical artifact therefore remains append-only and is not silently patched.

See [AR-P003 v0.2.3 Historical Frozen Baseline](AR-P003-V0.2.3-HISTORICAL-BASELINE.md).

---

## Continuity guard

**Status:** Repository-local consistency guard

The machine-readable `research/project-continuity-state.json` and `research/validate_continuity_state.py` protect a small set of high-risk continuity facts from silent drift:

- the frozen v0.2.3 freeze ID and C1 counts;
- v0.3 draft/not-executed state;
- current public direct-delegation profile;
- research-only status of multi-hop and DSSE work;
- claim gates for human benefit, safety, compliance, conformance, production signing, customer demand, and institutional endorsement;
- separation of ARC and Julia/DGAP research lanes from the Activity Receipt project.

The guard is not an external validator. It is a project discipline mechanism so later development does not accidentally rewrite frozen history or promote research status into unsupported claims.

---

## Repository security smoke test

**Status:** Repository-local defense-in-depth; not an independent security audit

The repository now runs `research/security_smoke_test.py` directly in CI and through the aggregate reproducibility suite.

The deterministic check verifies:

- the primary validation workflow explicitly grants only `contents: read`;
- `pull_request_target` is absent from the primary validation workflow;
- external Actions are pinned to full commit SHAs;
- checkout credential persistence is disabled;
- a finite workflow timeout and stale-run cancellation are present;
- Dependabot monitors pip and GitHub Actions;
- CODEOWNERS names the repository owner;
- private-study `.gitignore` guards remain present;
- the offline runner keeps a strict no-network CSP/boundary and bounded local input sizes;
- high-confidence private-key/token markers are absent from tracked text files.

These checks do not replace CodeQL, secret scanning, branch protection, private vulnerability reporting, penetration testing, or production security review.

---

## Aggregate reproducibility runner

**Status:** Public repository-local reproducibility helper

The repository now includes `research/reproduce.py`, which runs the current deterministic/synthetic checks in a fixed order and emits a JSON report containing per-check exit status, captured output, Python version, and SHA-256/byte-size metadata for the scripts, schemas, fixtures, protocol files, dependency declarations/lock, ignore rules, and CI workflow used by the run. CI uses CPython 3.12.14, an exact tested dependency snapshot, commit-pinned GitHub Actions, and publishes the generated report as a workflow artifact.

GitHub Actions runs the aggregate suite in addition to the individually named checks. This deliberately duplicates execution: the individual steps remain easy to diagnose, while the aggregate runner tests the exact one-command path available to an external reviewer.

Run:

```bash
python research/reproduce.py --output reproducibility-report.json
```

This is a reproducibility convenience layer. A project-authored green report does not constitute independent external reproduction, human-study evidence, standards conformance, production security validation, or real-world effectiveness.

---

## AR-P001 — Structural Validation

**Status:** Completed synthetic engineering pilot  
**Result:** 12 / 12 prespecified fixtures produced the expected accept/reject outcome.

### Purpose

Test whether the proposed AI Activity Receipt schema and invariant checker could enforce a small set of governance rules on synthetic AI-agent activity.

### Tested invariants

The pilot checked that:

1. required system, version, deployer, and task fields exist;
2. material sources cited by a result are registered;
3. a completed consequential action has prior approved authorization;
4. a prohibited action is not recorded as completed;
5. blocked unauthorized activity or tool failure produces an incident record;
6. completed consequential actions include an explicit verification state;
7. private chain-of-thought / hidden-reasoning fields are excluded.

### Public-repository reproduction note

AR-P001 and AR-P002 summarize earlier internal synthetic engineering suites and may use vocabulary from earlier schema iterations. The current public repository publishes a separate **21-fixture candidate-v0.2 reproducibility suite** using the present `system`, `authority.principal`, `authority.delegate`, provenance, action timing, authorization-decision timing, verification, incident, and integrity fields. The public workflow should not be described as a reproduction of all 12 AR-P001 or 24 AR-P002 historical cases unless those historical fixtures are separately published.

### Interpretation

AR-P001 supports the narrow conclusion that the schema and invariant checker behaved consistently on these synthetic fixtures.

It does **not** establish that the Receipt improves human auditing, incident reconstruction, productivity, or safety.

---

## AR-P002 — Expanded Engineering Validation

**Status:** Completed synthetic engineering checks  
**Result:** 24 / 24 historical internal v0.2 engineering fixtures behaved as expected.

The expanded fixture set covered areas including:

- authorization timing;
- event tampering;
- delegation;
- provenance;
- failed tool calls;
- incident linking;
- verification;
- private-reasoning exclusion.

### Interpretation

AR-P002 provides additional internal engineering evidence that the v0.2 design behaves as intended across a broader synthetic test set.

It remains an **internal engineering result**, not evidence of real-world effectiveness.

---

## Current public candidate-v0.2 reproducibility suite

**Status:** Public repository engineering smoke test  
**Manifest:** `examples/fixture-manifest.json`  
**Current cases:** 21 synthetic fixtures

The public suite tests both JSON Schema outcomes and semantic-invariant outcomes. Negative fixtures specify the invariant(s) expected to fire so the suite can detect a case that is rejected for the wrong reason.

Semantic invariants are evaluated only after structural validation succeeds because those checks assume schema-defined object shapes. This avoids turning malformed input such as a non-object `authority` value into an implementation exception. The private-reasoning exclusion scan still runs defensively on structurally invalid JSON values.

The current public cases exercise:

- required structural identity fields;
- registered and unique material-source identifiers;
- approved, in-scope, prior authorization for consequential completion;
- explicit prohibited-action contradictions;
- linked incident preservation for materially blocked/failed activity;
- inverted authority windows and action timing before/after the authority window;
- confirmed-verification evidence requirements;
- unresolved verification references;
- unresolved incident references;
- direct-delegation consistency;
- duplicate material-action event identifiers;
- private-reasoning-field rejection;
- generation timestamps that precede represented activity;
- malformed object shapes that must be rejected without crashing semantic validation;
- RFC 3339 date-time values missing a timezone offset.

The suite is intentionally a **repository reproducibility check**, not a measurement of human audit benefit, safety, compliance, or commercial performance.

---

## Canonical record derivation smoke test

**Status:** Public synthetic engineering check

The repository now publishes one candidate canonical Activity Record, an exact expected derived Receipt, and a deterministic derivation utility.

The self-test checks that:

- the canonical record satisfies `activity-record.schema.json`;
- actor/source/event references are internally resolvable under the candidate profile;
- non-material source/event records are excluded from the Receipt view;
- the derived Receipt exactly matches the published expected fixture;
- the derived Receipt passes the current Receipt schema and semantic invariant checker;
- repeated derivation is deterministic;
- canonical-record semantic checks reject denied completion, out-of-scope consequential actions, late/missing authorization decisions, prohibited approved completion, missing incidents for materially blocked/failed actions, actions outside the authority window, and confirmed verification without evidence;
- recursive dictionary insertion-order changes do not alter the project-local digest;
- a non-material record mutation changes the record binding while leaving the non-integrity Receipt projection unchanged;
- a material record mutation changes both the record binding and the visible Receipt projection;
- the Receipt carries a SHA-256 binding to the parsed source record under the documented project-local serialization profile.

This establishes only deterministic behavior for the published synthetic example and the stated project-local digest properties. It does not establish exact input-byte preservation, RFC 8785/JCS conformance, raw-log ingestion fidelity, cryptographic signing/non-repudiation, standards conformance, or real-world audit benefit.

---

## OpenTelemetry GenAI adapter smoke test

**Status:** Public synthetic interoperability engineering check

The repository now includes a candidate adapter that consumes one OTLP/JSON GenAI trace plus separate authority/materiality context and produces a canonical Activity Record.

The self-test checks that:

- the OTLP fixture maps exactly to the published expected canonical record;
- the canonical record passes the record schema and semantic checks;
- deterministic Receipt derivation exactly matches the published expected Receipt;
- the derived Receipt passes the Receipt schema and executable invariants;
- a successful consequential tool span without separate authorization evidence remains `unknown` and is rejected by the Receipt authorization invariant;
- opt-in tool arguments/results in the synthetic telemetry are not copied into the canonical record;
- nanosecond timestamp fractions survive OTLP-to-record conversion without microsecond truncation;
- malformed, duplicate, or all-zero OpenTelemetry trace/span identifiers are rejected;
- duplicate OTLP attribute keys and inverted span times are rejected;
- unsupported timestamp magnitudes fail as validation errors rather than escaping as runtime exceptions;
- malformed sidecar containers, dangling span-keyed governance entries, and unresolved material-source/source-role references are rejected.

This establishes only deterministic behavior on the published synthetic trace. It does not establish OpenTelemetry conformance, production telemetry completeness, authorization correctness, real-world interoperability, or human audit benefit.

---

## MCP 2026-07-28 adapter smoke test

**Status:** Public synthetic interoperability engineering check

The repository includes a candidate adapter that consumes captured MCP `tools/call` request/response interactions plus separate authenticated authority context and produces a canonical Activity Record.

The self-test checks that:

- the synthetic MCP capture maps exactly to the published expected canonical record;
- the canonical record passes the record schema and semantic checks;
- deterministic Receipt derivation exactly matches the published expected Receipt;
- the derived Receipt passes the Receipt schema and executable invariants;
- changing self-reported `clientInfo` does not alter the authenticated canonical system identity;
- a successful consequential tool call without separate approval evidence remains `unknown` and is rejected by the Receipt authorization invariant;
- a mismatched `Mcp-Name` routing header is rejected;
- duplicate case-insensitive MCP headers and non-JSON-RPC-2.0 envelopes are rejected;
- malformed sidecar list/object fields and dangling request-ID authorization/status evidence are rejected;
- sidecar record/trace IDs are not silently stringified from arbitrary JSON values;
- tool arguments/results and self-reported client/server names are not copied into the canonical record.

This establishes only deterministic behavior on the published synthetic capture. It does not establish MCP conformance, OAuth/OIDC correctness, authenticated identity verification, real-world interoperability, production security, or human audit benefit.

---

## DSSE research signing / verification smoke test

**Status:** Test-only cryptographic prototype; no production keys or trust roots

The repository signs the exact bytes of a synthetic candidate Activity Record in a DSSE v1 envelope using an ephemeral Ed25519 private key created only in process memory.

Verification separately checks the machine-readable trust policy, DSSE envelope structure, recognized payload type, DSSE pre-authentication encoding, Ed25519 signature, signer role/validity/threshold, Activity Record schema and semantics, deterministic Receipt derivation, Receipt invariants, and record-hash binding.

The self-test includes the upstream DSSE `HelloWorld` PAE vector, positive standard/URL-safe base64 verification, a valid signed record, and adversarial cases covering unknown key ID, wrong signing key, exact-byte payload mutation that preserves parsed JSON content, payload-type mutation, signature mutation, wrong verification key, malformed envelope, duplicate same-key signatures, signed schema-invalid record, signed semantic-invalid record, mismatched Receipt binding, and signer expiry. The verifier decodes the payload once and passes the same authenticated bytes to the JSON parser.

Private keys are not stored in the repository. This test does not deploy production identity issuance, key custody, revocation/status infrastructure, trusted timestamps, or production trust roots.

---

## Attestation trust-policy smoke test

**Status:** Research policy validation; no cryptographic signing implemented

The repository publishes a machine-readable candidate attestation trust-policy schema/example plus semantic validator.

The policy defines a project-controlled Activity Record payload-type URI, exact-payload-byte DSSE semantics, record-emitter/verifier roles, trusted signer identity types, verification-material references, key lifecycle requirements, required roles/signature threshold, and production revocation behavior.

The self-test requires one valid research policy and rejects duplicate signer/key identities, missing required-role signers, inverted validity windows, active test identities, test signers in production, production signers without revocation references, non-URI payload identifiers, unknown role/payload references, impossible signature thresholds, and attempted private-key fields.

This establishes only that the trust policy is explicit and mechanically checkable. It does not verify any digital signature or deploy a production identity/key-management system.

---

## External evidence-reference / C2PA smoke test

**Status:** Standalone research prototype; not integrated into candidate-record-v0.1

The repository publishes a generic external evidence-reference JSON Schema, a C2PA-oriented example, and a semantic validator.

The example links a synthetic canonical record to a C2PA content-provenance manifest reference, a C2PA 2.4 `c2pa.repository-receipt` anchor, and a separate authorization-decision reference.

The validator requires record identity match, exact canonical-record SHA-256 binding under the existing project-local deterministic serialization profile, unique evidence IDs, event/source subject resolution, explicit validator/time metadata before a reference may claim `state = valid`, and C2PA/profile/manifest-ID/URI information for repository-receipt references. Its self-test also verifies that a changed canonical record breaks the binding and that an arbitrary repository proof body cannot be inserted into the constrained locator object.

This demonstrates the external-reference design boundary only. It does not validate a real Content Credential, repository receipt, trust list, certificate, signature, or external authorization decision.

---

## Heterogeneous workflow derivation pilot

**Status:** Development-only synthetic workflow diversity check

The repository publishes four direct canonical-record workflow fixtures plus the existing OpenTelemetry GenAI and MCP adapter paths, for six total derivation cases.

The pilot requires canonical-record structural/semantic validity, deterministic Receipt derivation, Receipt schema/invariant validity, expected material-operation/source/incident/verification behavior, and explicit non-material-event filtering.

The six-case set must collectively exercise completed, failed, blocked, and pending execution; approved, denied, unknown, and not-required authorization; tool-failure and blocked-unauthorized-action incidents; confirmed, failed, pending, and uncertain verification; direct record ingestion; OpenTelemetry adaptation; and MCP adaptation.

Run:

```bash
python research/workflow_pilot.py
```

This is synthetic engineering coverage. It does not complete the roadmap item for realistic heterogeneous workflow traces or establish real-world capture fidelity or human audit benefit.

---

## candidate-record-v0.2 multi-hop migration smoke test

**Status:** Versioned future research profile; current candidate-record-v0.1 remains unchanged

The repository publishes `research/candidate-record-v0.2.schema.json`, a valid two-hop example, `candidate-receipt-v0.3.schema.json`, and `multi_hop_v02.py`.

The validator computes delegation-path continuity, effective scope by hop intersection, effective prohibitions by union, and the effective validity window. It requires complete native chains to carry active hops, recorded delegation decision times, and resolvable hop evidence.

The migration test converts a direct-delegation v0.1 record into a one-hop `legacy_partial` chain without inventing a delegation-decision timestamp, then requires the new Receipt to preserve the v0.1 human-visible core while exposing the delegation path/evidence state.

Adversarial cases cover broken continuity, cycles, authority amplification, revoked hops, missing complete-chain evidence, late delegation decisions, material actor mismatch, action outside the effective chain window, misuse of `legacy_partial` for multi-hop chains, and upstream prohibitions.

This does not replace the current canonical schema or claim authenticated multi-agent authorization.

---

## Delegation-chain prototype smoke test

**Status:** Standalone research prototype; not integrated into candidate-record-v0.1

The repository publishes a separate delegation-chain JSON Schema, valid example, and executable semantic validator under `research/`.

The prototype computes the effective actor path, scope intersection, and time-window intersection and rejects adversarial cases for:

- broken adjacent-hop continuity;
- cycles;
- downstream scope amplification;
- delegation decisions after the action;
- revoked hops;
- actions outside the effective time window;
- current-actor mismatch;
- completed consequential actions outside effective scope;
- action authorization decisions after execution;
- unresolved actors.

The self-test currently requires one valid multi-hop example plus ten adversarial mutations to behave as expected.

This prototype validates the candidate semantics only. It does not authenticate identities, validate OAuth tokens, implement revocation infrastructure, or change the current direct-delegation record schema.

---

## Multi-agent delegation design definition

**Status:** Design/research definition; not implemented in candidate-record-v0.1

The repository now defines a candidate future multi-hop delegation model with explicit invariants for ordered chain continuity, root/current actor continuity, cycle rejection, no authority amplification, scope intersection, time-window intersection, prior delegation decisions, actor resolution, action-in-scope checks, historical-vs-current authority separation, and revocation/expiry handling.

The design treats the current direct principal -> delegate profile as the one-hop special case and explicitly defers schema/validator implementation to a future versioned record profile.

The interoperability crosswalk also includes RFC 8693 Token Exchange concepts such as validated subject/current actor identity, scope/time evidence, nested `act` history, `may_act`, and raw-token exclusion.

This definition does not establish authenticated delegation or production authorization correctness.

---

## Cross-adapter normalization parity smoke test

**Status:** Public synthetic interoperability consistency check

The repository includes `adapters/cross_adapter_parity.py`, which adapts aligned synthetic OpenTelemetry GenAI and MCP episodes into the canonical record, derives Receipts, and compares a protocol-independent governance/action projection.

The self-test requires matching:

- aligned agent identity/version;
- principal/delegate/scope/prohibited authority fields;
- material operation, status, authorization, and consequentiality;
- verification state.

It simultaneously requires protocol-specific evidence to remain distinct, including trace identifiers, timestamps, and material-source provenance where the source fixtures differ.

A negative test removes separate MCP approval evidence and verifies that the action remains `unknown`, fails the existing Receipt authorization invariant, and no longer matches the authorized OpenTelemetry projection.

This is a single synthetic normalization check. It does not establish general cross-protocol interoperability, capture completeness, or standards conformance.

---

## Machine-readable interoperability mapping smoke test

**Status:** Public synthetic/research consistency check

The repository publishes a versioned machine-readable crosswalk covering OpenTelemetry GenAI, MCP 2026-07-28, W3C PROV, OAuth RAR, OAuth Token Exchange RFC 8693, C2PA 2.4, and A2A.

The mapping validator checks that:

- the crosswalk conforms to its JSON Schema;
- each mapped canonical target path still resolves against `activity-record.schema.json`;
- profile and mapping identifiers are unique;
- implemented-adapter profiles point to existing adapter files;
- self-reported descriptive identity cannot directly populate `system.agent_id`, `authority.principal`, or `authority.delegate`;
- selected sensitive tool payloads and bearer credentials remain excluded;
- the mapping artifact declares the same canonical record profile as the record schema.

The self-test mutates these rules and requires the validator to reject the unsafe or stale mapping.

This is a consistency tool for research mappings. It does not establish conformance or interoperability certification with any referenced standard.

---

## AR-P003 assignment-balance hardening

**Status:** Development assignment-tooling correction and regression test

Testing of the earlier greedy condition allocator found a design defect: it could keep each case close to 50/50 across conditions while leaving an individual reviewer with an avoidable 4/2 split when six cases were assigned.

The current generator first selects reviewer/case incidence while balancing case exposure, then assigns control/Receipt labels using a deterministic bipartite edge-coloring construction. Its self-tests require:

- no reviewer sees the same case twice;
- case exposure imbalance is at most one;
- reviewer condition imbalance is at most one;
- case condition imbalance is at most one;
- even-degree reviewer/case designs receive exact 50/50 local splits;
- odd-degree designs remain within one observation;
- mixed ordinary/stale/incomplete/conflicting strata preserve the local balance guarantees;
- repeated generation with the same seed is identical.

The generator emits reviewer-, case-, and stratum-level balance diagnostics. Stratum totals remain an inspection item before freeze rather than a guaranteed property.

This was found and corrected during development. No confirmatory human assignment or human outcome dataset was frozen under the superseded allocator.

---

## AR-P003 sample-size / precision planner smoke test

**Status:** Development planning/tooling check

The AR-P003 workspace includes a deterministic screening utility for:

- two-group binary accuracy differences;
- standardized continuous effect sizes;
- single-proportion precision;
- difference-in-proportions precision.

The utility supports explicit design-effect and unusable-observation inflation and can translate total case-observations into a rough reviewer-equivalent workload when cases/reviewer is supplied.

The self-test checks stable outputs for representative scenarios and rejects invalid planning inputs.

These formulas treat observations as independent before the explicit design-effect multiplier. Because AR-P003 is crossed by reviewer and case, this tool does **not** complete or freeze the confirmatory sample-size analysis. A final design must use frozen endpoint/effect targets plus justified reviewer/case variance assumptions or a crossed-design simulation/analysis.

---

## AR-P003 case-package linter smoke test

**Status:** Development governance/tooling check

The AR-P003 workspace now includes a case-package manifest schema and linter intended for development corpus preparation.

The linter checks that:

- the control and Receipt conditions share one declared underlying evidence file set, with the Receipt represented separately;
- reviewer-facing evidence and Receipt files are disjoint from analysis-only files such as gold labels;
- linked paths are relative, remain inside the package root, and exist;
- declared Receipt state matches ordinary/stale/incomplete/conflicting stratum;
- exact prespecified forbidden reviewer markers do not appear in reviewer-facing files;
- file hashes and sizes can be recorded for later freeze preparation.

The self-test requires rejection of reviewer/analysis overlap, path traversal, exact leakage markers, stratum/state mismatch, and missing files.

This is a mechanical corpus-preparation tool. It cannot establish realism, eliminate all semantic answer leakage, validate gold labels, or substitute for independent pre-freeze review.

---

## AR-P003 — Comparative Audit Reconstruction Benchmark

**Status:** Benchmark development and auxiliary reviewer testing  
**Primary human-benefit claim:** Not yet established.

### Research question

Given the same underlying AI-agent episode, can independent reviewers reconstruct:

- material actions;
- authorization state;
- material source provenance;
- incidents;
- verification state;

more accurately and/or faster when provided with a standardized AI Activity Receipt?

### Early auxiliary reviewer work

An early AR-P003 AI-reviewer pilot reviewed 80 synthetic episodes.

Its main value was methodological: it exposed problems in the benchmark design, including:

- action-ontology ambiguity;
- material-source ambiguity;
- invalid reviewer timing;
- verification-semantics confusion;
- scorer/instruction mismatches.

These results were retained as debugging evidence rather than converted into an effectiveness claim.

### Frozen v0.2.3 auxiliary result

A later auxiliary run reached ceiling-level performance on non-timing endpoints in both conditions.

That result did **not** establish a Receipt advantage because:

- control performance was also at ceiling;
- timing was unavailable;
- incident-label leakage was present;
- case ordering created learning/pattern risk;
- the human runner had timing-design problems;
- Receipt conditions contained substantially more displayed text.

The protocol therefore should not be silently altered and rescored as though it were confirmatory evidence.

---

## Current next benchmark — AR-P003 v0.3 direction

The preferred next step is a new human-centered benchmark using a fresh sealed corpus.

Planned improvements include:

- randomized case order;
- reduced answer leakage;
- realistic heterogeneous log formats;
- proper wall-clock timing;
- safer break handling;
- lower ceiling effects;
- explicit stale or incomplete Receipt cases;
- explicit Receipt/raw-evidence conflict cases;
- independent human reviewers;
- frozen endpoints before results are inspected;
- preservation of misses, abstentions, negative results, and defects.

The benchmark should compare:

1. **Control:** heterogeneous raw evidence only;
2. **Receipt:** the same underlying evidence plus a standardized Receipt.

For ordinary cases, the Receipt must not contain evidence that cannot be derived from the raw evidence.

---

## Candidate evaluation measures

Current measures of interest include:

- material-action reconstruction accuracy;
- authorization-violation detection;
- material-source attribution accuracy;
- incident classification accuracy;
- verification-state accuracy;
- time to final reconstruction;
- reviewer agreement;
- false incident flags;
- missing-evidence identification;
- reviewer confidence.

No single post-hoc composite score should replace the prespecified endpoints after results are inspected.

---

## Governance rules

The validation program follows these principles:

- Freeze the test corpus before evaluation.
- Freeze reviewer instructions and scoring rules before evaluation.
- Do not remove slow, confusing, failed, or negative cases after inspection.
- Do not tune a Receipt version on a test set and then present rescoring of that same set as independent confirmation.
- A schema change creates a new Receipt version.
- A confirmatory claim requires a fresh sealed evaluation set.
- Human reviewers are required for claims about human audit performance.
- AI reviewers may be used for debugging or auxiliary analysis.
- Private chain-of-thought is not required or collected.

---

## Current evidence boundary

At this stage, the project supports claims about:

- synthetic schema behavior;
- invariant-checking behavior;
- benchmark-development methodology;
- discovered evaluation defects;
- provenance and governance design.

It does **not yet support claims of**:

- proven human productivity improvement;
- proven human audit-time reduction;
- improved real-world safety;
- regulatory compliance;
- standards certification or conformance;
- commercial performance;
- superiority over existing standards or observability systems.

---

## Validation philosophy

Failures and null results are part of the project record.

The goal is not to make every experiment look successful. The goal is to develop an AI activity record that can survive increasingly difficult attempts to test, falsify, and audit it.
