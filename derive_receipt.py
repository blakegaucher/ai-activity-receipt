#!/usr/bin/env python3
"""Deterministically derive a candidate AI Activity Receipt from a canonical record."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from validate_receipts import invariant_violations, schema_errors


ROOT = Path(__file__).resolve().parent
DEFAULT_RECORD_SCHEMA = ROOT / "activity-record.schema.json"
DEFAULT_RECEIPT_SCHEMA = ROOT / "activity-receipt.schema.json"
DEFAULT_EXAMPLE_RECORD = ROOT / "examples" / "canonical-record.json"
DEFAULT_EXPECTED_RECEIPT = ROOT / "examples" / "derived-receipt.json"
RECEIPT_VERSION = "candidate-v0.2"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_record_bytes(record: dict[str, Any]) -> bytes:
    """Project-local deterministic JSON serialization used by candidate-v0.1.

    This is intentionally documented as a project-local profile, not as a claim
    of RFC 8785/JCS conformance.
    """
    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def record_hash(record: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_record_bytes(record)).hexdigest()


def validate_record_structure(
    record: Any,
    schema: dict[str, Any],
) -> list[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.absolute_path),
    )
    output: list[str] = []
    for error in errors:
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def record_semantic_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    actors = record.get("actors") or []
    actor_values = [
        actor.get("actor_id")
        for actor in actors
        if isinstance(actor, dict) and actor.get("actor_id")
    ]
    actor_ids = set(actor_values)
    for actor_id, count in Counter(actor_values).items():
        if count > 1:
            errors.append(f"duplicate actor_id {actor_id!r}")

    sources = record.get("sources") or []
    source_values = [
        source.get("source_id")
        for source in sources
        if isinstance(source, dict) and source.get("source_id")
    ]
    source_ids = set(source_values)
    material_source_ids = {
        source.get("source_id")
        for source in sources
        if isinstance(source, dict)
        and source.get("source_id")
        and source.get("material") is True
    }
    for source_id, count in Counter(source_values).items():
        if count > 1:
            errors.append(f"duplicate source_id {source_id!r}")

    events = record.get("events") or []
    event_values = [
        event.get("event_id")
        for event in events
        if isinstance(event, dict) and event.get("event_id")
    ]
    event_ids = set(event_values)
    material_event_ids = {
        event.get("event_id")
        for event in events
        if isinstance(event, dict)
        and event.get("event_id")
        and event.get("material") is True
    }
    for event_id, count in Counter(event_values).items():
        if count > 1:
            errors.append(f"duplicate event_id {event_id!r}")

    system = record.get("system") or {}
    authority = record.get("authority") or {}

    agent_id = system.get("agent_id")
    if agent_id and agent_id not in actor_ids:
        errors.append(f"system.agent_id {agent_id!r} is not registered in actors")

    for key in ("principal", "delegate"):
        actor_id = authority.get(key)
        if actor_id and actor_id not in actor_ids:
            errors.append(f"authority.{key} {actor_id!r} is not registered in actors")

    if (
        agent_id
        and authority.get("delegate")
        and agent_id != authority.get("delegate")
    ):
        errors.append(
            "candidate direct-delegation profile requires "
            "authority.delegate == system.agent_id"
        )

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue

        actor_id = event.get("actor_id")
        if actor_id and actor_id not in actor_ids:
            errors.append(
                f"events[{index}].actor_id {actor_id!r} is not registered in actors"
            )

        for source_ref in event.get("source_refs") or []:
            if source_ref not in source_ids:
                errors.append(
                    f"events[{index}].source_refs contains unknown source {source_ref!r}"
                )

        if event.get("material") is True:
            for source_ref in event.get("source_refs") or []:
                if source_ref not in material_source_ids:
                    errors.append(
                        f"material event {event.get('event_id')!r} references "
                        f"non-material source {source_ref!r}"
                    )

    verification = record.get("verification") or {}
    material_evidence_ids = material_source_ids | material_event_ids
    for evidence_ref in verification.get("evidence_refs") or []:
        if evidence_ref not in source_ids | event_ids:
            errors.append(
                f"verification.evidence_refs contains unknown evidence {evidence_ref!r}"
            )
        elif evidence_ref not in material_evidence_ids:
            errors.append(
                f"verification evidence {evidence_ref!r} is not material and "
                "cannot be represented in the candidate Receipt view"
            )

    for index, incident in enumerate(record.get("incidents") or []):
        if not isinstance(incident, dict):
            continue
        event_id = incident.get("event_id")
        if event_id and event_id not in event_ids:
            errors.append(
                f"incidents[{index}].event_id {event_id!r} does not resolve"
            )
        elif event_id and event_id not in material_event_ids:
            errors.append(
                f"incident event {event_id!r} is not material and cannot be "
                "represented in the candidate Receipt view"
            )

    evidence_ref = authority.get("evidence_ref")
    if evidence_ref and evidence_ref not in source_ids | event_ids:
        errors.append(
            f"authority.evidence_ref {evidence_ref!r} does not resolve"
        )

    return errors


def _drop_keys(value: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key not in keys
    }


def derive_receipt(
    record: dict[str, Any],
    receipt_id: str | None = None,
) -> dict[str, Any]:
    semantic = record_semantic_errors(record)
    if semantic:
        raise ValueError("; ".join(semantic))

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

    integrity = {
        "record_hash": record_hash(record),
        "derived_from_record_hash": record_hash(record),
        "generated_at": record["integrity"]["generated_at"],
    }
    if record["integrity"].get("previous_record_hash"):
        integrity["previous_record_hash"] = record["integrity"][
            "previous_record_hash"
        ]

    authority = _drop_keys(record["authority"], {"evidence_ref"})

    return {
        "receipt_id": receipt_id or f"AR-{record['record_id']}",
        "trace_id": record["trace_id"],
        "record_schema_version": record["record_schema_version"],
        "receipt_version": RECEIPT_VERSION,
        "system": copy.deepcopy(record["system"]),
        "authority": authority,
        "material_sources": material_sources,
        "material_actions": material_actions,
        "verification": copy.deepcopy(record["verification"]),
        "incidents": copy.deepcopy(record["incidents"]),
        "integrity": integrity,
    }


def validate_derived_receipt(
    receipt: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for item in schema_errors(receipt, receipt_schema):
        errors.append(
            f"receipt schema {item['path']}: {item['reason']}"
        )
    for item in invariant_violations(receipt):
        errors.append(
            f"{item['invariant']} {item['path']}: {item['reason']}"
        )
    return errors


def run_self_test(
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> int:
    record = load_json(DEFAULT_EXAMPLE_RECORD)
    expected = load_json(DEFAULT_EXPECTED_RECEIPT)

    structural = validate_record_structure(record, record_schema)
    assert not structural, structural

    semantic = record_semantic_errors(record)
    assert not semantic, semantic

    derived = derive_receipt(record)
    assert derived == expected, (
        "derived Receipt does not match examples/derived-receipt.json"
    )

    receipt_errors = validate_derived_receipt(derived, receipt_schema)
    assert not receipt_errors, receipt_errors

    assert derive_receipt(record) == derive_receipt(record)
    assert derived["integrity"]["record_hash"] == (
        "sha256:b60d8e6aada04a641cf402a8bca684d01c92a83fcf56cda7273f6de74cc42b65"
    )

    print("Canonical Activity Record derivation self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive a candidate AI Activity Receipt from a canonical record."
    )
    parser.add_argument("record", nargs="?", help="Canonical Activity Record JSON file")
    parser.add_argument("--output", help="Write the derived Receipt to this path")
    parser.add_argument("--receipt-id", help="Override the deterministic Receipt ID")
    parser.add_argument(
        "--record-schema",
        default=str(DEFAULT_RECORD_SCHEMA),
        help="Path to activity-record.schema.json",
    )
    parser.add_argument(
        "--receipt-schema",
        default=str(DEFAULT_RECEIPT_SCHEMA),
        help="Path to activity-receipt.schema.json",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        record_schema = load_json(Path(args.record_schema))
        receipt_schema = load_json(Path(args.receipt_schema))
        Draft202012Validator.check_schema(record_schema)
        Draft202012Validator.check_schema(receipt_schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load schema: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        return run_self_test(record_schema, receipt_schema)

    if not args.record:
        parser.error("provide a canonical record JSON file or use --self-test")

    try:
        record = load_json(Path(args.record))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load record: {exc}", file=sys.stderr)
        return 2

    if not isinstance(record, dict):
        print("ERROR: canonical record must be a JSON object", file=sys.stderr)
        return 2

    structural = validate_record_structure(record, record_schema)
    if structural:
        for error in structural:
            print(f"ERROR: record schema {error}", file=sys.stderr)
        return 1

    semantic = record_semantic_errors(record)
    if semantic:
        for error in semantic:
            print(f"ERROR: record semantic {error}", file=sys.stderr)
        return 1

    try:
        receipt = derive_receipt(record, receipt_id=args.receipt_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    receipt_errors = validate_derived_receipt(receipt, receipt_schema)
    if receipt_errors:
        for error in receipt_errors:
            print(f"ERROR: derived {error}", file=sys.stderr)
        return 1

    rendered = json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
