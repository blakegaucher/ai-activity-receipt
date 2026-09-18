# MCP 2026-07-28 Adapter — Candidate v0.1

> **Status:** Synthetic interoperability prototype. This adapter is not an MCP conformance implementation and does not establish production authorization correctness, real-world security, or audit benefit.

The candidate adapter converts a captured MCP `tools/call` request/response interaction plus separate authenticated authority context into the project's Canonical Activity Record. The existing derivation utility can then produce a compact AI Activity Receipt.

Files:

- `adapters/mcp_2026.py`
- `examples/mcp-2026-capture.json`
- `examples/mcp-adapter-context.json`
- `examples/mcp-derived-record.json`
- `examples/mcp-derived-receipt.json`

## Current protocol basis

The prototype targets the **2026-07-28** MCP protocol revision.

References:

- 2026-07-28 release: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- TypeScript SDK migration notes: https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28
- Current MCP roadmap: https://blog.modelcontextprotocol.io/posts/mcp-roadmap/

The 2026-07-28 revision is stateless at the protocol layer. Requests carry protocol/client metadata per request, and HTTP routing can expose the method/tool name through MCP headers.

The adapter is deliberately revision-specific so later MCP changes can be handled explicitly rather than silently changing semantics.

## Identity separation

The strongest design rule from the current MCP documentation is that `clientInfo` and `serverInfo` are **self-reported descriptive metadata** intended for display, logging, and debugging.

They are not security identity.

The adapter therefore ignores those values when deciding:

- who the authenticated agent is;
- who the principal is;
- what authority was delegated;
- whether an action was authorized.

The authenticated agent identity comes from the sidecar context.

The synthetic fixture intentionally claims a different client name/version. The self-test changes that claimed identity again and requires the canonical record to remain byte-for-byte equivalent as a parsed JSON object.

## Supported interaction

Candidate v0.1 adapts:

```text
tools/call
```

The canonical operation is the MCP tool name:

```text
request.method      = tools/call
request.params.name = send_email

canonical operation = send_email
```

Other MCP methods are currently ignored by this adapter.

## Request consistency checks

For each adapted `tools/call`, the adapter verifies:

- `MCP-Protocol-Version` is `2026-07-28`;
- `Mcp-Method`, when present, matches the JSON-RPC method;
- `Mcp-Name`, when present, matches `params.name`;
- the JSON-RPC response ID matches the request ID;
- request IDs are not duplicated within the capture.

These are capture-consistency checks. They do not substitute for an MCP implementation's own conformance validation.

## Event identity

The canonical event ID is derived from the JSON-RPC request ID:

```text
mcp-request:<request-id>
```

The sidecar may supply a separate trace/correlation ID for the larger workflow.

## Status mapping

Candidate mapping:

- JSON-RPC error -> `failed`;
- result with `isError: true` -> `failed`;
- `resultType: input_required` -> `pending`;
- otherwise -> `completed`.

The sidecar can override status when a separate control-plane record has stronger evidence, such as an action explicitly blocked before tool execution.

## Authorization is not inferred from execution

A successful MCP response proves that the captured protocol interaction returned successfully. It does **not** prove that the caller had valid delegated authority for the consequential action.

For consequential tools:

- sidecar authorization evidence is used when supplied;
- otherwise the canonical event records `authorization = "unknown"`.

The self-test removes the sidecar approval and verifies that deterministic Receipt derivation then fails the existing consequential-action authorization invariant.

## Sidecar context

Current sidecar fields include:

- `record_id`;
- `trace_id`;
- `principal`;
- `authenticated_agent_id`;
- `agent_version`;
- `authority.scope`;
- `authority.prohibited`;
- `authority.valid_from`;
- `authority.valid_until`;
- `material_tools`;
- `consequential_tools`;
- `authorization_by_request_id`;
- optional `status_by_request_id`;
- `verification`;
- `generated_at`.

The sidecar is a placeholder for evidence that would eventually come from an authenticated application/session layer, authorization server, enterprise policy system, gateway, or similar control plane.

The adapter does not claim that a plain JSON sidecar is cryptographically trustworthy.

## Content minimization

The synthetic capture includes:

- fake tool arguments;
- fake message content;
- self-reported client metadata;
- self-reported server metadata.

None of those values are copied into the canonical record.

The self-test checks that the fake recipient, fake message body, client name, and server name do not appear in the canonical output.

This keeps the Activity Record focused on:

- observable operation identity;
- execution status;
- separately evidenced authority;
- timestamps;
- materiality;
- incidents.

## Incidents

When a material tool action is blocked or failed and is consequential or denied authorization, the adapter creates a linked incident record.

Candidate classifications:

- blocked + denied -> `blocked_unauthorized_action`;
- otherwise -> `tool_failure`.

This is a deterministic classification from the captured status plus sidecar authorization state, not a claim of real-world harm.

## Deterministic synthetic test

Run:

```bash
python adapters/mcp_2026.py --self-test
```

The self-test confirms:

1. the synthetic MCP capture maps exactly to the published canonical-record fixture;
2. the record passes the canonical schema and semantic checks;
3. deterministic Receipt derivation exactly matches the expected Receipt;
4. the Receipt passes the current schema and executable invariants;
5. changing self-reported `clientInfo` does not change authenticated system identity;
6. removing separate authorization evidence leaves the consequential action `unknown` and causes the Receipt authorization check to fail;
7. a mismatched `Mcp-Name` routing header is rejected;
8. tool arguments/results and self-reported client/server names are not copied into the record.

## Manual use

```bash
python adapters/mcp_2026.py \
  mcp-capture.json \
  --context authenticated-context.json \
  --output activity-record.json \
  --receipt-output activity-receipt.json
```

If the canonical record is internally valid but the derived Receipt violates a Receipt invariant, the command fails rather than silently presenting the result as valid.

## Known limitations

Candidate v0.1 intentionally does not yet:

- implement a live MCP client/server;
- validate OAuth tokens or issuer-bound credentials;
- consume enterprise authorization extensions;
- capture resource/prompt methods;
- implement Multi Round-Trip Request state reconstruction;
- model the Tasks extension;
- preserve every MCP response/result field;
- prove that the capture itself is complete or authentic;
- sign or attest the canonical record;
- run the official MCP conformance suite.

## Design findings

The prototype reinforces several project decisions:

1. **Self-reported implementation metadata must remain separate from security identity.**
2. **Protocol success must remain separate from authorization.**
3. **A canonical record is a useful normalization boundary between protocol-specific evidence and the human Receipt.**
4. **Header/body consistency checks are useful evidence-quality checks but are not authorization checks.**
5. **The Receipt generally does not need tool arguments or response bodies to answer who acted, what action occurred, under what authority, and with what result.**
6. **Future authenticated evidence references are likely more important than copying more protocol payload into the Receipt.**

## Evidence boundary

Passing this self-test establishes deterministic behavior only for the published synthetic capture.

It does not establish:

- MCP conformance;
- OAuth/OIDC correctness;
- authenticated identity verification;
- completeness of capture;
- production security;
- real-world interoperability;
- improved human auditing;
- safety or regulatory compliance.
