# Illustrative Human-Readable Activity Receipt

> **Illustrative example only.** This page presents the existing synthetic `examples/sample-receipt.json` in a human-facing format. It is not a frozen normative schema and does not establish real-world effectiveness.

## Activity summary

| Field | Receipt view |
| --- | --- |
| Receipt | `AR-example-001` |
| Trace | `trace-example-001` |
| Agent | `agent-4` |
| Agent version | `example-version` |
| Authority window | 2026-09-13 15:00–16:00 UTC |
| Allowed scope | read, analyze |
| Explicitly prohibited | send_email |
| Verification | pending |
| Integrity link | `sha256:example-record-hash` |

## Material evidence

**Source:** `src-A`  
**Role:** supports result

The receipt points back to the material evidence rather than replacing it.

## Material action

**Attempted operation:** send_email  
**Outcome:** blocked  
**Authorization:** denied  
**Consequential action:** yes  
**Event:** `event-blocked-1`  
**Time:** 2026-09-13 15:15 UTC  
**Linked source:** `src-A`

### What a reviewer can reconstruct from this receipt

- The agent was authorized to **read** and **analyze**.
- The agent was explicitly **not authorized to send email**.
- A send-email operation was attempted.
- The operation was **blocked**, not completed.
- The authorization decision was recorded as **denied**.
- The blocked action was preserved as an incident rather than silently discarded.
- Verification of the broader result is still **pending**.

## Incident

**Type:** blocked unauthorized action  
**Linked event:** `event-blocked-1`

## What a reviewer should check next

The receipt is an index into evidence, not a substitute for evidence. A reviewer could follow the linked records to confirm:

1. the authority record and its validity window;
2. the evidence behind `src-A`;
3. the exact blocked action event;
4. the policy/authorization decision that denied the action;
5. whether any separate execution path later completed the action;
6. what remains outstanding before verification can move beyond `pending`.

## What this example demonstrates

This synthetic example demonstrates the **presentation concept**:

- identity and version;
- bounded delegated authority;
- material source references;
- material actions and outcomes;
- authorization decisions;
- verification state;
- incidents;
- integrity/lineage references.

It does **not** demonstrate that the Receipt improves reviewer accuracy, reduces review time, prevents incidents, provides legal compliance, or is production-secure.

## Machine-readable source

See the underlying synthetic JSON:

[examples/sample-receipt.json](sample-receipt.json)
