# AI Activity Receipt — Project Continuity Snapshot

> **Snapshot date:** 2026-09-18  
> **Purpose:** Keep future work aligned across conversations, repository artifacts, historical benchmark files, business notes, and public documentation.  
> This is a continuity record, not a standards release, funding claim, or experimental result.

## 1. Project identity

**AI Activity Receipt** is the flagship technical research project of **Blake Gaucher / Ancient Immortal Art**.

The core design remains:

```text
evidence substrate
      |
      v
Canonical Activity Record
      |
      v
human-facing Activity Receipt
```

The project records observable/auditable facts such as system identity, delegated authority, material actions, provenance/source roles, authorization state, verification state, incidents, timestamps, and integrity links.

Private chain-of-thought is explicitly excluded.

## 2. Historical benchmark continuity

### AR-P003 v0.2.3

The v0.2.3 benchmark is a frozen, append-only historical artifact.

Freeze ID:

```text
8a381f4ae20a5f6824e513c7f96920fdf3cfe6b00b0b8d301127f5e0b659d0fd
```

C1, the auxiliary AI reviewer, completed all 80 frozen episodes:

- 40 control;
- 40 Receipt + raw logs;
- 100% on every frozen non-timing endpoint in both conditions;
- timing unavailable.

This supports contract interpretability to that AI reviewer, not a Receipt accuracy or speed advantage.

See [AR-P003 v0.2.3 Historical Frozen Baseline](AR-P003-V0.2.3-HISTORICAL-BASELINE.md).

### AR-P003 v0.3

The repository contains v0.3 **development/preregistration preparation**, not a completed human study.

Current direction includes:

- ordinary evidence-symmetric cases;
- stale/incomplete/conflicting Receipt challenge strata;
- balanced randomized assignment;
- objective reconstruction endpoints;
- reliable study-system timing;
- fresh sealed corpus;
- frozen scorer/exclusions/analysis plan;
- ethics/REB/IRB review or determination as applicable before recruitment.

Do not silently retrofit v0.3 improvements into v0.2.3.

## 3. Current public engineering stack

The public repository currently includes:

- candidate Activity Receipt schema and executable invariant checker;
- canonical Activity Record schema and deterministic derivation;
- Receipt-to-record SHA-256 binding under the documented project-local serialization profile;
- pre-derivation canonical governance checks;
- OpenTelemetry GenAI adapter prototype;
- MCP 2026 evidence adapter prototype;
- cross-adapter governance-action parity test;
- machine-readable interoperability mapping;
- standalone delegation-chain prototype;
- versioned multi-hop `candidate-record-v0.2` / `candidate-receipt-v0.3` research profile with loss-aware v0.1 migration;
- C2PA/external-evidence-reference research profile;
- machine-readable attestation trust policy;
- research-only DSSE v1 + Ed25519 signing/verification prototype using ephemeral test keys;
- heterogeneous synthetic workflow derivation pilot;
- one-command public reproducibility runner with SHA-256 artifact manifest;
- AR-P003 development scoring, assignment, case-package linting, planning, and freeze-manifest tooling.

These are engineering/research capabilities. They do not establish human benefit or production readiness.

## 4. Integrity and attestation boundary

The project now distinguishes four layers:

1. **record content binding** — deterministic project-local JSON serialization + SHA-256;
2. **external evidence binding** — a separately bound external evidence-reference index;
3. **test-only cryptographic attestation** — DSSE v1 + Ed25519 research prototype;
4. **production trust** — still open and requires real identity issuance, protected private-key storage, revocation/status infrastructure, deployment trust roots, and an appropriate timestamp/history model.

A valid signature does not replace action authorization, source truth, or verification of the underlying activity.

## 5. Delegation boundary

The current public canonical record remains the direct-delegation `candidate-record-v0.1` profile.

A separate research profile implements multi-hop delegation as `candidate-record-v0.2` with:

- ordered hops;
- continuity and cycle checks;
- scope intersection;
- prohibition union;
- effective time-window intersection;
- explicit hop evidence state;
- loss-aware migration from v0.1.

Promotion of v0.2 into the public canonical schema path remains a future decision.

## 6. Reproducibility state

The repository exposes:

```bash
python research/reproduce.py --output reproducibility-report.json
```

This aggregate runner executes the current deterministic/synthetic public checks and records SHA-256 hashes for important artifacts.

A project-authored passing run is **preparation for external reproducibility**, not independent validation.

Phase 6 remains open until an independent party can reproduce, critique, or implement the work without undocumented project knowledge.

## 7. Evidence and claim gates

Keep these statements stable unless new evidence changes them:

- current public evidence is primarily synthetic/technical;
- no proven human productivity benefit;
- no proven human audit-accuracy advantage;
- no proven real-world safety benefit;
- no legal or regulatory compliance claim;
- no standards-conformance/certification claim;
- no claim of NIST, C2PA, OpenTelemetry, MCP, FedDev, Two Rivers, or other institutional endorsement/adoption unless an explicit source establishes it;
- no production-signing claim from the research DSSE prototype;
- no real-world customer-demand or pricing claim from technical development alone.

Negative and null results remain part of the record.

## 8. Cross-project boundaries

### ARC / ARC-AGI-2

ARC solver work is a separate competition/research lane.

Generic methods may be shared — provenance, frozen evaluation, append-only history, exact verification, negative-result preservation — but AI Activity Receipt schemas or benchmark claims must not be merged into ARC results.

The ARC lane should continue under its own frozen BUILD/TUNING/AUDIT governance.

### Julia / DGAP / meta-anchor research

Julia/DGAP recognition research remains separate from the Activity Receipt product/research lane.

Human-facing anchor labels are not AI Activity Receipt schema primitives and are not ARC primitives.

### Business / Ancient Immortal Art

Ancient Immortal Art remains early-stage, pre-revenue, and in planning/validation.

The AI Activity Receipt has stronger technical development than the other business concepts, but technical progress alone does not prove product-market fit.

Commercial readiness still requires identifiable buyers/workflows, customer validation, delivery-cost evidence, pricing/revenue hypotheses, and realistic business planning.

## 9. External correspondence continuity

NIST-related work should be represented as submitted comments/acknowledgements and requirements feedback, not endorsement.

The human-centered direction carried into AR-P003 remains consistent with the external-comment theme:

- observable evidence rather than private reasoning;
- traceability from short view to underlying record;
- objective reconstruction outcomes;
- missing-evidence detection;
- stale/incomplete/conflicting summary robustness;
- privacy-aware audit views.

Business/government correspondence should likewise remain evidence of discussion/routing, not adoption or funding.

## 10. Tasks that can continue without fabricating external evidence

The project can continue to improve:

- realistic-but-clearly-labeled development traces and ingestion tooling;
- migration/versioning tests;
- external evidence-substrate integration design;
- interoperability tests against independently maintained protocol implementations;
- AR-P003 runner/interface tooling before freeze;
- sealed-corpus construction procedures;
- reproducibility packaging;
- public documentation and evidence boundaries.

The following must remain open until the required external/human evidence exists:

- independent external reproduction;
- human AR-P003 outcome claims;
- ethics/REB/IRB determination where applicable;
- production signer/key/revocation deployment;
- actual customer-demand/pricing validation;
- financing readiness;
- standards certification/conformance;
- institutional endorsement/adoption.

## 11. Immediate continuity rule

Before changing a frozen benchmark, public schema version, claim boundary, or cross-project boundary:

1. identify the current source artifact;
2. preserve the historical version;
3. create a new version/branch instead of rewriting history;
4. run the reproducibility suite;
5. record negative results and limitations;
6. update this continuity snapshot or its dated successor.

This keeps later conversations from silently collapsing historical results, research prototypes, business hypotheses, and current public claims into one state.
