#!/usr/bin/env python3
"""Validate the standalone external-evidence-reference research profile.

This prototype links external evidence artifacts to a canonical Activity Record
without embedding raw credentials or full third-party proof payloads.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from derive_receipt import record_hash  # noqa: E402

DEFAULT_SCHEMA = ROOT / "research" / "external-evidence-reference.schema.json"
DEFAULT_EXAMPLE = ROOT / "research" / "external-evidence-reference.example.json"
DEFAULT_RECORD = ROOT / "research" / "workflow-pilot" / "research-email.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def structural_errors(doc: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(doc),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def semantic_errors(
    doc: dict[str, Any],
    record: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if doc["record_id"] != record.get("record_id"):
        errors.append(
            "record_id does not match the canonical Activity Record "
            f"({doc['record_id']!r} != {record.get('record_id')!r})"
        )

    expected_digest = record_hash(record)
    supplied_digest = doc["record_binding"]["digest"]
    if supplied_digest != expected_digest:
        errors.append(
            "record_binding.digest does not match the exact canonical Activity "
            f"Record ({supplied_digest!r} != {expected_digest!r})"
        )

    event_ids = {
        item.get("event_id")
        for item in record.get("events") or []
        if isinstance(item, dict) and item.get("event_id")
    }
    source_ids = {
        item.get("source_id")
        for item in record.get("sources") or []
        if isinstance(item, dict) and item.get("source_id")
    }

    seen: set[str] = set()
    for index, ref in enumerate(doc["references"]):
        evidence_id = ref["evidence_id"]
        if evidence_id in seen:
            errors.append(
                f"references[{index}] duplicates evidence_id {evidence_id!r}"
            )
        seen.add(evidence_id)

        subject = ref["subject"]
        subject_type = subject["type"]
        subject_id = subject.get("id")
        if subject_type == "event" and subject_id not in event_ids:
            errors.append(
                f"references[{index}].subject.id {subject_id!r} does not "
                "resolve to a canonical-record event"
            )
        if subject_type == "source" and subject_id not in source_ids:
            errors.append(
                f"references[{index}].subject.id {subject_id!r} does not "
                "resolve to a canonical-record source"
            )

        validation = ref["validation"]
        state = validation["state"]
        if state == "valid":
            if not validation.get("validated_at"):
                errors.append(
                    f"references[{index}] state='valid' requires validated_at"
                )
            if not validation.get("validator"):
                errors.append(
                    f"references[{index}] state='valid' requires validator"
                )

        if ref["kind"] == "repository_receipt":
            if ref.get("standard") != "C2PA":
                errors.append(
                    f"references[{index}] repository_receipt must declare "
                    "standard='C2PA'"
                )
            if "c2pa.repository-receipt" not in str(ref.get("profile") or ""):
                errors.append(
                    f"references[{index}] repository_receipt profile must "
                    "identify c2pa.repository-receipt"
                )
            if not ref.get("external_id"):
                errors.append(
                    f"references[{index}] repository_receipt requires "
                    "external_id for the repository-canonical manifest ID"
                )
            if not ref.get("locator", {}).get("uri"):
                errors.append(
                    f"references[{index}] repository_receipt requires an "
                    "external verification/retrieval URI"
                )

    return errors


def validate(
    doc: Any,
    schema: dict[str, Any],
    record: dict[str, Any],
) -> list[str]:
    errors = structural_errors(doc, schema)
    if errors:
        return errors
    if not isinstance(doc, dict):
        return ["$: evidence-reference index must be an object"]
    return semantic_errors(doc, record)


def run_self_test(
    schema: dict[str, Any],
    example: dict[str, Any],
    record: dict[str, Any],
) -> int:
    errors = validate(example, schema, record)
    assert not errors, errors

    duplicate = copy.deepcopy(example)
    duplicate["references"][1]["evidence_id"] = duplicate["references"][0][
        "evidence_id"
    ]
    errors = validate(duplicate, schema, record)
    assert any("duplicates evidence_id" in error for error in errors)

    unknown_source = copy.deepcopy(example)
    unknown_source["references"][0]["subject"]["id"] = "src-missing"
    errors = validate(unknown_source, schema, record)
    assert any("does not resolve to a canonical-record source" in error for error in errors)

    unknown_event = copy.deepcopy(example)
    unknown_event["references"][2]["subject"]["id"] = "event-missing"
    errors = validate(unknown_event, schema, record)
    assert any("does not resolve to a canonical-record event" in error for error in errors)

    wrong_record = copy.deepcopy(example)
    wrong_record["record_id"] = "other-record"
    errors = validate(wrong_record, schema, record)
    assert any("record_id does not match" in error for error in errors)

    wrong_digest = copy.deepcopy(example)
    wrong_digest["record_binding"]["digest"] = "sha256:" + ("0" * 64)
    errors = validate(wrong_digest, schema, record)
    assert any("record_binding.digest does not match" in error for error in errors)

    changed_record = copy.deepcopy(record)
    changed_record["notes"] = "Synthetic record changed after evidence index binding."
    errors = validate(example, schema, changed_record)
    assert any("record_binding.digest does not match" in error for error in errors)

    unsubstantiated_valid = copy.deepcopy(example)
    unsubstantiated_valid["references"][0]["validation"] = {"state": "valid"}
    errors = validate(unsubstantiated_valid, schema, record)
    assert any("requires validated_at" in error for error in errors)
    assert any("requires validator" in error for error in errors)

    malformed_repository_receipt = copy.deepcopy(example)
    repository_ref = malformed_repository_receipt["references"][1]
    repository_ref.pop("external_id")
    repository_ref["profile"] = "2.4"
    errors = validate(malformed_repository_receipt, schema, record)
    assert any("requires external_id" in error for error in errors)
    assert any("identify c2pa.repository-receipt" in error for error in errors)

    embedded_proof = copy.deepcopy(example)
    embedded_proof["references"][1]["locator"]["proof"] = {
        "alg": "ES256",
        "value": "SHOULD_NOT_BE_EMBEDDED",
    }
    errors = validate(embedded_proof, schema, record)
    assert any("Additional properties are not allowed" in error for error in errors)

    print(
        "External evidence-reference self-test passed: "
        "C2PA-oriented reference example plus 9 adversarial mutations, "
        "including exact canonical-record digest binding."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the external-evidence-reference research profile."
    )
    parser.add_argument(
        "index",
        nargs="?",
        default=str(DEFAULT_EXAMPLE),
        help="External evidence-reference index JSON.",
    )
    parser.add_argument(
        "--record",
        default=str(DEFAULT_RECORD),
        help="Canonical Activity Record used to resolve subjects.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
        help="External evidence-reference JSON Schema.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        schema = load_json(Path(args.schema))
        Draft202012Validator.check_schema(schema)
        doc = load_json(Path(args.index))
        record = load_json(Path(args.record))
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load schema/index/record: {exc}", file=sys.stderr)
        return 2

    if not isinstance(record, dict):
        print("ERROR: canonical record must be an object", file=sys.stderr)
        return 2

    if args.self_test:
        if not isinstance(doc, dict):
            print("ERROR: self-test index must be an object", file=sys.stderr)
            return 2
        return run_self_test(schema, doc, record)

    errors = validate(doc, schema, record)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("External evidence-reference index is structurally and semantically valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
