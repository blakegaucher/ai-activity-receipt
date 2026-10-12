# External Plugin Evidence Crosswalk — 2026-10-07

**Status:** research-only, non-normative; issue #108. Synthetic external service checks; not an AIAR adapter or standards-conformance claim.

## Live baseline consulted

- `README.md`, `docs/CANONICAL-RECORD.md`, `docs/INVARIANTS.md`, `docs/INTEROPERABILITY.md` on main, 2026-10-07.
- Existing record/receipt separation, authorization timing, source registration, verification references, deterministic derivation, and OTel sidecar policy are **already present**. Do not duplicate them.
- Issue #108 already owns the authorization-decision versus independently observed-effect research gate.

## Bounded external smoke-test observations

| System | Observed reference | Evidence class | Can establish | Cannot establish |
|---|---|---|---|---|
| ArmorCodex hosted | intent plan `8f196111-6888-43be-97fd-464db9917aa6` | declared intent | A three-step plan was registered | Permission, enforcement, execution, effect |
| MicroFn private | execution `161c070b-e3d7-462b-9270-d6115554cc94` | runtime execution | Synthetic function ran and returned an output | Independent external effect, authorization |
| 3Min API sandbox | record `01a11587-281f-79a1-a761-1a9a9132e77a` | stored report | Synthetic payload was accepted and later retrieved | Truth of payload, durability past retention |
| Sugra API | `boc_policy_rate` | attributed external data | Normalized observations and source/data timestamps | Independent verification of agent action |
| Not Just You | `openai-chatgpt-work` | status/advisory | Distinct provider/community/client signal channels | Absence of incident from zero reports |

The automatically generated 3Min sample with `side_effects:true` is **fixture data**, not a real observed effect. The other test payload used `side_effects:false`. No cryptographic cross-service correlation was tested.

## Minimal non-normative mapping proposal

For each external evidence reference, retain only:
- `evidence_class`: declared_intent | policy_decision | execution_report | stored_report | external_source | status_signal | independent_effect_observation
- `provider`, `external_reference`, `captured_at`, optional `source_observed_at`, optional `source_revision`
- `verification_state`: unknown | pending | corroborated | contradicted | not_observed
- `independence`: unknown | same_actor | external_actor | independently_verified
- `redaction_profile`: allowlisted_metadata_only

This is a **crosswalk vocabulary**, not a proposed addition to candidate-record-v0.1. Map to existing `sources`, `events`, `verification`, `incidents`, and sidecar evidence first. Source attribution is not equivalent to independent effect verification.

## Synthetic rejection/uncertainty vectors to implement only after coverage review

1. Intent registered, no execution -> execution not observed.
2. Execution observed, authorization missing -> do not infer approval.
3. Payload says `side_effects:true`, no independent observer -> effect indeterminate.
4. Permit with no observed effect -> distinguish no observation from proven no effect.
5. Deny plus independently observed effect -> disagreement/incident candidate.
6. Provider advisory versus surface status -> preserve both, do not collapse.
7. Source data stale or timestamp absent -> preserve freshness uncertainty.
8. Raw MicroFn execution log includes client/network metadata -> redact; reject leak in public projection.
9. 3Min record expires under free retention -> no durable-evidence claim.
10. Unbound cross-service identifiers -> no cryptographic or authenticated correlation claim.

## Gates before code/schema changes

- Review issue #108's decision/effect prototype and existing adapters; classify each concept equivalent / partial / absent / intentionally excluded.
- Pin primary provider specs and versions before conformance mapping.
- Implement a synthetic test adapter **outside core schema** only if mapping exposes a concrete uncovered behavior.
- Run existing `python derive_receipt.py --self-test`, `python validate_receipts.py`, and repository reproducibility suite in a suitable runner.
- Require clean validation, reviewer inspection, and explicit merge decision.
- Do not use private payloads, publish raw execution logs, modify AR-P003, change ArmorCodex policy, deploy 3Min production, or assert commercial validation.

**Current decision:** documentation-only research delta; no defensible core-schema change established.
