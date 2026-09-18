# Multi-Agent and Multi-Hop Delegation — Candidate Design v0.1

> **Status:** Research/design definition only. Not implemented in the current candidate-record-v0.1 schema.  
> **Snapshot:** 2026-09-18  
> This document does not claim OAuth conformance, authenticated delegation, legal agency, or production authorization correctness.

The current Activity Record supports one direct delegation relationship:

```text
principal -> delegate
```

That is sufficient for the present single-agent candidate profile, but it is not sufficient for workflows such as:

```text
human principal
    -> orchestrator agent
        -> specialist agent
            -> tool/service
```

A future record version therefore needs an explicit delegation-chain model rather than silently treating every downstream actor as if the human principal directly authorized it.

---

## 1. Design goals

A multi-hop delegation model should make it possible to answer:

- Who is the root principal?
- Which actor is acting now?
- Through which intermediate delegates did authority flow?
- What scope was granted at each hop?
- What is the effective scope after all hop restrictions are applied?
- When was each delegation valid?
- Which evidence supports each delegation decision?
- Was any hop revoked, expired, or otherwise unusable at action time?
- Did a downstream delegate attempt to expand authority beyond what it received?
- Which actor actually performed the material event?

The model should preserve those answers without copying bearer credentials, private chain-of-thought, or implementation-specific tokens into the Receipt.

---

## 2. External concepts that inform the design

### OAuth 2.0 Token Exchange — RFC 8693

Reference:

https://www.rfc-editor.org/rfc/rfc8693.html

RFC 8693 explicitly distinguishes delegation from impersonation. In delegation, the acting party keeps its own identity while acting on behalf of another principal.

The RFC defines:

- `subject_token` — typically the party on whose behalf a token is requested;
- `actor_token` — the acting party;
- the JWT `act` claim — identifies the current actor;
- nested `act` claims — can represent prior actors in a delegation history;
- `may_act` — can identify a party eligible to become an actor.

A particularly important boundary for this project is that RFC 8693 treats prior nested `act` actors as historical information for access-control purposes. Consumers are directed to use the top-level claims and the current actor for access-control decisions rather than treating the entire historical chain as independently authoritative.

That supports a key Activity Receipt rule:

> A historical delegation path is provenance. Current effective authority still has to be established from current, valid authorization evidence.

### W3C PROV delegation

References:

- https://www.w3.org/TR/prov-sem/
- https://www.w3.org/ns/prov

PROV models delegation through `actedOnBehalfOf`: one agent acts for another with respect to an activity.

This is useful provenance semantics for describing responsibility/delegation relationships, but PROV does not by itself define the complete operational authorization model needed here, such as scope intersection, expiry, revocation, or per-action approval.

### NIST software/AI agent identity and authorization work

Reference:

https://csrc.nist.gov/pubs/other/2026/02/05/accelerating-the-adoption-of-software-and-ai-agent/ipd

NIST's 2026 concept work treats identification, authorization, auditing, and non-repudiation of software/AI agents as distinct control problems.

That reinforces the project's existing separation between:

- identity evidence;
- delegation/authority evidence;
- observed action evidence;
- verification evidence;
- integrity/attestation evidence.

---

## 3. Candidate delegation-chain structure

A future canonical record version could represent delegation as an ordered chain.

Illustrative shape only:

```json
{
  "authority_chain": {
    "root_principal": "user-2",
    "current_actor": "agent-specialist-7",
    "hops": [
      {
        "hop_id": "delegation-1",
        "delegator": "user-2",
        "delegate": "agent-orchestrator-4",
        "scope": ["read", "analyze", "delegate:analysis"],
        "valid_from": "2026-09-18T12:00:00Z",
        "valid_until": "2026-09-18T13:00:00Z",
        "decided_at": "2026-09-18T11:59:30Z",
        "evidence_ref": "authz-record-101"
      },
      {
        "hop_id": "delegation-2",
        "delegator": "agent-orchestrator-4",
        "delegate": "agent-specialist-7",
        "scope": ["read", "analyze"],
        "valid_from": "2026-09-18T12:02:00Z",
        "valid_until": "2026-09-18T12:30:00Z",
        "decided_at": "2026-09-18T12:01:55Z",
        "evidence_ref": "authz-record-102"
      }
    ]
  }
}
```

This is a design sketch, not a committed schema.

---

## 4. Required chain invariants

### DLG-01 — Ordered continuity

For every adjacent pair of hops:

```text
previous.delegate == next.delegator
```

A chain with a broken actor handoff is invalid.

### DLG-02 — Root continuity

The first hop's `delegator` must equal `root_principal`.

### DLG-03 — Current-actor continuity

The final hop's `delegate` must equal `current_actor`.

For a material action attributed to that chain, the event actor must equal the current actor unless a separate tool/service execution model explicitly states otherwise.

### DLG-04 — No cycles

An actor must not appear again later in the same active delegation path in a way that creates a cycle.

For example:

```text
A -> B -> C -> A
```

is invalid as an active authorization chain.

Historical provenance can record that such interactions happened, but the authorization path used to justify one action should be acyclic.

### DLG-05 — No authority amplification

A delegate must not grant a downstream actor authority that exceeds the effective authority the delegator currently holds.

Conceptually:

```text
downstream_scope ⊆ upstream_effective_scope
```

A downstream hop may narrow authority. It may not expand it without a separate valid authority source.

### DLG-06 — Effective scope is the intersection

The effective scope for the current actor is the intersection of all active hop scopes, subject to any additional policy restrictions.

Conceptually:

```text
effective_scope =
    hop_1.scope
    ∩ hop_2.scope
    ∩ ...
    ∩ hop_n.scope
    ∩ applicable_policy
```

If `send_email` disappears at any hop, the downstream actor does not regain it merely because an earlier hop had it.

### DLG-07 — Effective time window is the intersection

The effective delegation time window is:

```text
effective_valid_from = max(all hop valid_from)
effective_valid_until = min(all hop valid_until)
```

The chain is unusable when:

```text
effective_valid_from > effective_valid_until
```

A material action must occur inside the effective window.

### DLG-08 — Delegation decisions precede use

For each hop used to authorize an action:

```text
hop.decided_at <= action.occurred_at
```

A later authorization decision cannot retroactively authorize an already completed consequential action in the candidate profile.

### DLG-09 — Every hop must resolve to known actors

Each `delegator` and `delegate` must resolve to an actor in the canonical record.

### DLG-10 — Consequential action must be in effective scope

For a completed consequential action:

```text
action.operation ∈ effective_scope
```

and any separate per-action authorization decision required by the policy must still be present and prior.

A valid delegation chain does not automatically mean every downstream action is approved.

### DLG-11 — Historical actors are not automatically current authority

A prior actor in delegation provenance is not sufficient evidence that the current actor is authorized now.

This mirrors the useful distinction in RFC 8693 between current actor identity and nested delegation history.

### DLG-12 — Revoked/expired hops invalidate downstream use

If any required hop is revoked, expired, invalidated, or otherwise unusable at action time, the chain cannot justify the downstream action.

The future schema needs an explicit way to reference revocation/invalidity evidence rather than inferring validity merely from the existence of a historical delegation record.

---

## 5. Direct delegation as the one-hop special case

The current candidate-record-v0.1 profile:

```text
authority.principal = user
authority.delegate  = agent
```

can be treated conceptually as a one-hop chain:

```text
user -> agent
```

This means a future chain model does not need to invalidate the current conceptual model. It can generalize it.

However, implementing the chain in the schema would be a versioned change.

The current direct-delegation invariant:

```text
authority.delegate == system.agent_id
```

should remain the rule for candidate-record-v0.1.

---

## 6. Identity and delegation are different

A chain must not be built from descriptive names alone.

Examples of evidence that may describe an actor but do not automatically authenticate it include:

- MCP `clientInfo`;
- MCP `serverInfo`;
- A2A Agent Card metadata;
- arbitrary application labels;
- model display names.

The future chain should use authenticated/stable actor identifiers supplied by an identity/control plane or another explicit trust mechanism.

Protocol metadata can still be preserved as provenance.

---

## 7. Delegation provenance versus authorization evidence

The project should preserve two related but different concepts.

### Delegation provenance

Examples:

- PROV `actedOnBehalfOf`;
- nested RFC 8693 `act` history;
- workflow orchestration records;
- parent/child agent traces.

This answers:

> How did responsibility or execution flow through the system?

### Authorization evidence

Examples:

- validated token-exchange decision;
- OAuth authorization-server record;
- enterprise policy decision;
- human approval;
- explicit signed delegation record.

This answers:

> What evidence established that this hop was permitted?

The same artifact may contribute to both, but the record should not assume that provenance automatically proves authorization.

---

## 8. Candidate mapping to RFC 8693

A future adapter could treat RFC 8693 as follows.

| RFC 8693 concept | Candidate Activity Record role |
| --- | --- |
| validated subject identity | root/current represented subject/principal evidence |
| current outermost `act` actor | current authenticated actor/delegate evidence |
| nested `act` actors | delegation-history provenance |
| `scope` | candidate authority-scope evidence |
| `may_act` | evidence that a party may be eligible to become an actor, not proof that a later action occurred or was approved |
| token `exp` / `nbf` | candidate time-bound evidence |
| raw `subject_token` / `actor_token` / access token | **excluded** from Activity Record/Receipt |

The machine-readable interoperability crosswalk should record these distinctions.

---

## 9. Candidate Receipt projection

The human-facing Receipt should remain compact.

A future Receipt could show:

```text
Principal:      user-2
Current actor:  agent-specialist-7
Delegation:     user-2 -> orchestrator-4 -> specialist-7
Effective scope: read, analyze
Effective window: 12:02–12:30 UTC
Action:         analyze_document
Authorization:  approved
```

The detailed per-hop evidence should remain in the canonical record or linked evidence substrate.

A compact Receipt should not copy raw tokens or every historical claim.

---

## 10. Multi-agent event attribution

Multi-agent workflows create an additional distinction:

- the actor that **decided** to request an operation;
- the actor/tool/service that **executed** it.

Candidate-record-v0.1 currently has one `actor_id` per event.

A future version may need either:

1. separate decision/execution actor fields; or
2. distinct request and execution events linked by correlation.

The second approach may preserve provenance more cleanly because it avoids overloading one event with multiple meanings.

This remains an implementation decision.

---

## 11. Failure and incident cases

The future validator should include negative examples such as:

- downstream scope amplification;
- expired intermediate hop;
- revoked intermediate hop;
- cyclic chain;
- broken delegator/delegate handoff;
- unknown actor reference;
- action outside the intersected time window;
- action outside the effective scope;
- delegation decision recorded after action;
- current event actor not equal to the final delegate;
- historical `act` chain present but no current valid authorization evidence;
- valid chain but missing required per-action approval;
- valid chain with a blocked unauthorized downstream request.

A chain validator should report which hop broke the authorization path.

---

## 12. Adapter implications

### OpenTelemetry

A parent/child span relationship can help reconstruct execution flow, but it is not sufficient by itself to prove delegation authority.

A future OTEL adapter may preserve:

- parent/child span correlation;
- authenticated workload/agent identity;
- references to external authorization decisions.

It must not infer a valid delegation hop merely because one agent span called another.

### MCP

A tool request identifies protocol activity but does not establish the full principal-to-agent delegation chain.

Self-reported client/server metadata remains descriptive only.

A future MCP adapter should consume authenticated control-plane evidence for delegation rather than inventing chain hops from names.

### A2A

Agent/task relationships may help describe inter-agent workflow provenance.

Agent discovery metadata alone should not be treated as authenticated delegation authority.

---

## 13. Versioning decision

Implementing a chain changes the semantics of:

- authority;
- actor attribution;
- action authorization;
- Receipt projection;
- validator invariants.

Therefore it should not be silently added to `candidate-record-v0.1`.

Recommended sequence:

1. keep candidate-record-v0.1 as the direct-delegation profile;
2. publish chain semantics and negative cases first;
3. prototype a versioned `candidate-record-v0.2` or equivalent draft;
4. add migration examples from one-hop v0.1;
5. add deterministic chain validation;
6. only then add adapter support.

---

## 14. Current decision

For the present project stage:

- **define** multi-hop delegation as an ordered, evidence-backed chain;
- **treat** direct delegation as the one-hop special case;
- **intersect** scope and time constraints across hops;
- **forbid** authority amplification and active cycles;
- **separate** historical delegation provenance from current authorization evidence;
- **require** current action actor and authorization evidence to resolve through the active chain;
- **exclude** raw bearer/delegation tokens from the Activity Record/Receipt;
- **defer implementation** to a versioned future record schema rather than changing candidate-record-v0.1 in place.

This closes the design-definition gap without pretending that the current schema already implements multi-agent authorization.


---

## 15. Executable standalone prototype

The repository includes a non-integrated research prototype:

- `research/delegation-chain.schema.json`
- `research/delegation-chain-example.json`
- `research/delegation_chain.py`

Run:

```bash
python research/delegation_chain.py --self-test
```

The validator exercises the chain rules without changing `candidate-record-v0.1`. A valid example produces:

- the ordered actor path;
- the effective scope intersection;
- the effective `valid_from`;
- the effective `valid_until`.

Its adversarial self-test covers broken continuity, cycles, authority amplification, late delegation decisions, revoked hops, out-of-window actions, actor mismatch, out-of-scope action, late per-action approval, and unresolved actors.

This is deliberately a **standalone prototype**. Integrating these semantics into the canonical Activity Record still requires a versioned schema/Receipt design and migration tests.
