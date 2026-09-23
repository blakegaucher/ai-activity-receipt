# AI Activity Receipt — Prior-Art Landscape Snapshot

> **Research snapshot:** 2026-09-23  
> **Status:** Non-exhaustive research review; not a legal novelty, patentability, freedom-to-operate, standards-conformance, certification, or endorsement opinion.  
> **Purpose:** Record recent public technical work that materially overlaps the AI Activity Receipt problem space so project claims remain appropriately scoped and the human-centered research contribution can be tested without overstating novelty.

## 1. Search scope

A focused Exa research pass reviewed 80 result slots across nine searches covering active standards/specifications and Internet-Drafts, recent 2025–2026 academic systems, human-review / audit-evidence research, current agent tracing and approval infrastructure, and open 2026 research/competition opportunities.

Six high-signal primary sources were then fetched for deeper review. The search was designed to identify overlap, not to prove absence of prior art. A later legal/patent search would be a separate task.

## 2. Main conclusion

The core **machine-record primitives** represented by AI Activity Receipt are now a crowded and fast-moving area. Public 2026 work already covers many of the following individually and, in some cases, together: agent identity; delegated authority; tool/action records; policy / authorization decisions; human approvals; provenance; timestamps and ordered sessions; errors / incidents; tamper evidence; cryptographic attestations; and external verification.

Accordingly, this project should **not** claim that it invented agent audit trails, delegated-authority records, tamper-evident agent logs, provenance-aware traces, or human-facing agent review in general.

The strongest defensible project direction remains narrower:

1. normalize heterogeneous evidence into a model-neutral canonical activity record;
2. derive a compact human-facing Receipt without inventing facts;
3. preserve uncertainty, incidents, authorization state, verification state, and evidence links;
4. measure whether relevant professional reviewers can make **evidence-supported correct audit judgments within a prespecified deadline**, while separately testing whether a neutral structured control produces the same benefit.

That combination should be treated as a **research hypothesis and evaluation target**, not assumed novelty or effectiveness.

## 3. Claim-by-claim overlap matrix

| AI Activity Receipt concept | Public overlap found | Current claim posture |
| --- | --- | --- |
| Agent / system identity | OCSF 1.9 AI-agent objects; OpenTelemetry GenAI agent fields; AAT; AITLP | **Established area.** Do not claim novelty. |
| Human principal / delegated authority | OCSF 1.9 delegation object; HDP; Mandato; IETF audit architecture; AITLP | **Established and rapidly standardizing.** Treat as mapped evidence substrate. |
| Bounded authorization scope / time | HDP scope; Mandato mandates; OAuth-family delegation patterns; AITLP mandates | **Established concept.** Project value is normalization/presentation, not invention. |
| Tool calls / material actions | OpenTelemetry GenAI execute-tool spans; AAT action taxonomy; Agent Flight Recorder; NovaFabric | **Established area.** Materiality selection remains a project-local semantic decision. |
| Pre-execution approval / denial | AAT record phase; OpenAI Agents SDK approval flows; Mandato; AITLP | **Established area.** Preserve evidence of decision timing. |
| Human approval evidence | Agent Flight Recorder; OpenAI Agents SDK; IETF audit architecture | **Established concept.** Receipt can index/normalize it. |
| Source / context provenance | W3C PROV; Agent Flight Recorder; LEDGER; NovaFabric; provenance survey work | **Established area.** Receipt should preserve source roles and links without overstating provenance guarantees. |
| Delegation chain provenance | HDP; Agent Flight Recorder; IETF audit architecture; OCSF 1.9 | **Established / active standards area.** Multi-hop work should emphasize interoperability and loss-aware normalization. |
| Verification / attestation state | OCSF 1.9 record integrity; GAR; NovaFabric; AAT; Agent Flight Recorder | **Established area.** Distinguish verification state from evidence actually proving a claim. |
| Incidents / blocked actions / errors | OpenTelemetry error spans; AAT outcomes; GAR alerts/lifecycle events; AITLP suspension events | **Established primitives.** Project-specific incident semantics may still be useful. |
| Timestamps / session ordering | AAT; GAR; OpenTelemetry traces; Agent Flight Recorder | **Established area.** |
| Tamper-evident chaining / cryptographic integrity | AAT; GAR; OCSF 1.9; Agent Flight Recorder; NovaFabric; Mandato | **Heavily covered.** Do not imply the project originated these mechanisms. |
| Human-readable audit summary | Auditability Card; LEDGER review interface; IntelliAudit auditor-facing recommendations | **Partial-to-strong overlap.** Avoid broad claims to being the first human-facing audit artifact. |
| Claim-to-evidence review path | LEDGER; IntelliAudit; provenance/evidence tracing literature | **Strong adjacent overlap.** AIAR should distinguish its receipt format, evidence symmetry, and governance-state focus. |
| Model-neutral normalization above telemetry/providers | OCSF profiles; OpenTelemetry; NovaFabric provider-neutral evidence; IETF architecture | **Partial overlap.** Still a useful engineering goal, but not inherently novel. |
| Receipt derived deterministically from canonical evidence | Related evidence packaging exists, but the exact project pipeline remains project-specific | **Potentially differentiating implementation detail.** Phrase as project architecture, not a field-wide novelty claim. |
| Explicit “receipt must not invent facts” invariant | Adjacent grounding/evidence-integrity ideas exist | **Potentially differentiating evaluation/governance rule.** Do not claim uniqueness without a deeper search. |
| Relevant-professional reviewer study | IntelliAudit uses practicing auditors for evaluation; adjacent human-review work exists | **Not unique in using professionals.** |
| Three-condition raw vs structured vs Receipt comparison | No exact match identified in this search | **Candidate differentiator.** Treat as a study-design contribution pending exhaustive literature review. |
| Primary endpoint: evidence-supported correct completion by 180s | No exact match identified in this search | **Candidate differentiator.** This is currently a stronger research distinction than the underlying logging fields. |
| Failure on fabricated material facts / mismatched authorization | Adjacent audit correctness and evidence-grounding work exists | **Candidate differentiator as part of the frozen endpoint contract**, not as a general novelty claim. |
| Integrated stale / incomplete / conflicting Receipt challenge strata | Adjacent robustness and misleading-evidence research exists | **Candidate differentiator in evaluation design.** Must be validated empirically. |

## 4. Closest technical overlaps

### 4.1 OCSF 1.9

OCSF 1.9 (August 3, 2026) added an AI-agent object, an AI-operation profile, a delegation object linking actions to delegated authority, a record-integrity profile, cryptographic attestations, and tamper-evident chain references.

Reference: https://github.com/ocsf/ocsf-schema/releases/tag/1.9.0

**Implication:** AI Activity Receipt should treat OCSF as a high-priority candidate evidence source / mapping target rather than presenting identity, delegation, or record-integrity primitives as original.

### 4.2 OpenTelemetry GenAI semantic conventions

OpenTelemetry's developing GenAI conventions include agent operations, workflow invocation, planning, retrieval, memory, tool execution, inputs/outputs, errors, and agent/provider metadata.

Reference: https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md

**Implication:** The existing project direction—OpenTelemetry as evidence substrate feeding the canonical record—is strengthened. The Receipt should remain above telemetry rather than duplicate it.

### 4.3 Agent Audit Trail (AAT)

AAT defines a JSON audit record with agent identity, action type, outcome, trust level, ordered sessions, pre-/post-execution record phase, tamper-evident chaining, optional signatures, and regulatory mappings.

Reference: https://datatracker.ietf.org/doc/html/draft-sharif-agent-audit-trail-04

**Implication:** Do not claim a new standard agent log format. AIAR's research distinction should focus on evidence normalization, human presentation, and reviewer outcomes.

### 4.4 Human Delegation Provenance Protocol (HDP)

HDP records the human principal, authorization scope, session binding, and signed delegation hops, enabling offline verification of the delegation chain.

Reference: https://datatracker.ietf.org/doc/html/draft-helixar-hdp-agentic-delegation-00

**Implication:** Direct and multi-hop delegation provenance is an active protocol area. AIAR should preserve compatibility and avoid re-inventing a competing delegation protocol unless a specific gap is demonstrated.

### 4.5 Governance Audit Record (GAR)

GAR proposes an evidentiary architecture for agent governance with session audit records, governance events, authority lifecycle events, alerts, audit packages, signatures, causal ordering, and transparency-log integration.

Reference: https://datatracker.ietf.org/doc/draft-sato-soos-gar/06/

**Implication:** AIAR should not position itself as the first agent-governance audit package. Its compact receipt and controlled human-review evaluation remain a more defensible focus.

### 4.6 IETF audit architecture for AI agent delegation

This architecture explicitly links user intent, delegation, authorization, execution, distributed audit records, attestation, and transparency logging.

Reference: https://www.ietf.org/archive/id/draft-kuehlewind-audit-architecture-00.html

**Implication:** “Intent → delegation → authorization → execution” is now clearly shared territory. AIAR should emphasize its normalization and review layer.

### 4.7 Agent Flight Recorder

The September 2026 paper records intent, policy evaluation, human approval, execution, effects, context provenance, code provenance, and delegation provenance in a tamper-evident architecture and evaluates forensic query performance.

Reference: https://arxiv.org/html/2609.01931

**Implication:** This is close prior art for much of the machine/evidence layer. It strengthens the case for separating **evidence creation/integrity** from **human reviewer performance**.

### 4.8 Auditable Agents

This work defines five dimensions of agent auditability—action recoverability, lifecycle coverage, policy checkability, responsibility attribution, and evidence integrity—and proposes an Auditability Card.

Reference: https://arxiv.org/html/2604.05485v2

**Implication:** Broad “human-readable audit artifact” novelty claims are unsafe. AIAR should distinguish the specific Receipt schema, evidence-symmetry rules, and controlled reviewer benchmark.

### 4.9 LEDGER

LEDGER builds layered claim-to-evidence trace graphs for human review of agent sessions, connecting conclusions to actions, artifacts, checks, and source records.

Reference: https://arxiv.org/html/2608.18398v1

**Implication:** This is the strongest overlap found for evidence-centered human review. AIAR's defensible distinction is not “human review of agent traces” generally; it is the compact governance-oriented receipt plus a prespecified comparative human evaluation.

### 4.10 IntelliAudit

IntelliAudit produces auditor-facing recommendations with cited evidence, rationale, missing-evidence analysis, and remediation guidance, and evaluates them with practicing auditors and audit-readiness users.

Reference: https://arxiv.org/html/2608.07688

**Implication:** Use of professional auditors and evidence-grounded review is not unique. AR-P003 should emphasize its different task: reconstructing agent activity and authority from the same underlying evidence under controlled presentation conditions.

## 5. Safe project positioning

A claim-safe description is:

> **AI Activity Receipt is a human-centered, model-neutral research architecture that normalizes heterogeneous agent evidence into a canonical activity record and derives a compact Receipt for human review. The project studies whether that Receipt helps relevant professional reviewers reach evidence-supported audit judgments accurately and within a prespecified time limit, while preserving uncertainty and testing misleading or incomplete Receipt conditions.**

This wording intentionally does **not** claim first agent audit trail, first agent provenance record, first delegated-authority log, first tamper-evident agent record, first human-facing agent audit interface, standards conformance, proven human benefit, or proven safety/compliance.

## 6. AR-P003 implications

1. **Keep the neutral structured control.** Because structured logs/graphs already provide known benefits, the study should distinguish generic evidence organization from any additional Receipt benefit.
2. **Keep the primary endpoint decision-focused.** The strongest research question is not whether the Receipt contains fields, but whether reviewers reach a defensible judgment under time pressure.
3. **Preserve challenge strata.** A compact summary can become dangerous if stale, incomplete, or conflicting; robustness is part of the contribution.
4. **Keep evidence symmetry.** The Receipt must not gain hidden informational advantage over the raw/structured conditions.
5. **Do not promote cryptographic integrity into a human-benefit claim.** Integrity and usability are separate hypotheses.

## 7. Recommended interoperability additions

The next interoperability refresh should prioritize explicit mappings to OCSF 1.9 AI-agent / AI-operation / delegation / record-integrity concepts; AAT record phase / action taxonomy / outcome fields; HDP principal, scope, and delegation-chain concepts; GAR session / audit-package concepts; and the IETF distributed audit-context architecture.

These should remain **candidate mappings**, not conformance claims.

## 8. Claim-control rule

Before adding a public novelty statement to the README, paper, competition submission, or business material:

1. identify the exact claimed contribution;
2. search recent standards, papers, and production systems for that exact contribution;
3. distinguish “not found in this search” from “does not exist”;
4. prefer **“this project studies / implements / evaluates”** over **“first / unique / novel”** unless a dedicated novelty review supports the stronger wording;
5. keep the latest dated landscape snapshot in the repository.

## 9. Opportunities note — 2026-09-23

The research pass also checked opportunities with deadlines after September 23, 2026. The Steerability Challenge remains open through **November 21, 2026**, but it is primarily a model-steering competition rather than a direct AI Activity Receipt fit.

Reference: https://steerability.github.io/competition/steerability-challenge-guide.pdf

A separate competition-decision process should therefore keep model-steering work in its own lane rather than changing AR-P003 or the Receipt architecture simply to fit that challenge.

## 10. Next research gate

The next useful prior-art step, if needed for a formal paper or IP decision, is a **dedicated novelty search** that expands beyond the current technical web review into patent databases, conference proceedings not well indexed by general web search, standards working-group issues / pull requests, commercial product documentation, pre-2025 security/audit literature, and explicit claim charts against the final paper contribution.

That step should occur before making any legal or “first-of-kind” novelty assertion.
