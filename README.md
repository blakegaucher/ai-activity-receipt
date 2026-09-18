# AI Activity Receipt

**Human-centered, provenance-aware records for consequential AI-agent activity.**

> **Status:** Pre-commercial research and development. Current evidence is synthetic/technical; this repository does **not** claim proven productivity, safety, legal compliance, standards conformance, or commercial advantage.

AI Activity Receipt is an independent research project by **Blake Gaucher / Ancient Immortal Art** exploring a simple question:

> When an AI system performs meaningful work, what should a human be able to verify afterward?

The project is developing a **model-neutral activity record and human-facing receipt** for agent runs. The goal is to make consequential AI activity easier to inspect without exposing private chain-of-thought.

---
## Project resources

- [Sample Activity Receipt](examples/sample-receipt.json)
- [Valid authorization fixture](examples/valid-completed-authorized-action.json)
- [Intentionally invalid authorization fixture](examples/invalid-completed-with-denied-authorization.json)
- [Candidate JSON Schema](activity-receipt.schema.json)
- [Candidate Canonical Activity Record Schema](activity-record.schema.json)
- [Canonical Record Design and Derivation](docs/CANONICAL-RECORD.md)
- [Integrity and Attestation Direction](docs/ATTESTATION.md)
- [Multi-Agent Delegation Design](docs/MULTI-AGENT-DELEGATION.md)
- [Canonical Record Example](examples/canonical-record.json)
- [Expected Derived Receipt](examples/derived-receipt.json)
- [Candidate Invariants](docs/INVARIANTS.md)
- [Terminology and Field Semantics](docs/TERMINOLOGY.md)
- [Fixture expectation manifest](examples/fixture-manifest.json)
- [Validation Record](docs/VALIDATION.md)
- [Interoperability Research Snapshot](docs/INTEROPERABILITY.md)
- [Machine-Readable Interoperability Crosswalk](docs/MACHINE-READABLE-MAPPINGS.md)
- [OpenTelemetry GenAI Adapter Prototype](docs/OTEL-ADAPTER.md)
- [MCP 2026-07-28 Adapter Prototype](docs/MCP-ADAPTER.md)
- [AR-P003 v0.3 Preregistration Draft](docs/AR-P003-V0.3-PROTOCOL.md)
- [AR-P003 v0.3 Reviewer Instructions Draft](docs/AR-P003-V0.3-REVIEWER-INSTRUCTIONS-DRAFT.md)
- [AR-P003 v0.3 Benchmark Workspace](benchmark/arp003_v0_3/README.md)
- [Project Roadmap](docs/ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Executable validator](validate_receipts.py)
---
## The problem

AI-agent activity is often fragmented across provider logs, application traces, tool calls, policy systems, approval records, and human confirmations.

That makes basic governance questions harder than they should be:

- Which system or agent acted?
- Who delegated authority to it?
- What was it allowed to do, and for how long?
- Which sources materially supported the result?
- Which tools or external actions occurred?
- Were consequential actions approved before execution?
- Was the result independently verified?
- Were failures, blocked actions, or other incidents preserved?

AI Activity Receipt aims to organize those answers into a compact, inspectable record backed by underlying evidence.

---

## Current design direction

The project is being developed around three layers:

1. **Evidence substrate** — raw traces, provider logs, application events, authorization records, and other source evidence.
2. **Canonical Activity Record** — a normalized, append-oriented machine record that preserves identities, authority, provenance, events, verification, incidents, and integrity links.
3. **Activity Receipt View** — a compact human-facing summary derived from the canonical record.

A candidate canonical-record schema and deterministic derivation utility are now published. The synthetic derivation test filters non-material source/event records, generates a Receipt, binds it to the parsed canonical record under a documented project-local SHA-256 serialization profile, and validates the result against the Receipt schema/invariants.

The receipt is intended to summarize and index evidence, **not invent new facts**.

### Information currently represented

The current prototype/design work includes:

- run / trace identity;
- agent, human, organization, and tool actors;
- principal-to-agent delegated authority in the current direct-delegation profile;
- multi-hop delegation is defined as a future versioned extension, not silently implemented in candidate-record-v0.1;
- bounded scope and time-limited authorization;
- material source and resource provenance;
- tool and action events;
- authorization / policy decisions;
- verification state and supporting evidence;
- incidents and mitigation records;
- timestamps and trace links;
- a compact human-readable summary;
- SHA-256-linked content bindings for deterministic change detection and lineage experiments.

Private chain-of-thought, hidden scratchpads, passwords, tokens, and unnecessary sensitive prompt content are intentionally outside the receipt model.

---

## Illustrative receipt

The example below is **illustrative, not a frozen normative schema**.

```json
{
  "receipt_id": "AR-example-001",
  "trace_id": "trace-example-001",
  "record_schema_version": "example-v0.2",
  "receipt_version": "example-v0.2",
  "system": {
    "agent_id": "agent-4",
    "version": "example-version"
  },
  "authority": {
    "principal": "user-2",
    "delegate": "agent-4",
    "scope": ["read", "analyze"],
    "prohibited": ["send_email"],
    "valid_from": "2026-09-13T15:00:00Z",
    "valid_until": "2026-09-13T16:00:00Z"
  },
  "material_sources": [
    {"source_id": "src-A", "role": "supports_result"}
  ],
  "material_actions": [
    {
      "operation": "send_email",
      "status": "blocked",
      "authorization": "denied",
      "consequential": true,
      "event_id": "event-blocked-1",
      "occurred_at": "2026-09-13T15:15:00Z",
      "source_refs": ["src-A"]
    }
  ],
  "verification": {
    "state": "pending"
  },
  "incidents": [
    {
      "type": "blocked_unauthorized_action",
      "event_id": "event-blocked-1"
    }
  ],
  "integrity": {
    "record_hash": "sha256:example-record-hash",
    "derived_from_record_hash": "sha256:example-record-hash",
    "generated_at": "2026-09-13T15:30:00Z"
  }
}
```

---

## Validation status

### AR-P001 — structural validation

**12 / 12** prespecified synthetic fixtures produced the expected accept/reject outcome.

The pilot tested invariants including required identity/version fields, registered material sources, prior authorization for consequential completed actions, prohibited-action handling, incident creation, verification state, and exclusion of private chain-of-thought.

**What this establishes:** the pilot schema + invariant checker behaved consistently on those fixtures.

**What it does not establish:** real-world audit benefit, incident-reconstruction benefit, productivity, or safety.

### AR-P002 — expanded engineering checks

**24 / 24** new synthetic v0.2 fixtures behaved as expected, covering authorization timing, event tampering, delegation, provenance, failed tools, incident linking, verification, and private-reasoning exclusion.

These remain **internal engineering checks**, not external effectiveness evidence.

### Repository validation automation

The public repository includes a candidate JSON Schema, semantic-invariant fixtures, an executable Python validator, and a GitHub Actions workflow. The automated check is intended to confirm that the published examples continue to produce their prespecified structural and semantic outcomes as the repository changes.

Run locally with:

```bash
python -m pip install -r requirements.txt
python validate_receipts.py
```

The public fixture manifest currently covers **21 synthetic cases**. It includes valid Receipts, structurally valid but semantically invalid Receipts, and structurally invalid Receipts. Negative fixtures also record the invariant(s) expected to fire so a test cannot silently pass for the wrong reason.

A passing suite means the current candidate schema and executable invariant checker produced the prespecified outcomes for those 21 public fixtures. It does **not** reproduce the complete historical AR-P001/AR-P002 fixture suites summarized above and does not establish real-world effectiveness.

### AR-P003 — comparative audit reconstruction benchmark

AR-P003 was created to test whether reviewers can reconstruct agent activity more accurately and/or faster when given a standardized Receipt in addition to the same underlying evidence.

The first auxiliary AI-reviewer work was useful mainly because it exposed benchmark defects. A later frozen auxiliary run reached ceiling-level non-timing results in both control and Receipt conditions, while timing was unavailable and answer-leakage/design issues remained.

That means the current AR-P003 auxiliary results **do not support a claim that the Receipt improves auditability or productivity**.

A candidate **AR-P003 v0.3 preregistration draft and scoring workspace are now published**. They specify:

- fresh sealed cases distinct from development fixtures;
- randomized balanced incomplete-block assignment;
- no reviewer seeing the same underlying case in both conditions;
- system-captured timing and prespecified timing failure rules;
- explicit stale/incomplete/conflicting-Receipt challenge strata;
- component-level endpoints rather than a post-hoc composite;
- a schema-validated scoring-record format;
- seeded reviewer/case assignment tooling;
- freeze hashes for protocol/corpus/scorer artifacts;
- independent human reviewers as the evidence arm required for any human-benefit claim.

The v0.3 protocol is **not frozen or executed**. Reviewer population, primary endpoint/effect target, sample size or precision analysis, final corpus, ethics determination as applicable, and final freeze manifest still must be completed before confirmatory human data collection.

---

## Research principles

- **Evidence symmetry:** a normal Receipt should contain only information derivable from the underlying evidence.
- **Versioned evaluation:** changing the schema or scorer requires a new version and, for confirmatory work, a new sealed evaluation set.
- **Preserve failures:** negative results, abstentions, defects, and confusing cases stay in the record.
- **No post-hoc score tuning:** endpoints are frozen before comparative results are inspected.
- **Human-centered evaluation:** AI reviewers may help debug, but they do not substitute for human evidence when the claim concerns human audit performance.
- **No chain-of-thought requirement:** auditability should come from observable actions, authority, evidence, and verification — not hidden reasoning traces.

---

## Interoperability direction

AI Activity Receipt is intended to **map to, not replace**, existing observability and provenance systems.

A dated [Interoperability Research Snapshot](docs/INTEROPERABILITY.md) records candidate crosswalks and boundaries for:

- **W3C PROV / PROV-O**;
- **OpenTelemetry and the developing GenAI semantic conventions**;
- **C2PA 2.4 / Content Credentials**;
- **MCP 2026-07-28**;
- **Agent2Agent (A2A)**;
- **OAuth 2.0 Rich Authorization Requests (RFC 9396)**;
- relevant **NIST AI-agent identity and authorization** work.

Executable interoperability prototypes are published for both [OpenTelemetry GenAI](docs/OTEL-ADAPTER.md) and [MCP 2026-07-28](docs/MCP-ADAPTER.md). Both target the canonical Activity Record before Receipt derivation, deliberately separate observed execution from authorization evidence, and minimize copied protocol content. A [machine-readable candidate crosswalk](docs/MACHINE-READABLE-MAPPINGS.md) now records and validates source-to-record mapping decisions across OpenTelemetry, MCP, PROV, OAuth RAR, OAuth Token Exchange, C2PA, and A2A.

These remain research mappings and synthetic engineering tests. No standards-conformance, certification, endorsement, production-readiness, or real-world interoperability claim is made here.

---

## Roadmap

Near-term work:

1. refine the published candidate Canonical Activity Record and test deterministic Receipt derivation on more realistic traces;
2. expand deterministic schema/invariant examples;
3. freeze and run the next human-centered AR-P003 benchmark;
4. publish null, negative, and positive results together;
5. develop interoperability mappings;
6. test the approach with realistic agent workflows and, later, external pilot partners.

---

## Why this matters

Powerful AI outputs are not enough for consequential workflows.

For many real-world uses, people also need a compact answer to:

**What happened, under whose authority, using what evidence, with what verification, and what went wrong?**

AI Activity Receipt is an attempt to make that answer inspectable.

---

## Project identity

Independent research by **Blake Gaucher / Ancient Immortal Art**.

See the broader profile: https://github.com/blakegaucher
