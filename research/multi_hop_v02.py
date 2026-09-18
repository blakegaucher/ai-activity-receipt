#!/usr/bin/env python3
"""Research-only candidate-record-v0.2 multi-hop delegation prototype.

This module does not replace candidate-record-v0.1. It validates one active
delegation chain per record, derives candidate-receipt-v0.3, and provides a
loss-aware migration from the direct-delegation v0.1 profile.
"""

from __future__ import annotations

import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from derive_receipt import (  # noqa: E402
    derive_receipt as derive_v01_receipt,
    record_hash,
    record_semantic_errors as v01_semantic_errors,
    validate_derived_receipt,
    validate_record_structure,
)
from validate_receipts import parse_datetime  # noqa: E402

V02_SCHEMA = ROOT / "research" / "candidate-record-v0.2.schema.json"
V03_RECEIPT_SCHEMA = ROOT / "research" / "candidate-receipt-v0.3.schema.json"
V02_EXAMPLE = ROOT / "research" / "candidate-record-v0.2.example.json"
V01_EXAMPLE = ROOT / "research" / "workflow-pilot" / "research-email.json"

RECORD_VERSION = "candidate-record-v0.2"
RECEIPT_VERSION = "candidate-receipt-v0.3"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def chain_semantic_errors(
    record: dict[str, Any],
) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    actors = {
        item.get("actor_id")
        for item in record.get("actors") or []
        if isinstance(item, dict) and item.get("actor_id")
    }
    sources = {
        item.get("source_id")
        for item in record.get("sources") or []
        if isinstance(item, dict) and item.get("source_id")
    }
    events = {
        item.get("event_id")
        for item in record.get("events") or []
        if isinstance(item, dict) and item.get("event_id")
    }

    chain = record.get("authority_chain") or {}
    root = chain.get("root_principal")
    current = chain.get("current_actor")
    evidence_state = chain.get("evidence_state")
    hops = chain.get("hops") or []

    if root not in actors:
        errors.append("DLG-09 root_principal does not resolve to actors")
    if current not in actors:
        errors.append("DLG-09 current_actor does not resolve to actors")

    if not hops:
        errors.append("DLG-00 authority_chain requires at least one hop")
        return errors, None

    if hops[0].get("delegator") != root:
        errors.append("DLG-02 first hop delegator must equal root_principal")
    if hops[-1].get("delegate") != current:
        errors.append("DLG-03 final hop delegate must equal current_actor")

    hop_ids = [hop.get("hop_id") for hop in hops]
    if len(hop_ids) != len(set(hop_ids)):
        errors.append("DLG-00 hop_id values must be unique")

    for index in range(1, len(hops)):
        if hops[index - 1].get("delegate") != hops[index].get("delegator"):
            errors.append(
                f"DLG-01 adjacent hops break continuity at index {index}"
            )

    path = [root] + [hop.get("delegate") for hop in hops]
    if len(path) != len(set(path)):
        errors.append("DLG-04 active delegation path contains a cycle")

    for index, hop in enumerate(hops):
        if hop.get("delegator") not in actors:
            errors.append(f"DLG-09 hop {index} delegator is unknown")
        if hop.get("delegate") not in actors:
            errors.append(f"DLG-09 hop {index} delegate is unknown")
        if hop.get("state") != "active":
            errors.append(
                f"DLG-12 hop {index} is not active (state={hop.get('state')!r})"
            )

    if evidence_state == "legacy_partial" and len(hops) != 1:
        errors.append(
            "DLG-11 legacy_partial is permitted only for migrated one-hop records"
        )

    effective_scope: set[str] | None = None
    effective_prohibited: set[str] = set()
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    for index, hop in enumerate(hops):
        hop_scope = set(hop.get("scope") or [])
        hop_prohibited = set(hop.get("prohibited") or [])
        if effective_scope is None:
            effective_scope = set(hop_scope)
        else:
            amplified = hop_scope - effective_scope
            if amplified:
                errors.append(
                    f"DLG-05 hop {index} amplifies authority with "
                    f"{sorted(amplified)!r}"
                )
            effective_scope &= hop_scope
        effective_prohibited |= hop_prohibited

        start = parse_datetime(hop.get("valid_from"))
        end = parse_datetime(hop.get("valid_until"))
        if start and end and start > end:
            errors.append(f"DLG-07 hop {index} valid_from occurs after valid_until")
        if start:
            effective_from = start if effective_from is None else max(effective_from, start)
        if end:
            effective_until = end if effective_until is None else min(effective_until, end)

        decision_state = hop.get("decision_time_state")
        decided = parse_datetime(hop.get("decided_at"))
        evidence_ref = hop.get("evidence_ref")

        if evidence_state == "complete":
            if decision_state != "recorded" or not decided:
                errors.append(
                    f"DLG-08 complete chain hop {index} requires recorded decided_at"
                )
            if not evidence_ref:
                errors.append(
                    f"DLG-11 complete chain hop {index} requires evidence_ref"
                )
        elif decision_state == "legacy_not_recorded" and decided:
            errors.append(
                f"DLG-11 legacy hop {index} must not invent a decided_at timestamp"
            )

        if evidence_ref and evidence_ref not in sources | events:
            errors.append(
                f"DLG-09 hop {index} evidence_ref {evidence_ref!r} does not resolve"
            )

    if effective_scope is None:
        effective_scope = set()
    if effective_from and effective_until and effective_from > effective_until:
        errors.append("DLG-07 effective delegation time window is empty")

    system_agent = (record.get("system") or {}).get("agent_id")
    if system_agent and current and system_agent != current:
        errors.append(
            "DLG-03 system.agent_id must equal authority_chain.current_actor"
        )

    for index, event in enumerate(record.get("events") or []):
        if not isinstance(event, dict) or event.get("material") is not True:
            continue
        if event.get("actor_id") != current:
            errors.append(
                f"DLG-03 material event {event.get('event_id')!r} actor_id "
                "must equal current_actor"
            )

        occurred = parse_datetime(event.get("occurred_at"))
        if occurred and effective_from and occurred < effective_from:
            errors.append(
                f"DLG-07 material event {event.get('event_id')!r} occurs before "
                "effective delegation window"
            )
        if occurred and effective_until and occurred > effective_until:
            errors.append(
                f"DLG-07 material event {event.get('event_id')!r} occurs after "
                "effective delegation window"
            )

        if evidence_state == "complete" and occurred:
            for hop_index, hop in enumerate(hops):
                decided = parse_datetime(hop.get("decided_at"))
                if decided and decided > occurred:
                    errors.append(
                        f"DLG-08 hop {hop_index} decision occurs after material "
                        f"event {event.get('event_id')!r}"
                    )

    summary = {
        "principal": root,
        "delegate": current,
        "scope": sorted(effective_scope),
        "prohibited": sorted(effective_prohibited),
        "valid_from": _iso(effective_from) if effective_from else None,
        "valid_until": _iso(effective_until) if effective_until else None,
        "delegation_path": path,
        "delegation_evidence_state": evidence_state,
    }

    return errors, summary


def semantic_errors(
    record: dict[str, Any],
) -> tuple[list[str], dict[str, Any] | None]:
    chain_errors, summary = chain_semantic_errors(record)
    if summary is None:
        return chain_errors, None

    compat = copy.deepcopy(record)
    compat["record_schema_version"] = "candidate-record-v0.1"
    compat["authority"] = {
        "principal": summary["principal"],
        "delegate": summary["delegate"],
        "scope": summary["scope"],
        "prohibited": summary["prohibited"],
        "valid_from": summary["valid_from"],
        "valid_until": summary["valid_until"],
    }
    compat.pop("authority_chain", None)

    base_errors = v01_semantic_errors(compat)
    return chain_errors + base_errors, summary


def _drop_keys(value: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key not in keys
    }


def derive_v03_receipt(record: dict[str, Any]) -> dict[str, Any]:
    errors, summary = semantic_errors(record)
    if errors or summary is None:
        raise ValueError("; ".join(errors))

    material_sources = [
        _drop_keys(source, {"material"})
        for source in record["sources"]
        if source.get("material") is True
    ]
    material_actions = [
        _drop_keys(event, {"actor_id", "material"})
        for event in record["events"]
        if event.get("material") is True
    ]

    digest = record_hash(record)
    integrity = {
        "record_hash": digest,
        "derived_from_record_hash": digest,
        "generated_at": record["integrity"]["generated_at"],
    }
    if record["integrity"].get("previous_record_hash"):
        integrity["previous_record_hash"] = record["integrity"]["previous_record_hash"]

    return {
        "receipt_id": f"AR-{record['record_id']}",
        "trace_id": record["trace_id"],
        "record_schema_version": RECORD_VERSION,
        "receipt_version": RECEIPT_VERSION,
        "system": copy.deepcopy(record["system"]),
        "authority": summary,
        "material_sources": material_sources,
        "material_actions": material_actions,
        "verification": copy.deepcopy(record["verification"]),
        "incidents": copy.deepcopy(record["incidents"]),
        "integrity": integrity,
    }


def migrate_v01_to_v02(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("record_schema_version") != "candidate-record-v0.1":
        raise ValueError("migration input must declare candidate-record-v0.1")

    authority = record.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("migration input is missing authority")
    scope = authority.get("scope")
    if not isinstance(scope, list) or not scope:
        raise ValueError("v0.1 authority.scope must be non-empty for v0.2 migration")

    migrated = copy.deepcopy(record)
    migrated["record_schema_version"] = RECORD_VERSION
    migrated.pop("authority", None)

    hop: dict[str, Any] = {
        "hop_id": "legacy-direct-hop-1",
        "delegator": authority["principal"],
        "delegate": authority["delegate"],
        "scope": copy.deepcopy(scope),
        "prohibited": copy.deepcopy(authority.get("prohibited") or []),
        "valid_from": authority["valid_from"],
        "valid_until": authority["valid_until"],
        "decision_time_state": "legacy_not_recorded",
        "state": "active",
    }
    if authority.get("evidence_ref"):
        hop["evidence_ref"] = authority["evidence_ref"]

    migrated["authority_chain"] = {
        "root_principal": authority["principal"],
        "current_actor": authority["delegate"],
        "evidence_state": "legacy_partial",
        "hops": [hop],
    }

    note = str(migrated.get("notes") or "").strip()
    migration_note = (
        "Migrated from candidate-record-v0.1 without inventing a delegation "
        "decision timestamp; authority_chain.evidence_state is legacy_partial."
    )
    migrated["notes"] = f"{note} {migration_note}".strip()
    return migrated


def core_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    authority = receipt["authority"]
    return {
        "trace_id": receipt["trace_id"],
        "system": receipt["system"],
        "authority": {
            "principal": authority["principal"],
            "delegate": authority["delegate"],
            "scope": authority["scope"],
            "prohibited": authority.get("prohibited") or [],
            "valid_from": authority["valid_from"],
            "valid_until": authority["valid_until"],
        },
        "material_sources": receipt["material_sources"],
        "material_actions": receipt["material_actions"],
        "verification": receipt["verification"],
        "incidents": receipt["incidents"],
    }


def run_self_test() -> int:
    record_schema = load_json(V02_SCHEMA)
    receipt_schema = load_json(V03_RECEIPT_SCHEMA)
    Draft202012Validator.check_schema(record_schema)
    Draft202012Validator.check_schema(receipt_schema)

    record = load_json(V02_EXAMPLE)
    structural = validate_record_structure(record, record_schema)
    assert not structural, structural
    errors, summary = semantic_errors(record)
    assert not errors, errors
    assert summary == {
        "principal": "user-pilot",
        "delegate": "agent-specialist-7",
        "scope": ["analyze", "read", "send_email"],
        "prohibited": [],
        "valid_from": "2026-09-18T14:02:00Z",
        "valid_until": "2026-09-18T14:45:00Z",
        "delegation_path": [
            "user-pilot",
            "agent-orchestrator-4",
            "agent-specialist-7",
        ],
        "delegation_evidence_state": "complete",
    }

    receipt = derive_v03_receipt(record)
    receipt_errors = validate_derived_receipt(receipt, receipt_schema)
    assert not receipt_errors, receipt_errors
    assert receipt["authority"]["delegation_path"][-1] == record["system"]["agent_id"]

    # Migration preserves the v0.1 human-visible core without inventing a
    # delegation decision timestamp.
    legacy = load_json(V01_EXAMPLE)
    legacy_receipt = derive_v01_receipt(legacy)
    migrated = migrate_v01_to_v02(legacy)
    migrated_structural = validate_record_structure(migrated, record_schema)
    assert not migrated_structural, migrated_structural
    migrated_errors, migrated_summary = semantic_errors(migrated)
    assert not migrated_errors, migrated_errors
    assert migrated_summary is not None
    assert migrated_summary["delegation_evidence_state"] == "legacy_partial"
    assert migrated["authority_chain"]["hops"][0]["decision_time_state"] == (
        "legacy_not_recorded"
    )
    assert "decided_at" not in migrated["authority_chain"]["hops"][0]

    migrated_receipt = derive_v03_receipt(migrated)
    migrated_receipt_errors = validate_derived_receipt(
        migrated_receipt, receipt_schema
    )
    assert not migrated_receipt_errors, migrated_receipt_errors
    assert core_projection(migrated_receipt) == core_projection(legacy_receipt)

    cases: list[tuple[str, str, dict[str, Any]]] = []

    broken = copy.deepcopy(record)
    broken["authority_chain"]["hops"][1]["delegator"] = "user-pilot"
    cases.append(("broken-continuity", "DLG-01", broken))

    cycle = copy.deepcopy(record)
    cycle["authority_chain"]["hops"][1]["delegate"] = "user-pilot"
    cycle["authority_chain"]["current_actor"] = "user-pilot"
    cycle["system"]["agent_id"] = "user-pilot"
    for event in cycle["events"]:
        if event.get("material") is True:
            event["actor_id"] = "user-pilot"
    cases.append(("cycle", "DLG-04", cycle))

    amplified = copy.deepcopy(record)
    amplified["authority_chain"]["hops"][1]["scope"].append("delete_account")
    cases.append(("scope-amplification", "DLG-05", amplified))

    revoked = copy.deepcopy(record)
    revoked["authority_chain"]["hops"][1]["state"] = "revoked"
    cases.append(("revoked-hop", "DLG-12", revoked))

    missing_evidence = copy.deepcopy(record)
    missing_evidence["authority_chain"]["hops"][1].pop("evidence_ref")
    cases.append(("missing-hop-evidence", "DLG-11", missing_evidence))

    late_decision = copy.deepcopy(record)
    late_decision["authority_chain"]["hops"][1]["decided_at"] = (
        "2026-09-18T14:21:00Z"
    )
    cases.append(("late-hop-decision", "DLG-08", late_decision))

    actor_mismatch = copy.deepcopy(record)
    actor_mismatch["events"][0]["actor_id"] = "agent-orchestrator-4"
    cases.append(("event-actor-mismatch", "DLG-03", actor_mismatch))

    outside_window = copy.deepcopy(record)
    outside_window["events"][-1]["occurred_at"] = "2026-09-18T14:46:00Z"
    outside_window["events"][-1]["authorization_decided_at"] = (
        "2026-09-18T14:44:00Z"
    )
    cases.append(("outside-window", "DLG-07", outside_window))

    legacy_multihop = copy.deepcopy(record)
    legacy_multihop["authority_chain"]["evidence_state"] = "legacy_partial"
    cases.append(("legacy-multihop", "DLG-11", legacy_multihop))

    prohibited = copy.deepcopy(record)
    prohibited["authority_chain"]["hops"][0]["prohibited"] = ["send_email"]
    cases.append(("upstream-prohibition", "prohibited", prohibited))

    for label, marker, candidate in cases:
        candidate_errors, _ = semantic_errors(candidate)
        assert candidate_errors, f"{label}: invalid candidate was accepted"
        assert any(
            marker in error for error in candidate_errors
        ), f"{label}: expected marker {marker!r}, got {candidate_errors!r}"

    print(
        "candidate-record-v0.2 multi-hop self-test passed: "
        "native two-hop record, loss-aware v0.1 migration, "
        f"and {len(cases)} adversarial cases."
    )
    return 0


def main() -> int:
    try:
        return run_self_test()
    except (
        OSError,
        json.JSONDecodeError,
        SchemaError,
        ValueError,
        AssertionError,
    ) as exc:
        print(f"ERROR: multi-hop v0.2 prototype failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
