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
- [Candidate Invariants](docs/INVARIANTS.md)
- [Validation Record](docs/VALIDATION.md)
- [Project Roadmap](docs/ROADMAP.md)
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

The receipt is intended to summarize and index evidence, **not invent new facts**.

### Information currently represented

The current prototype/design work includes:

- run / trace identity;
- agent, human, organization, and tool actors;
- principal-to-agent delegated authority;
- bounded scope and time-limited authorization;
- material source and resource provenance;
- tool and action events;
- authorization / policy decisions;
- verification state and supporting evidence;
- incidents and mitigation records;
- timestamps and trace links;
- a compact human-readable summary;
- SHA-256-linked integrity records for tamper detection.

Private chain-of-thought, hidden scratchpads, passwords, tokens, and unnecessary sensitive prompt content are intentionally outside the receipt model.

---

## Illustrative receipt

The example below is **illustrative, not a frozen normative schema**.

```json
{
  "receipt_id": "AR-example-001",
  "trace_id": "trace-example-001",
  "system": {
    "agent_id": "agent-4",
    "version": "example-version"
  },
  "authority": {
    "principal": "user-2",
    "scope": ["read", "analyze"],
    "valid_until": "2026-09-12T12:31:59Z"
  },
  "material_sources": [
    {"source_id": "src-A", "role": "supports_result"}
  ],
  "material_actions": [
    {
      "operation": "send_email",
      "status": "blocked",
      "authorization": "denied"
    }
  ],
  "verification": {
    "state": "pending"
  },
  "incidents": [
    {"type": "blocked_unauthorized_action"}
  ],
  "integrity": {
    "derived_from_record_hash": "sha256:example"
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

The invalid fixture is intentionally expected to be **structurally valid but semantically rejected**. A passing test suite therefore means the validator correctly accepts the valid fixtures and rejects that governance-inconsistent fixture.

### AR-P003 — comparative audit reconstruction benchmark

AR-P003 was created to test whether reviewers can reconstruct agent activity more accurately and/or faster when given a standardized Receipt in addition to the same underlying evidence.

The first auxiliary AI-reviewer work was useful mainly because it exposed benchmark defects. A later frozen auxiliary run reached ceiling-level non-timing results in both control and Receipt conditions, while timing was unavailable and answer-leakage/design issues remained.

That means the current AR-P003 auxiliary results **do not support a claim that the Receipt improves auditability or productivity**.

The preferred next step is a new human-centered benchmark with:

- fresh sealed cases;
- randomized reviewer order;
- reduced answer leakage;
- better timing instrumentation;
- explicit stale/incomplete/conflicting-Receipt cases;
- frozen endpoints and claim gates before inspection;
- independent human reviewers as the primary evidence arm.

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

Current research directions include compatibility or crosswalk work with:

- **W3C PROV / PROV-O**
- **OpenTelemetry**
- content-provenance approaches such as **C2PA**
- emerging AI-agent identity, authorization, incident-reporting, and evaluation practices.

No standards-conformance claim is made here.

---

## Roadmap

Near-term work:

1. refine and version the canonical Activity Record and Receipt view;
2. publish deterministic schema/invariant examples;
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
