#!/usr/bin/env python3
"""Research-only DSSE signing/verification prototype for canonical Activity Records.

This prototype demonstrates:
- DSSE v1 pre-authentication encoding (PAE);
- exact-byte Ed25519 signatures over an Activity Record artifact;
- separate trust-policy evaluation;
- canonical-record schema and semantic validation after signature verification;
- deterministic Receipt derivation and record-hash binding.

Private keys are generated only in memory by the self-test. No private key is
stored in the repository. This is not production key management.
"""

from __future__ import annotations

import base64
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from derive_receipt import (  # noqa: E402
    derive_receipt,
    record_hash,
    record_semantic_errors,
    validate_derived_receipt,
    validate_record_structure,
)
from research.validate_attestation_policy import (  # noqa: E402
    validate as validate_policy,
)

POLICY_SCHEMA = ROOT / "research" / "attestation-trust-policy.schema.json"
POLICY_EXAMPLE = ROOT / "research" / "attestation-trust-policy.example.json"
ENVELOPE_SCHEMA = ROOT / "research" / "dsse-envelope.schema.json"
RECORD_EXAMPLE = ROOT / "research" / "workflow-pilot" / "research-email.json"
RECORD_SCHEMA = ROOT / "activity-record.schema.json"
RECEIPT_SCHEMA = ROOT / "activity-receipt.schema.json"


class VerificationError(ValueError):
    """Raised when one verification layer fails."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bytes(path: Path) -> bytes:
    return path.read_bytes()


def parse_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VerificationError(f"{label} is not a valid date-time") from exc
    if parsed.utcoffset() is None:
        raise VerificationError(f"{label} must include a timezone offset")
    return parsed


def dsse_pae(payload_type: str, payload: bytes) -> bytes:
    """Return DSSE v1 Pre-Authentication Encoding.

    PAE("DSSEv1", payloadType, payload) is:
      b"DSSEv1" SP len(type) SP type SP len(payload) SP payload
    where lengths are base-10 ASCII byte lengths.
    """
    if not isinstance(payload_type, str) or not payload_type:
        raise ValueError("payload_type must be a non-empty string")
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")

    payload_type_bytes = payload_type.encode("utf-8")
    return b" ".join(
        (
            b"DSSEv1",
            str(len(payload_type_bytes)).encode("ascii"),
            payload_type_bytes,
            str(len(payload)).encode("ascii"),
            payload,
        )
    )


def strict_b64decode(value: Any, label: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{label} must be a non-empty base64 string")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise VerificationError(f"{label} is not valid base64") from exc


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


def sign_payload(
    payload: bytes,
    payload_type: str,
    private_key: Ed25519PrivateKey,
    key_id: str,
) -> dict[str, Any]:
    if not isinstance(key_id, str) or not key_id:
        raise ValueError("key_id must be a non-empty string")

    signature = private_key.sign(dsse_pae(payload_type, payload))
    return {
        "payloadType": payload_type,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [
            {
                "keyid": key_id,
                "sig": base64.b64encode(signature).decode("ascii"),
            }
        ],
    }


def signer_eligible(
    signer: dict[str, Any],
    policy: dict[str, Any],
    verification_time: datetime,
) -> tuple[bool, str | None]:
    status = signer["status"]
    environment = policy["environment"]

    if environment == "production":
        if status != "active":
            return False, f"production signer status {status!r} is not active"
    else:
        if status not in {"active", "test_only"}:
            return False, f"research signer status {status!r} is not eligible"

    valid_from = parse_time(signer["valid_from"], "signer.valid_from")
    valid_until = parse_time(signer["valid_until"], "signer.valid_until")
    if verification_time < valid_from:
        return False, "signer is not yet valid at verification time"
    if verification_time > valid_until:
        return False, "signer is expired at verification time"

    return True, None


def verify_signatures(
    envelope: dict[str, Any],
    policy: dict[str, Any],
    verification_keys: Mapping[str, Ed25519PublicKey],
    verification_time: datetime,
) -> list[dict[str, str]]:
    payload_type = envelope["payloadType"]
    payload = strict_b64decode(envelope["payload"], "envelope.payload")
    pae = dsse_pae(payload_type, payload)

    signer_by_key_id = {
        signer["key_id"]: signer for signer in policy["trusted_signers"]
    }
    role_by_id = {role["role_id"]: role for role in policy["roles"]}

    seen_key_ids: set[str] = set()
    verified: list[dict[str, str]] = []
    errors: list[str] = []

    for index, signature_entry in enumerate(envelope["signatures"]):
        key_id = signature_entry["keyid"]
        if key_id in seen_key_ids:
            errors.append(
                f"signatures[{index}] duplicates keyid {key_id!r}; "
                "duplicate signatures do not count toward threshold"
            )
            continue
        seen_key_ids.add(key_id)

        signer = signer_by_key_id.get(key_id)
        if signer is None:
            errors.append(
                f"signatures[{index}] keyid {key_id!r} has no trusted signer candidate"
            )
            continue

        role = role_by_id.get(signer["role"])
        if role is None:
            errors.append(
                f"signatures[{index}] signer role {signer['role']!r} is unknown"
            )
            continue
        if payload_type not in role["may_attest_payload_types"]:
            errors.append(
                f"signatures[{index}] signer role {signer['role']!r} "
                "is not permitted for this payload type"
            )
            continue

        eligible, reason = signer_eligible(signer, policy, verification_time)
        if not eligible:
            errors.append(f"signatures[{index}] signer is not eligible: {reason}")
            continue

        material_uri = signer["verification_material"]["uri"]
        public_key = verification_keys.get(material_uri)
        if public_key is None:
            errors.append(
                f"signatures[{index}] trusted verification material is unavailable "
                f"for {material_uri!r}"
            )
            continue

        signature = strict_b64decode(
            signature_entry["sig"],
            f"signatures[{index}].sig",
        )
        try:
            public_key.verify(signature, pae)
        except InvalidSignature:
            errors.append(f"signatures[{index}] cryptographic signature is invalid")
            continue

        verified.append(
            {
                "signer_id": signer["signer_id"],
                "role": signer["role"],
                "key_id": key_id,
                "identity_type": signer["identity_type"],
                "identity": signer["identity"],
            }
        )

    if errors and not verified:
        raise VerificationError("; ".join(errors))

    unique_signers = {item["signer_id"] for item in verified}
    if len(unique_signers) < policy["verification"]["minimum_signatures"]:
        raise VerificationError(
            "verified unique signer count does not satisfy minimum_signatures"
        )

    verified_roles = {item["role"] for item in verified}
    missing_roles = sorted(
        set(policy["verification"]["required_roles"]) - verified_roles
    )
    if missing_roles:
        raise VerificationError(
            f"verified signatures do not satisfy required role(s): {missing_roles!r}"
        )

    # Any malformed/duplicate/untrusted signature entry is surfaced instead of
    # being silently ignored, even if another signature verifies.
    if errors:
        raise VerificationError("; ".join(errors))

    return verified


def verify_envelope(
    envelope: Any,
    *,
    policy: dict[str, Any],
    policy_schema: dict[str, Any],
    envelope_schema: dict[str, Any],
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
    verification_keys: Mapping[str, Ed25519PublicKey],
    verification_time: datetime,
    provided_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_errors = validate_policy(policy, policy_schema)
    if policy_errors:
        raise VerificationError(
            "trust policy is invalid: " + "; ".join(policy_errors)
        )

    envelope_errors = structural_errors(envelope, envelope_schema)
    if envelope_errors:
        raise VerificationError(
            "DSSE envelope structure is invalid: " + "; ".join(envelope_errors)
        )
    if not isinstance(envelope, dict):
        raise VerificationError("DSSE envelope must be an object")

    payload_type = envelope["payloadType"]
    payload_profiles = {
        item["payload_type"]: item for item in policy["payload_types"]
    }
    profile = payload_profiles.get(payload_type)
    if profile is None:
        raise VerificationError(
            f"payload type {payload_type!r} is not trusted by this policy"
        )

    verified_signers = verify_signatures(
        envelope,
        policy,
        verification_keys,
        verification_time,
    )

    payload = strict_b64decode(envelope["payload"], "envelope.payload")
    try:
        record = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(
            "verified DSSE payload is not valid UTF-8 JSON"
        ) from exc

    if not isinstance(record, dict):
        raise VerificationError(
            "verified DSSE payload must decode to a JSON object"
        )

    expected_schema_version = profile["record_schema_version"]
    if record.get("record_schema_version") != expected_schema_version:
        raise VerificationError(
            "record_schema_version does not match the trusted payload profile "
            f"({record.get('record_schema_version')!r} != {expected_schema_version!r})"
        )

    record_structure_errors = validate_record_structure(record, record_schema)
    if record_structure_errors:
        raise VerificationError(
            "verified Activity Record fails JSON Schema: "
            + "; ".join(record_structure_errors)
        )

    semantic = record_semantic_errors(record)
    if semantic:
        raise VerificationError(
            "verified Activity Record fails semantic checks: "
            + "; ".join(semantic)
        )

    receipt = derive_receipt(record)
    receipt_errors = validate_derived_receipt(receipt, receipt_schema)
    if receipt_errors:
        raise VerificationError(
            "derived Receipt fails validation: " + "; ".join(receipt_errors)
        )

    expected_record_hash = record_hash(record)
    if (
        receipt["integrity"]["record_hash"] != expected_record_hash
        or receipt["integrity"]["derived_from_record_hash"]
        != expected_record_hash
    ):
        raise VerificationError(
            "derived Receipt does not bind to the verified Activity Record"
        )

    if provided_receipt is not None:
        provided_errors = validate_derived_receipt(
            provided_receipt,
            receipt_schema,
        )
        if provided_errors:
            raise VerificationError(
                "provided Receipt fails validation: "
                + "; ".join(provided_errors)
            )
        if (
            provided_receipt["integrity"]["derived_from_record_hash"]
            != expected_record_hash
        ):
            raise VerificationError(
                "provided Receipt is bound to a different Activity Record"
            )
        if provided_receipt != receipt:
            raise VerificationError(
                "provided Receipt does not equal deterministic derivation "
                "from the verified Activity Record"
            )

    return {
        "valid": True,
        "verification_profile": "DSSE-v1 + candidate-attestation-trust-v0.1",
        "payload_type": payload_type,
        "payload_size_bytes": len(payload),
        "verified_signers": verified_signers,
        "record_id": record["record_id"],
        "record_schema_version": record["record_schema_version"],
        "record_hash": expected_record_hash,
        "receipt_id": receipt["receipt_id"],
        "receipt_binding_verified": True,
        "signature_validity_is_not_authorization": True,
    }


def expect_failure(label: str, callback: Any, contains: str) -> None:
    try:
        callback()
    except VerificationError as exc:
        if contains not in str(exc):
            raise AssertionError(
                f"{label}: expected {contains!r}, got {str(exc)!r}"
            ) from exc
    else:
        raise AssertionError(f"{label}: invalid case was accepted")


def run_self_test() -> int:
    policy_schema = load_json(POLICY_SCHEMA)
    envelope_schema = load_json(ENVELOPE_SCHEMA)
    record_schema = load_json(RECORD_SCHEMA)
    receipt_schema = load_json(RECEIPT_SCHEMA)
    policy = load_json(POLICY_EXAMPLE)
    payload = load_bytes(RECORD_EXAMPLE)
    record = json.loads(payload.decode("utf-8"))

    for schema in (
        policy_schema,
        envelope_schema,
        record_schema,
        receipt_schema,
    ):
        Draft202012Validator.check_schema(schema)

    payload_type = policy["payload_types"][0]["payload_type"]
    signer = policy["trusted_signers"][0]
    verification_uri = signer["verification_material"]["uri"]
    verification_time = parse_time(
        "2026-09-18T12:00:00Z",
        "self_test.verification_time",
    )

    # Private key exists only in process memory for this test.
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    keyring = {verification_uri: public_key}

    envelope = sign_payload(
        payload,
        payload_type,
        private_key,
        signer["key_id"],
    )
    derived_receipt = derive_receipt(record)

    report = verify_envelope(
        envelope,
        policy=policy,
        policy_schema=policy_schema,
        envelope_schema=envelope_schema,
        record_schema=record_schema,
        receipt_schema=receipt_schema,
        verification_keys=keyring,
        verification_time=verification_time,
        provided_receipt=derived_receipt,
    )
    assert report["valid"] is True
    assert report["record_id"] == record["record_id"]
    assert report["record_hash"] == record_hash(record)
    assert report["verified_signers"][0]["role"] == "record_emitter"

    # PAE sanity: exact formula and byte-length behavior.
    assert dsse_pae("x", b"abc") == b"DSSEv1 1 x 3 abc"
    unicode_type = "https://example.invalid/μ"
    encoded_type = unicode_type.encode("utf-8")
    expected = (
        b"DSSEv1 "
        + str(len(encoded_type)).encode("ascii")
        + b" "
        + encoded_type
        + b" 1 x"
    )
    assert dsse_pae(unicode_type, b"x") == expected

    # Unknown keyid must not become identity merely because a signature exists.
    unknown_keyid = copy.deepcopy(envelope)
    unknown_keyid["signatures"][0]["keyid"] = "unknown-key"
    expect_failure(
        "unknown-keyid",
        lambda: verify_envelope(
            unknown_keyid,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "no trusted signer candidate",
    )

    # Same keyid + wrong cryptographic key must fail.
    wrong_private_key = Ed25519PrivateKey.generate()
    wrong_key_envelope = sign_payload(
        payload,
        payload_type,
        wrong_private_key,
        signer["key_id"],
    )
    expect_failure(
        "wrong-key",
        lambda: verify_envelope(
            wrong_key_envelope,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "cryptographic signature is invalid",
    )

    # Exact-byte mutation invalidates the DSSE signature even when parsed JSON
    # content and project-local record hash remain equivalent.
    pretty_equivalent = (
        json.dumps(record, indent=4, ensure_ascii=False).encode("utf-8") + b"\n"
    )
    assert json.loads(pretty_equivalent.decode("utf-8")) == record
    assert record_hash(json.loads(pretty_equivalent.decode("utf-8"))) == record_hash(record)
    byte_mutated = copy.deepcopy(envelope)
    byte_mutated["payload"] = base64.b64encode(pretty_equivalent).decode("ascii")
    expect_failure(
        "exact-byte-mutation",
        lambda: verify_envelope(
            byte_mutated,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "cryptographic signature is invalid",
    )

    # Payload type is authenticated and policy constrained.
    type_mutated = copy.deepcopy(envelope)
    type_mutated["payloadType"] = "https://example.invalid/other-payload"
    expect_failure(
        "payload-type-mutation",
        lambda: verify_envelope(
            type_mutated,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "is not trusted by this policy",
    )

    # Signature bytes cannot be modified.
    signature_mutated = copy.deepcopy(envelope)
    raw_sig = bytearray(
        strict_b64decode(
            signature_mutated["signatures"][0]["sig"],
            "self_test.signature",
        )
    )
    raw_sig[0] ^= 0x01
    signature_mutated["signatures"][0]["sig"] = base64.b64encode(
        bytes(raw_sig)
    ).decode("ascii")
    expect_failure(
        "signature-byte-mutation",
        lambda: verify_envelope(
            signature_mutated,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "cryptographic signature is invalid",
    )

    # Trusted signer metadata cannot rescue the wrong verification key.
    other_public_key = Ed25519PrivateKey.generate().public_key()
    expect_failure(
        "wrong-verification-material",
        lambda: verify_envelope(
            envelope,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys={verification_uri: other_public_key},
            verification_time=verification_time,
        ),
        "cryptographic signature is invalid",
    )

    # Malformed/truncated envelope is rejected before crypto.
    malformed = copy.deepcopy(envelope)
    malformed.pop("signatures")
    expect_failure(
        "malformed-envelope",
        lambda: verify_envelope(
            malformed,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "DSSE envelope structure is invalid",
    )

    # Duplicate signatures from one key must not inflate a threshold.
    duplicate_signature = copy.deepcopy(envelope)
    duplicate_signature["signatures"].append(
        copy.deepcopy(duplicate_signature["signatures"][0])
    )
    expect_failure(
        "duplicate-signature",
        lambda: verify_envelope(
            duplicate_signature,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "duplicates keyid",
    )

    # A correctly signed but structurally invalid record still fails.
    bad_structure_record = copy.deepcopy(record)
    bad_structure_record.pop("record_id")
    bad_structure_payload = (
        json.dumps(bad_structure_record, indent=2).encode("utf-8") + b"\n"
    )
    bad_structure_envelope = sign_payload(
        bad_structure_payload,
        payload_type,
        private_key,
        signer["key_id"],
    )
    expect_failure(
        "signed-invalid-record-schema",
        lambda: verify_envelope(
            bad_structure_envelope,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "fails JSON Schema",
    )

    # A correctly signed but semantically invalid record still fails.
    bad_semantic_record = copy.deepcopy(record)
    bad_semantic_record["events"][-1]["authorization"] = "denied"
    bad_semantic_payload = (
        json.dumps(bad_semantic_record, indent=2).encode("utf-8") + b"\n"
    )
    bad_semantic_envelope = sign_payload(
        bad_semantic_payload,
        payload_type,
        private_key,
        signer["key_id"],
    )
    expect_failure(
        "signed-invalid-record-semantics",
        lambda: verify_envelope(
            bad_semantic_envelope,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
        ),
        "fails semantic checks",
    )

    # A valid signature does not permit a Receipt bound to another record.
    wrong_receipt = copy.deepcopy(derived_receipt)
    wrong_receipt["integrity"]["record_hash"] = "sha256:" + ("0" * 64)
    wrong_receipt["integrity"]["derived_from_record_hash"] = (
        "sha256:" + ("0" * 64)
    )
    expect_failure(
        "receipt-binding-mismatch",
        lambda: verify_envelope(
            envelope,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=verification_time,
            provided_receipt=wrong_receipt,
        ),
        "provided Receipt is bound to a different Activity Record",
    )

    # Signer validity window is evaluated independently of signature math.
    expired_time = parse_time(
        "2027-09-19T00:00:00Z",
        "self_test.expired_time",
    )
    expect_failure(
        "expired-signer",
        lambda: verify_envelope(
            envelope,
            policy=policy,
            policy_schema=policy_schema,
            envelope_schema=envelope_schema,
            record_schema=record_schema,
            receipt_schema=receipt_schema,
            verification_keys=keyring,
            verification_time=expired_time,
        ),
        "signer is not eligible",
    )

    print(
        "DSSE research prototype self-test passed: "
        "1 valid exact-byte signed Activity Record + 11 adversarial cases."
    )
    return 0


def main() -> int:
    try:
        return run_self_test()
    except (
        OSError,
        json.JSONDecodeError,
        SchemaError,
        VerificationError,
        AssertionError,
    ) as exc:
        print(f"ERROR: DSSE research prototype failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
