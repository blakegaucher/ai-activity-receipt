# Multi-Hop Record / Receipt Prototype — candidate-record-v0.2

> **Status:** Research-only future profile.  
> **Snapshot:** 2026-09-18  
> This does not replace the current public `candidate-record-v0.1` direct-delegation profile.

The repository now contains a versioned future record/Receipt prototype that implements the multi-hop delegation semantics previously defined only as a standalone chain model.

Files:

- `research/candidate-record-v0.2.schema.json`
- `research/candidate-record-v0.2.example.json`
- `research/candidate-receipt-v0.3.schema.json`
- `research/multi_hop_v02.py`

## Record model

The future record replaces the direct `authority` object with `authority_chain`:

- `root_principal`;
- `current_actor`;
- `evidence_state`;
- ordered delegation `hops`.

Each hop records:

- delegator and delegate;
- scope;
- prohibited operations;
- validity window;
- decision-time state and optional decision timestamp;
- evidence reference;
- active/revoked/invalid state.

The prototype is intentionally limited to **one active delegation chain per record**.

## Effective authority

The validator computes:

- delegation path;
- effective scope = intersection of hop scopes;
- effective prohibited set = union of hop prohibitions;
- effective valid-from = latest hop start;
- effective valid-until = earliest hop end.

A downstream hop may narrow authority but may not add scope that the upstream chain no longer holds.

The current actor must match the final delegate and the record's `system.agent_id`.

Material events in this profile must be attributed to that current actor.

## Complete versus migrated chain evidence

Native v0.2 chains use:

```text
evidence_state = complete
```

For a complete chain, every hop must have:

- recorded `decided_at`;
- resolvable `evidence_ref`;
- active state.

The migration path from v0.1 deliberately uses:

```text
evidence_state = legacy_partial
decision_time_state = legacy_not_recorded
```

The migration **does not invent a delegation decision timestamp** that v0.1 never recorded.

To avoid normalizing incomplete multi-hop evidence, `legacy_partial` is permitted only for a one-hop migrated chain.

## Receipt projection

The future Receipt retains the familiar compact authority summary:

- principal;
- delegate;
- effective scope;
- effective prohibited operations;
- effective validity window.

It adds:

- `delegation_path`;
- `delegation_evidence_state`.

The detailed hop evidence remains in the canonical record rather than being copied into the compact Receipt.

## Migration behavior

`migrate_v01_to_v02()` converts a valid direct-delegation record into the one-hop special case.

The self-test requires the migrated v0.3 Receipt to preserve the v0.1 human-visible core:

- trace;
- system;
- principal/delegate;
- scope/prohibited set;
- authority window;
- material sources/actions;
- verification;
- incidents.

The new record hash changes because the canonical representation changes, and the new Receipt exposes the migration/evidence state.

## Adversarial coverage

The self-test rejects:

- broken adjacent-hop continuity;
- cycles;
- downstream authority amplification;
- revoked hop;
- missing evidence in a complete chain;
- delegation decision after material action;
- material event attributed to the wrong actor;
- action outside the effective chain window;
- multi-hop use of `legacy_partial`;
- upstream prohibition that a downstream hop attempts to ignore.

Run:

```bash
python research/multi_hop_v02.py
```

## Evidence boundary

This is a versioned research profile and migration experiment.

It does not yet establish:

- multiple concurrent delegation chains in one record;
- actor switching across different material actions in one record;
- authenticated hop evidence;
- production OAuth token-exchange validation;
- production revocation infrastructure;
- backward-compatible replacement of candidate-record-v0.1.

The current public v0.1 schema and derivation path remain unchanged.
