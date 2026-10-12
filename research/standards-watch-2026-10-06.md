# Standards Watch — 2026-10-06

Status: research-only comparison for issue #108. No standards-conformance or production-readiness claim.

## Decision matrix

| Source | AIAR baseline | Gap decision | Bounded action |
|---|---|---|---|
| WIMSE agent audit record -02 | authorization + execution status + verification are separate | **Partial / real gap:** no explicit independently observed effect or derived decision-effect agreement | prototype outside core schema; synthetic vectors first |
| WIMSE attenuated delegation -01 | no-amplification, scope intersection, chain continuity, validity/revocation prototype | **Mostly equivalent** | map parent linkage, holder binding and canonicalization; no schema expansion until a surviving delta is proven |
| WIMSE authenticated provenance -01 | actor/event provenance + integrity + delegation evidence refs | **Partial** | compare per-hop transformation attribution; research mapping only |
| WIMSE verifier-side evaluation / scoped delegation | local verification and chain invariants | **Partial/overlap** | harvest reject vectors and verifier semantics where not already tested |
| NovaFabric | DSSE research, OTel adapter, external evidence refs | **Comparator** | assess replay/evidence-bundle/observer-independence ideas; no architectural import by default |
| A2A-ForensicTrace | multi-agent/delegation research and tamper-evident evidence | **Comparator** | use evaluation dimensions/test ideas; do not treat paper results as AIAR validation |
| OpenTelemetry GenAI | implemented candidate adapter | **Maintenance gap** | update references to dedicated GenAI semconv repository and test drift |

## First surviving gap: decision versus independently observed effect

The October WIMSE audit-record draft distinguishes:
1. what an authorization decision point reported; and
2. what an observer outside the agent's addressable layer observed actually happened.

AIAR currently has authorization state, execution status, verification evidence and incidents, but those fields do not encode observer independence or a deterministic decision/effect agreement result.

### Prototype rules

Keep this out of `activity-record.schema.json` until reviewed. A research prototype should model:
- reported decision: permit / deny / unknown;
- observed effect: occurred / none / unknown;
- observer class and independence evidence;
- correlation/request digest rather than raw sensitive arguments;
- derived agreement: agree / disagree / indeterminate / not-exercised.

Minimum synthetic cases:
- permit + attributable effect -> agree;
- deny + attributable effect -> disagree;
- permit + no effect -> not-exercised;
- effect present but attribution unresolved -> indeterminate;
- in-process/self-reported observer -> never upgraded to independent observation;
- malformed/duplicate/canonicalization failures remain integrity failures, not policy disagreement.

This prototype must not infer authority from telemetry and must not copy tool payloads.

## OTel maintenance note

The legacy OpenTelemetry GenAI pages now state that GenAI semantic conventions moved to the dedicated `open-telemetry/semantic-conventions-genai` repository. AIAR already references that repository in its machine-readable crosswalk; documentation and regression fixtures should be checked for drift before changing mappings.

## Maturity boundary

All cited WIMSE Internet-Drafts are work in progress. Mapping to them is interoperability research, not IETF/WIMSE conformance. NovaFabric and A2A-ForensicTrace are comparators, not validation of AIAR's claimed benefit.
