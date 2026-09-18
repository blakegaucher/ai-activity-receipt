#!/usr/bin/env python3
"""Validate the candidate attestation trust-policy research profile.

This validates identity/trust/key-lifecycle policy structure only. It does not
perform cryptographic signature verification.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "research" / "attestation-trust-policy.schema.json"
DEFAULT_EXAMPLE = ROOT / "research" / "attestation-trust-policy.example.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid date-time") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    return parsed


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


def semantic_errors(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    payload_types = doc["payload_types"]
    payload_ids = [item["payload_type"] for item in payload_types]
    if len(set(payload_ids)) != len(payload_ids):
        errors.append("payload_type identifiers must be unique")

    schema_versions = [item["record_schema_version"] for item in payload_types]
    if len(set(schema_versions)) != len(schema_versions):
        errors.append("record_schema_version values must map to one payload type each")

    for index, payload in enumerate(payload_types):
        parsed = urlparse(payload["payload_type"])
        if parsed.scheme not in {"http", "https"}:
            errors.append(
                f"payload_types[{index}].payload_type must be a project-controlled "
                "HTTP(S) URI in this candidate policy"
            )

    roles = doc["roles"]
    role_ids = [role["role_id"] for role in roles]
    if len(set(role_ids)) != len(role_ids):
        errors.append("role_id values must be unique")
    known_roles = set(role_ids)
    known_payloads = set(payload_ids)

    role_by_id = {role["role_id"]: role for role in roles}
    for index, role in enumerate(roles):
        unknown = sorted(set(role["may_attest_payload_types"]) - known_payloads)
        if unknown:
            errors.append(
                f"roles[{index}] references unknown payload type(s): {unknown!r}"
            )

    signers = doc["trusted_signers"]
    signer_ids = [signer["signer_id"] for signer in signers]
    key_ids = [signer["key_id"] for signer in signers]
    if len(set(signer_ids)) != len(signer_ids):
        errors.append("signer_id values must be unique")
    if len(set(key_ids)) != len(key_ids):
        errors.append("key_id values must be unique within one trust policy")

    for index, signer in enumerate(signers):
        if signer["role"] not in known_roles:
            errors.append(
                f"trusted_signers[{index}].role {signer['role']!r} is unknown"
            )

        valid_from = parse_time(
            signer["valid_from"], f"trusted_signers[{index}].valid_from"
        )
        valid_until = parse_time(
            signer["valid_until"], f"trusted_signers[{index}].valid_until"
        )
        if valid_from > valid_until:
            errors.append(
                f"trusted_signers[{index}] valid_from occurs after valid_until"
            )

        if signer["identity_type"] == "test_identity":
            if signer["status"] != "test_only":
                errors.append(
                    f"trusted_signers[{index}] test_identity must have status='test_only'"
                )
        elif signer["status"] == "test_only":
            errors.append(
                f"trusted_signers[{index}] status='test_only' requires identity_type='test_identity'"
            )

        if doc["environment"] == "production":
            if signer["status"] == "test_only":
                errors.append(
                    f"trusted_signers[{index}] test-only signer is forbidden in production"
                )
            if signer["status"] == "active" and not signer.get("revocation_ref"):
                errors.append(
                    f"trusted_signers[{index}] active production signer requires revocation_ref"
                )

    required_roles = doc["verification"]["required_roles"]
    for role in required_roles:
        if role not in known_roles:
            errors.append(f"verification.required_roles contains unknown role {role!r}")

    eligible_statuses = {"active"}
    if doc["environment"] == "research":
        eligible_statuses.add("test_only")

    eligible_signers = [
        signer for signer in signers if signer["status"] in eligible_statuses
    ]

    for required_role in required_roles:
        candidates = [
            signer
            for signer in eligible_signers
            if signer["role"] == required_role
        ]
        if not candidates:
            errors.append(
                f"required role {required_role!r} has no eligible trusted signer"
            )
            continue

        role_payloads = set(
            role_by_id[required_role]["may_attest_payload_types"]
        )
        if not role_payloads:
            errors.append(
                f"required role {required_role!r} has no allowed payload types"
            )

    if doc["verification"]["minimum_signatures"] > len(eligible_signers):
        errors.append(
            "verification.minimum_signatures exceeds number of eligible trusted signers"
        )

    if (
        doc["environment"] == "production"
        and doc["revocation"]["unknown_status_behavior"] != "fail_closed"
    ):
        errors.append(
            "production policy must fail closed when signer revocation status is unknown"
        )

    return errors


def validate(doc: Any, schema: dict[str, Any]) -> list[str]:
    errors = structural_errors(doc, schema)
    if errors:
        return errors
    if not isinstance(doc, dict):
        return ["$: trust policy must be an object"]
    try:
        return semantic_errors(doc)
    except ValueError as exc:
        return [f"semantic time error: {exc}"]


def run_self_test(schema: dict[str, Any], example: dict[str, Any]) -> int:
    errors = validate(example, schema)
    assert not errors, errors

    duplicate_signer = copy.deepcopy(example)
    duplicate_signer["trusted_signers"].append(
        copy.deepcopy(duplicate_signer["trusted_signers"][0])
    )
    errors = validate(duplicate_signer, schema)
    assert any("signer_id values must be unique" in error for error in errors)
    assert any("key_id values must be unique" in error for error in errors)

    missing_required_role = copy.deepcopy(example)
    missing_required_role["trusted_signers"][0]["role"] = "independent_verifier"
    errors = validate(missing_required_role, schema)
    assert any("has no eligible trusted signer" in error for error in errors)

    inverted_window = copy.deepcopy(example)
    inverted_window["trusted_signers"][0]["valid_from"] = "2027-09-19T00:00:00Z"
    errors = validate(inverted_window, schema)
    assert any("valid_from occurs after valid_until" in error for error in errors)

    test_identity_active = copy.deepcopy(example)
    test_identity_active["trusted_signers"][0]["status"] = "active"
    errors = validate(test_identity_active, schema)
    assert any("test_identity must have status='test_only'" in error for error in errors)

    production_test_signer = copy.deepcopy(example)
    production_test_signer["environment"] = "production"
    errors = validate(production_test_signer, schema)
    assert any("test-only signer is forbidden in production" in error for error in errors)
    assert any("has no eligible trusted signer" in error for error in errors)

    production_unknown_revocation = copy.deepcopy(example)
    production_unknown_revocation["environment"] = "production"
    signer = production_unknown_revocation["trusted_signers"][0]
    signer["identity_type"] = "public_key_fingerprint"
    signer["identity"] = "sha256:example-production-identity"
    signer["status"] = "active"
    production_unknown_revocation["revocation"]["unknown_status_behavior"] = (
        "policy_specific"
    )
    errors = validate(production_unknown_revocation, schema)
    assert any("requires revocation_ref" in error for error in errors)
    assert any("must fail closed" in error for error in errors)

    bad_payload = copy.deepcopy(example)
    bad_payload["payload_types"][0]["payload_type"] = "not-a-uri"
    errors = validate(bad_payload, schema)
    assert any("project-controlled HTTP(S) URI" in error for error in errors)

    unknown_role_payload = copy.deepcopy(example)
    unknown_role_payload["roles"][0]["may_attest_payload_types"] = [
        "https://example.invalid/no-such-payload-type"
    ]
    errors = validate(unknown_role_payload, schema)
    assert any("references unknown payload type" in error for error in errors)

    too_many_signatures = copy.deepcopy(example)
    too_many_signatures["verification"]["minimum_signatures"] = 2
    errors = validate(too_many_signatures, schema)
    assert any("minimum_signatures exceeds" in error for error in errors)

    private_key_field = copy.deepcopy(example)
    private_key_field["trusted_signers"][0]["private_key"] = "SHOULD_NOT_BE_HERE"
    errors = validate(private_key_field, schema)
    assert any("Additional properties are not allowed" in error for error in errors)

    print(
        "Attestation trust-policy self-test passed: "
        "1 valid research policy + 10 adversarial mutations."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the candidate attestation trust policy."
    )
    parser.add_argument(
        "policy",
        nargs="?",
        default=str(DEFAULT_EXAMPLE),
        help="Trust-policy JSON file.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
        help="Trust-policy JSON Schema.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        schema = load_json(Path(args.schema))
        Draft202012Validator.check_schema(schema)
        policy = load_json(Path(args.policy))
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load policy/schema: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        if not isinstance(policy, dict):
            print("ERROR: self-test policy must be an object", file=sys.stderr)
            return 2
        return run_self_test(schema, policy)

    errors = validate(policy, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Attestation trust policy is structurally and semantically valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
