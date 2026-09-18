# AI Activity Receipt — Interoperability Research Snapshot

> **Research snapshot:** 2026-09-18  
> **Status:** Candidate mapping, non-normative. This document records research direction; it does not claim conformance, certification, endorsement, or compatibility testing.

AI Activity Receipt is intended to sit **above** existing telemetry, identity, authorization, provenance, and content-authenticity systems. The Receipt should summarize and index evidence produced by those systems rather than replace them.

This snapshot records the strongest current mapping opportunities and the limits that should remain explicit.

---

## 1. W3C PROV / PROV-O

**Reference:** W3C Recommendation, *PROV-O: The PROV Ontology*  
https://www.w3.org/TR/prov-o/

PROV-O provides a stable provenance vocabulary centered on:

- `prov:Entity`;
- `prov:Activity`;
- `prov:Agent`;
- derivation and generation relationships;
- usage relationships;
- delegation through `prov:actedOnBehalfOf`.

### Candidate mapping

| Activity Receipt concept | Candidate PROV mapping | Notes |
| --- | --- | --- |
| `system.agent_id` | `prov:Agent` | Good conceptual fit for an acting software/AI agent. |
| `authority.principal` | `prov:Agent` | Represents the responsible/delegating party. |
| `authority.delegate` | `prov:Agent` + `prov:actedOnBehalfOf` | PROV captures delegation/provenance, not the full authorization policy. |
| material action | `prov:Activity` | A tool call or other consequential operation can be represented as an activity. |
| material source | `prov:Entity` | Source documents/resources can be represented as entities. |
| source use | `prov:used` | Candidate fit for an action consuming a source. |
| derived result | `prov:wasDerivedFrom` / `prov:wasGeneratedBy` | Useful for result provenance and canonical-record derivation. |

### Boundary

PROV is a provenance model, not a complete authorization or audit-policy system. A mapping to PROV should not turn `prov:actedOnBehalfOf` into evidence that an action was actually authorized for a particular scope or time window.

---

## 2. OpenTelemetry and GenAI semantic conventions

**References:**

- OpenTelemetry Semantic Conventions 1.44.0  
  https://opentelemetry.io/docs/specs/semconv/
- OpenTelemetry GenAI Semantic Conventions repository  
  https://github.com/open-telemetry/semantic-conventions-genai
- GenAI agent span conventions  
  https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md

As of this snapshot, the GenAI conventions have moved to a dedicated repository and are still marked **Development**. The active work includes agent spans, tool execution, MCP, provider-specific conventions, and agent/orchestration topics.

### Candidate mapping

| Activity Receipt concept | OpenTelemetry candidate source |
| --- | --- |
| `trace_id` | OpenTelemetry trace identity |
| `system.agent_id` | `gen_ai.agent.id` where emitted |
| `system.version` | `gen_ai.agent.version` or application/resource version metadata |
| material action | agent/tool spans or named events |
| `operation` | `gen_ai.operation.name` or domain-specific operation attributes |
| `status` | span status plus error/outcome attributes |
| `occurred_at` | event timestamp or span timing |
| provider/model context | `gen_ai.provider.name`, request/response model attributes |
| source/retrieval evidence | GenAI retrieval/document attributes where captured |

### Design implication

OpenTelemetry is a strong **evidence substrate** for Activity Receipts. The Receipt should retain the originating trace/event identifiers whenever possible.

Sensitive prompt/message content is explicitly a telemetry concern in the GenAI conventions. The Receipt should therefore prefer stable identifiers, hashes, roles, and bounded summaries over copying raw prompt or message content.

Because the GenAI conventions are developing, adapters should be versioned and should not hard-code a single provider's telemetry as the canonical Activity Receipt model.

### Implemented prototype

The repository now includes a candidate `otel-genai-v0.1` adapter and synthetic OTLP/JSON fixture. It targets the **Canonical Activity Record**, not the human-facing Receipt directly.

The prototype uses standard OTLP trace nesting and selected current GenAI attributes such as `gen_ai.operation.name`, `gen_ai.agent.id`, `gen_ai.agent.version`, `gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.tool.name`, and `gen_ai.data_source.id`.

Authorization and materiality are supplied separately through sidecar evidence. This is intentional: an observed successful span does not establish that an action was authorized.

The adapter also deliberately does not copy opt-in tool arguments or results into the record. See [OTEL-ADAPTER.md](OTEL-ADAPTER.md) for the exact mapping and test boundary.

---

## 3. C2PA / Content Credentials

**Reference:** C2PA Technical Specification 2.4, April 2026  
https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html

C2PA focuses on tamper-evident provenance for digital content and media. Version 2.4 added, among other features:

- a JSON-LD-derived Content Credential representation (`crJSON`);
- a `c2pa.repository-receipt` assertion for proof that a manifest was ingested by a repository;
- a `c2pa.ai-disclosure` assertion for machine-readable AI transparency information.

### Candidate relationship

C2PA is most relevant when an Activity Receipt refers to, produces, or distributes a **content asset**. It can supply content-provenance evidence or an external attestation reference.

The C2PA repository receipt is conceptually interesting because it demonstrates a signed/tamper-evident **receipt-like proof of registration**, but it is not the same thing as an AI Activity Receipt.

### Boundary

AI Activity Receipt should not claim C2PA conformance merely because it stores hashes, provenance references, or an AI disclosure field. C2PA has its own manifest, assertion, signing, validation, and trust requirements.

---

## 4. Model Context Protocol (MCP)

**References:**

- MCP 2026-07-28 release  
  https://blog.modelcontextprotocol.io/posts/2026-07-28/
- TypeScript SDK migration notes for 2026-07-28  
  https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28

The 2026-07-28 MCP revision moved the core protocol to a stateless request/response model and strengthened authorization behavior. Requests carry method/tool information that can be observed at gateways, and authorization hardening includes issuer validation and tighter credential handling.

The TypeScript SDK documentation also makes an important distinction: MCP `clientInfo` / `serverInfo` are **self-reported descriptive identity**, suitable for display/logging/debugging, and should not be treated as security identity.

### Candidate mapping

| Activity Receipt concept | MCP evidence |
| --- | --- |
| material action | `tools/call`, resource reads, prompt operations, task operations |
| operation | MCP method/tool name |
| system metadata | client/server descriptive info, with provenance label |
| authorization evidence | OAuth / enterprise authorization records outside or alongside MCP payloads |
| event identity | request/task/tool-call identifiers where available |
| trace evidence | gateway, client, server, and OpenTelemetry correlation identifiers |

### Design implication

The Receipt should distinguish:

1. **self-reported identity metadata**;
2. **authenticated identity**;
3. **authorization decision evidence**.

A tool call must not be marked authorized solely because an MCP client declared a name/version.

### Implemented prototype

The repository now includes a revision-specific `mcp-2026-v0.1` adapter for captured `tools/call` request/response pairs.

The adapter validates basic capture consistency such as protocol version, `Mcp-Method`, `Mcp-Name`, and JSON-RPC request/response IDs. It maps the MCP tool name into the canonical Activity Record while taking principal identity, authenticated agent identity, delegated authority, materiality, and approval evidence from a separate sidecar.

The synthetic test deliberately changes self-reported `clientInfo` and requires the authenticated canonical identity to remain unchanged. It also verifies that a successful tool response without separate authorization evidence remains `unknown` and fails the existing consequential-action Receipt invariant.

See [MCP-ADAPTER.md](MCP-ADAPTER.md).

---

## 5. Agent2Agent (A2A)

**Reference:** Agent2Agent Protocol specification  
https://a2aproject.github.io/A2A/latest/specification/

The current A2A documentation describes a protocol for communication among independent agents, with discovery through an Agent Card, task/message lifecycles, HTTP-layer authentication, and server-side authorization.

The currently surfaced specification is marked **dev**, so mappings should be treated as provisional.

### Candidate mapping

| Activity Receipt concept | A2A candidate source |
| --- | --- |
| agent/system metadata | Agent Card identity/capability metadata |
| material action | task/message operations and agent-side tool actions |
| trace/run correlation | A2A task identifiers plus external trace identifiers |
| authorization evidence | authenticated transport identity + server policy decision |
| incident | failed/auth-required/rejected task transitions where material |

### Boundary

An Agent Card is useful discovery metadata, but it is not automatically proof of the authenticated actor or proof that a particular consequential action was authorized.

---

## 6. OAuth 2.0 Rich Authorization Requests

**Reference:** RFC 9396, *OAuth 2.0 Rich Authorization Requests*  
https://www.rfc-editor.org/rfc/rfc9396.html

RFC 9396 defines `authorization_details` for carrying fine-grained authorization data in OAuth flows.

### Candidate relationship

For deployments already using OAuth RAR, a Receipt could preserve references to the authorization decision or normalized action/resource details that materially establish delegated scope.

This is a better fit for `authority.scope` than treating a broad bearer-token scope string as the only evidence of fine-grained authority.

### Boundary

Activity Receipt should store only the minimum authorization evidence needed for auditability. Tokens, client secrets, refresh tokens, passwords, and other bearer credentials do not belong in the Receipt.

---

## 7. NIST AI-agent identity and authorization work

**References:**

- NIST AI Agent Standards Initiative, announced 2026-02-17  
  https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure
- NCCoE concept paper announcement on software/AI agent identity and authorization, 2026-02-05  
  https://www.nist.gov/news-events/news/2026/02/new-concept-paper-identity-and-authority-software-agents
- NIST AI RMF Generative AI Profile (NIST AI 600-1)  
  https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

NIST's 2026 work explicitly identifies agent identification, authorization, auditing, and non-repudiation as active areas of interest. This is strongly aligned with the problem space addressed by AI Activity Receipt, but it is **not an endorsement or adoption** of this project.

### Design implication

The project should continue to separate:

- identity evidence;
- delegation/authority evidence;
- observed action evidence;
- verification evidence;
- integrity/non-repudiation mechanisms.

That separation makes later mapping to emerging standards easier than embedding one provider-specific authorization model into the Receipt.

---

## 8. Candidate crosswalk summary

| Receipt field / concept | PROV | OpenTelemetry GenAI | C2PA | MCP / A2A / OAuth |
| --- | --- | --- | --- | --- |
| `trace_id` | activity/bundle identifier candidate | native trace correlation | external reference only | task/request correlation |
| `system.agent_id` | `prov:Agent` | `gen_ai.agent.id` | disclosure metadata only | Agent Card / descriptive client-server info |
| `authority.principal` | responsible `prov:Agent` | custom attribute/evidence | not primary purpose | authenticated principal |
| `authority.delegate` | `prov:actedOnBehalfOf` candidate | agent identity + custom delegation evidence | not primary purpose | authenticated client/agent |
| `authority.scope` | no complete native equivalent | custom policy/attribute evidence | not primary purpose | OAuth scopes / RAR authorization details |
| material source | `prov:Entity` | retrieval/document attributes | ingredient/content assertion where applicable | resource/tool evidence |
| material action | `prov:Activity` | span/event/tool execution | content action where applicable | tool/task/message operation |
| verification | qualified provenance/evidence links | evaluation or application events | validation status for C2PA assets | application-specific |
| incident | entity/activity record | error span/event | validation failures for content | protocol/task/auth failure evidence |
| integrity hash | entity identifier/attribute | telemetry attribute/reference | cryptographic manifest/content binding | external attestation/log evidence |

---

## 9. Research conclusions for candidate-v0.2

The interoperability review supports several concrete design rules:

1. **Keep the Receipt model-neutral.** Treat protocol/provider records as evidence inputs, not the canonical schema.
2. **Separate descriptive identity from authenticated identity.** Self-reported agent names are provenance metadata, not security proof.
3. **Preserve time.** Action time and authorization-decision time are necessary to test whether authorization preceded consequential execution.
4. **Use stable event IDs.** Verification and incident records need resolvable event references.
5. **Preserve uncertainty.** Missing evidence should remain missing/unknown rather than being promoted to confirmed.
6. **Do not copy secrets or private reasoning.** Auditability should rely on observable evidence and references.
7. **Treat content provenance and operational provenance as related but distinct.** C2PA can complement an Activity Receipt without replacing it.
8. **Version adapters and mappings.** OpenTelemetry GenAI, MCP, and A2A are evolving quickly enough that mappings must carry a version/date.

---

## 10. Machine-readable crosswalk

The repository now publishes `mappings/interoperability-v0.1.json` plus a JSON Schema and semantic validator.

The machine-readable artifact records whether an external field/concept is currently:

- mapped into a canonical-record field;
- supporting evidence only;
- deliberately excluded;
- or without a dedicated current equivalent.

CI verifies that mapped target paths still exist in `activity-record.schema.json`, that implemented-adapter references resolve, that self-reported identity metadata is not promoted into security-sensitive identity fields, and that selected sensitive payload/credential sources remain excluded.

See [MACHINE-READABLE-MAPPINGS.md](MACHINE-READABLE-MAPPINGS.md).

---

## Cross-adapter normalization parity

The repository now includes a synthetic cross-adapter parity test that passes aligned identity/authority context through both the OpenTelemetry GenAI and MCP adapters, derives Receipts, and compares the substrate-independent governance/action projection.

The test requires the two adapters to agree on:

- normalized agent identity/version after explicit authenticated-context alignment;
- principal/delegate authority scope and prohibited set;
- material consequential operation;
- execution status;
- authorization state;
- verification state.

The test deliberately does **not** require whole-record equality. Protocol/run identifiers, timestamps, and protocol-specific provenance remain distinct. In the current synthetic fixtures, OpenTelemetry carries a material retrieval source that MCP does not.

The negative parity case removes separate MCP authorization evidence and verifies that successful execution remains `unknown`, the derived Receipt fails the consequential-authorization invariant, and parity with the authorized OpenTelemetry projection is lost.

This is evidence of normalization consistency on one synthetic paired scenario, not proof of general interoperability or standards conformance.

---

## Next interoperability work

- extend the machine-readable crosswalk when external specifications or adapter semantics change;
- add richer evidence-substrate references beyond the current trace/event/source fields;
- evaluate whether C2PA attestation references should be optional evidence objects for produced content;
- prototype an A2A evidence adapter only after the task/identity mapping and authenticated-context boundary are sufficiently clear;
- monitor NIST AI-agent identity/authorization work and emerging industry standards;
- avoid any standards-conformance claim until an explicit conformance target and test method exist.
