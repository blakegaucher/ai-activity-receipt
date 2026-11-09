# Standards comparison review — 2026-10-20

Scope: the source-only prototype in PR109 / issue108. This review closes the
comparison needed to incorporate that bounded research artifact. It does not
implement the external protocols, adopt them into the core schema, or close all
future implementation work described by issue108. The October 6 note is retained
as the original hypothesis; the decisions here supersede its tentative labels.

## Revision-pinned source and coverage decisions

The classifications below are judgments from reading the named source alongside
the linked local implementation; they are not conformance results.

| Primary source | Local coverage | Decision for this incorporation |
|---|---|---|
| [Agent audit record -02](https://www.ietf.org/archive/id/draft-gilda-wimse-agent-audit-record-02.html), sections 3, 4.1 and 5.3–5.7 | [decision/effect prototype](decision_effect_agreement.py), [DSSE prototype](dsse_prototype.py), [authority separation](../docs/INVARIANTS.md) | **Partial.** Synthetic decision/effect derivation is useful. The full signed observation, write-chain, coverage, commitment and canonicalization contract is absent. Keep the small prototype outside the core schema. |
| [Attenuated delegation -01](https://www.ietf.org/archive/id/draft-asor-wimse-agent-delegation-chain-01.html), sections 4–7 | [delegation validator](delegation_chain.py), [candidate multi-hop](multi_hop_v02.py) | **Partial semantic overlap, not cryptographic equivalence.** Local code checks scope intersection, actor continuity, cycles, time windows and declared state. It does not verify JOSE parent-token hashes, holder proof or a trusted token chain. Do not import token handling merely to rename existing checks. |
| [Authenticated provenance -01](https://www.ietf.org/archive/id/draft-reddy-wimse-aggregate-signatures-01.html), sections 5–6 | [multi-hop evidence](../docs/MULTI-HOP-V0.2.md), [external references](validate_external_evidence.py) | **Absent per-hop proof.** Actor/evidence references do not establish signed transformations or non-removability of unchanged hops. Record the gap; no aggregate-signature implementation in this PR. |
| [Verifier evaluation -03](https://www.ietf.org/archive/id/draft-jackson-wimse-evaluation-03.html), sections 3–5 | [delegation validator](delegation_chain.py), [attestation policy](validate_attestation_policy.py) | **Partial.** Local expiry/revocation-state checks are synthetic inputs. Frozen-call binding, fresh external status ordering and separate issuer/evaluator keys are not supplied by them. Future work needs its own trust and failure model. |
| [Scoped delegation -01](https://www.ietf.org/archive/id/draft-atakora-wimse-sadp-delegation-01.html), sections 4–6 | [delegation design](../docs/MULTI-AGENT-DELEGATION.md), [excluded sensitive payloads](../docs/OTEL-ADAPTER.md) | **Absent encrypted key-release mechanism.** Content minimization is useful but does not implement capability-bound decryption, caveat accumulation or nested signed grants. Keep keys/context release outside this research artifact. |
| [NovaFabric v1](https://arxiv.org/html/2609.12582v1), sections 3–5 | [DSSE prototype](dsse_prototype.py), [reproduction harness](reproduce.py) | **Comparator only.** Portable bundles, replay modes and capture-completeness labels suggest evaluation questions. A local deterministic reproduction is not equivalent to captured runtime replay; no imported architecture or claimed benefit. |
| [A2A-ForensicTrace v1](https://arxiv.org/html/2609.33924v1), sections III–V and VII | [external evidence](validate_external_evidence.py), [mapping](../mappings/interoperability-v0.1.json) | **Comparator only.** Integrity must precede bounded interpretation of committed relationships. AIAR has no equivalent complete A2A incident verifier, external signer binding or evaluated capture substrate. No numerical paper result is transferred to AIAR. |

All five IETF documents are work in progress, not adopted standards. Papers are
research sources. The original issue's October 5 date for the audit-record source
is not used as a revision identity; the retrieved -02 page lists October 4.

## Decision/effect compatibility boundary

The draft's table motivates the four familiar outcomes, but this prototype is
deliberately smaller. It models an `unknown` decision and excludes
`permit-with-conditions`; it does not accept or emit the draft's reserved
`one-sided` value. It takes boolean attribution/independence declarations rather
than deriving them from signed observations. A supplied True flag is a premise
for the synthetic example, not proof of a trustworthy observer.

The strict boolean patch preserves all 36 valid decision/effect/flag combinations
and rejects 468 malformed-input combinations before any outcome branch. Invalid
input is distinct from disagreement. No schema migration or production authority
decision is made here.

## OpenTelemetry reference and drift review

Checked `open-telemetry/semantic-conventions-genai` at commit
`547934afa90a34298441caf80c43b27255c3a292` (October 18, retrieved October 20):

- [Agent span definitions](https://github.com/open-telemetry/semantic-conventions-genai/blob/547934afa90a34298441caf80c43b27255c3a292/docs/gen-ai/gen-ai-agent-spans.md)
- [GenAI span definitions](https://github.com/open-telemetry/semantic-conventions-genai/blob/547934afa90a34298441caf80c43b27255c3a292/docs/gen-ai/gen-ai-spans.md)
- [Attribute registry](https://github.com/open-telemetry/semantic-conventions-genai/blob/547934afa90a34298441caf80c43b27255c3a292/docs/registry/attributes/gen-ai.md)

The seven GenAI attribute names consumed by the adapter are present:
`gen_ai.operation.name`, `gen_ai.agent.id`, `gen_ai.agent.version`,
`gen_ai.provider.name`, `gen_ai.request.model`, `gen_ai.tool.name`, and
`gen_ai.data_source.id`. The two deliberately excluded tool-content names also
remain present: `gen_ai.tool.call.arguments` and `gen_ai.tool.call.result`.
This is a bounded name/meaning review of the adapter's supported fields, not a
test of every newer upstream feature or a full semantic-convention validator.

The existing adapter documentation already references the dedicated repository;
no migration of adapter logic is warranted by this check. Reference URLs in the
machine-readable crosswalk are now pinned to this reviewed commit. Existing OTLP
identifier, sidecar, sensitive-content exclusion and cross-adapter parity tests
remain the behavioral evidence. Telemetry is still separate from authority.

The initially requested `model/gen-ai.yaml` path was unavailable at this commit;
the review used the linked generated span definitions and attribute registry.

## Incorporation decision

Incorporate the bounded source-only prototype, its regressions and this corrected
comparison after exact-head CI. Keep all external cryptographic mechanisms and
live integrations excluded. This documents surviving gaps without pretending
they have been implemented; follow-up implementation needs a separate scoped
change and validation. No conformance, trusted observer, human-benefit, deployment
or AR-P003 methodology claim follows.
