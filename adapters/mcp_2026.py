#!/usr/bin/env python3
"""Candidate MCP 2026-07-28 capture -> canonical Activity Record adapter.

The adapter treats MCP wire/capture metadata as observed protocol evidence.
Self-reported clientInfo/serverInfo are descriptive only and are never used as
authenticated security identity or authorization evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from derive_receipt import (  # noqa: E402
    derive_receipt,
    record_semantic_errors,
    validate_derived_receipt,
    validate_record_structure,
)


ADAPTER_VERSION = "mcp-2026-v0.1"
SUPPORTED_PROTOCOL_VERSION = "2026-07-28"
DEFAULT_RECORD_SCHEMA = ROOT / "activity-record.schema.json"
DEFAULT_RECEIPT_SCHEMA = ROOT / "activity-receipt.schema.json"
DEFAULT_CAPTURE_FIXTURE = ROOT / "examples" / "mcp-2026-capture.json"
DEFAULT_CONTEXT_FIXTURE = ROOT / "examples" / "mcp-adapter-context.json"
DEFAULT_EXPECTED_RECORD = ROOT / "examples" / "mcp-derived-record.json"
DEFAULT_EXPECTED_RECEIPT = ROOT / "examples" / "mcp-derived-receipt.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def lower_headers(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    if not isinstance(headers, dict):
        raise ValueError("request.headers must be an object when supplied")

    result: dict[str, str] = {}
    for key, value in headers.items():
        if key is None or value is None:
            continue
        normalized = str(key).lower()
        if normalized in result:
            raise ValueError(
                f"duplicate case-insensitive MCP header {normalized!r}"
            )
        result[normalized] = str(value)
    return result


def require_string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return list(value)


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    if not all(isinstance(key, str) and key for key in value):
        raise ValueError(f"{label} keys must be non-empty strings")
    return value


def validate_jsonrpc_envelope(body: dict[str, Any], label: str) -> None:
    if body.get("jsonrpc") != "2.0":
        raise ValueError(f"{label}.jsonrpc must equal '2.0'")


def request_id_text(value: Any) -> str:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return str(value)
    raise ValueError(f"unsupported JSON-RPC request id: {value!r}")


def response_status(response_body: dict[str, Any]) -> str:
    if "error" in response_body and response_body.get("error") is not None:
        return "failed"
    result = response_body.get("result")
    if not isinstance(result, dict):
        return "unknown"
    if result.get("resultType") == "input_required":
        return "pending"
    if result.get("isError") is True:
        return "failed"
    return "completed"


def build_record(capture: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    interactions = capture.get("interactions")
    if not isinstance(interactions, list) or not interactions:
        raise ValueError("capture must contain a non-empty interactions list")

    principal = context.get("principal")
    agent_id = context.get("authenticated_agent_id")
    agent_version = context.get("agent_version")
    generated_at = context.get("generated_at")

    for label, value in (
        ("principal", principal),
        ("authenticated_agent_id", agent_id),
        ("agent_version", agent_version),
        ("generated_at", generated_at),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"sidecar context must provide non-empty {label}")

    authority = context.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("sidecar context must provide authority")
    for required in ("scope", "valid_from", "valid_until"):
        if required not in authority:
            raise ValueError(f"sidecar authority is missing {required!r}")

    scope = require_string_list(authority.get("scope"), "sidecar authority.scope")
    if not scope:
        raise ValueError("sidecar authority.scope must not be empty")

    prohibited = require_string_list(
        authority.get("prohibited"), "sidecar authority.prohibited"
    )

    material_tools = set(
        require_string_list(context.get("material_tools"), "material_tools")
    )
    consequential_tools = set(
        require_string_list(
            context.get("consequential_tools"), "consequential_tools"
        )
    )
    authorization_by_request_id = require_mapping(
        context.get("authorization_by_request_id"),
        "authorization_by_request_id",
    )
    status_by_request_id = require_mapping(
        context.get("status_by_request_id"),
        "status_by_request_id",
    )

    for request_id, info in authorization_by_request_id.items():
        if not isinstance(info, dict):
            raise ValueError(
                "authorization_by_request_id values must be objects; "
                f"request {request_id!r} is invalid"
            )

    events: list[dict[str, Any]] = []
    incidents: list[dict[str, Any]] = []
    seen_request_ids: set[str] = set()

    for interaction in interactions:
        if not isinstance(interaction, dict):
            continue

        request = interaction.get("request") or {}
        response = interaction.get("response") or {}
        if not isinstance(request, dict) or not isinstance(response, dict):
            raise ValueError("request and response must be JSON objects")

        request_body = request.get("body") or {}
        response_body = response.get("body") or {}

        if not isinstance(request_body, dict) or not isinstance(response_body, dict):
            raise ValueError("request.body and response.body must be JSON objects")

        method = request_body.get("method")
        if method != "tools/call":
            continue

        validate_jsonrpc_envelope(request_body, "request.body")
        validate_jsonrpc_envelope(response_body, "response.body")

        headers = lower_headers(request.get("headers"))
        protocol_version = headers.get("mcp-protocol-version")
        if protocol_version != SUPPORTED_PROTOCOL_VERSION:
            raise ValueError(
                f"unsupported or missing MCP-Protocol-Version: {protocol_version!r}"
            )

        if headers.get("mcp-method") not in (None, method):
            raise ValueError("Mcp-Method header does not match JSON-RPC method")

        params = request_body.get("params") or {}
        if not isinstance(params, dict):
            raise ValueError("tools/call params must be an object")

        tool_name = params.get("name")
        if not isinstance(tool_name, str) or not tool_name:
            raise ValueError("tools/call params.name must be a non-empty string")

        header_name = headers.get("mcp-name")
        if header_name not in (None, tool_name):
            raise ValueError("Mcp-Name header does not match tools/call params.name")

        req_id = request_id_text(request_body.get("id"))
        if req_id in seen_request_ids:
            raise ValueError(f"duplicate JSON-RPC request id {req_id!r}")
        seen_request_ids.add(req_id)

        response_id = request_id_text(response_body.get("id"))
        if response_id != req_id:
            raise ValueError(
                f"response id {response_id!r} does not match request id {req_id!r}"
            )

        observed_at = interaction.get("request_observed_at")
        if not isinstance(observed_at, str) or not observed_at:
            raise ValueError(
                f"interaction {req_id!r} must provide request_observed_at"
            )

        status = status_by_request_id.get(req_id) or response_status(response_body)
        if status not in {"completed", "blocked", "failed", "pending", "unknown"}:
            raise ValueError(
                f"unsupported status override for request {req_id!r}: {status!r}"
            )

        material = tool_name in material_tools
        consequential = tool_name in consequential_tools

        auth_info = authorization_by_request_id.get(req_id) or {}
        if not isinstance(auth_info, dict):
            raise ValueError("authorization_by_request_id values must be objects")

        authorization = auth_info.get("authorization")
        if authorization is None:
            authorization = "unknown" if consequential else "not_required"
        if authorization not in {"approved", "denied", "not_required", "unknown"}:
            raise ValueError(
                f"unsupported authorization state for request {req_id!r}: "
                f"{authorization!r}"
            )

        event: dict[str, Any] = {
            "event_id": f"mcp-request:{req_id}",
            "occurred_at": observed_at,
            "actor_id": agent_id,
            "operation": tool_name,
            "status": status,
            "authorization": authorization,
            "consequential": consequential,
            "material": material,
        }
        if auth_info.get("decided_at"):
            event["authorization_decided_at"] = auth_info["decided_at"]

        events.append(event)

        if material and status in {"blocked", "failed"} and (
            consequential or authorization == "denied"
        ):
            incident_type = (
                "blocked_unauthorized_action"
                if status == "blocked" and authorization == "denied"
                else "tool_failure"
            )
            incidents.append(
                {
                    "type": incident_type,
                    "event_id": event["event_id"],
                }
            )

    if not events:
        raise ValueError("no MCP tools/call interactions were found")

    unknown_auth_ids = sorted(set(authorization_by_request_id) - seen_request_ids)
    if unknown_auth_ids:
        raise ValueError(
            "authorization_by_request_id contains unknown request id(s): "
            f"{unknown_auth_ids!r}"
        )

    unknown_status_ids = sorted(set(status_by_request_id) - seen_request_ids)
    if unknown_status_ids:
        raise ValueError(
            "status_by_request_id contains unknown request id(s): "
            f"{unknown_status_ids!r}"
        )

    verification = context.get("verification") or {"state": "pending"}
    if not isinstance(verification, dict):
        raise ValueError("verification must be an object when supplied")

    record_id = context.get("record_id")
    if record_id is None:
        record_id = f"record-mcp-{events[0]['event_id'].replace(':', '-')}"
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("record_id must be a non-empty string when supplied")

    trace_id = context.get("trace_id")
    if trace_id is None:
        trace_id = events[0]["event_id"]
    if not isinstance(trace_id, str) or not trace_id:
        raise ValueError("trace_id must be a non-empty string when supplied")

    return {
        "record_id": record_id,
        "record_schema_version": "candidate-record-v0.1",
        "trace_id": trace_id,
        "system": {
            "agent_id": agent_id,
            "version": agent_version,
        },
        "actors": [
            {"actor_id": principal, "kind": "human", "role": "principal"},
            {"actor_id": agent_id, "kind": "agent", "role": "delegate"},
        ],
        "authority": {
            "principal": principal,
            "delegate": agent_id,
            "scope": list(scope),
            "prohibited": list(prohibited),
            "valid_from": authority["valid_from"],
            "valid_until": authority["valid_until"],
        },
        "sources": [],
        "events": events,
        "verification": verification,
        "incidents": incidents,
        "integrity": {"generated_at": generated_at},
        "notes": (
            f"Adapted by {ADAPTER_VERSION} from MCP {SUPPORTED_PROTOCOL_VERSION} "
            "request/response capture. clientInfo/serverInfo are self-reported "
            "descriptive metadata and are not used as security identity or "
            "authorization evidence."
        ),
    }


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = validate_record_structure(record, schema)
    errors.extend(f"semantic: {item}" for item in record_semantic_errors(record))
    return errors


def run_self_test(
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> int:
    capture = load_json(DEFAULT_CAPTURE_FIXTURE)
    context = load_json(DEFAULT_CONTEXT_FIXTURE)
    expected_record = load_json(DEFAULT_EXPECTED_RECORD)
    expected_receipt = load_json(DEFAULT_EXPECTED_RECEIPT)

    record = build_record(capture, context)
    assert record == expected_record, "MCP adapter record differs from expected fixture"

    errors = validate_record(record, record_schema)
    assert not errors, errors

    receipt = derive_receipt(record)
    assert receipt == expected_receipt, "MCP-derived Receipt differs from expected fixture"

    receipt_errors = validate_derived_receipt(receipt, receipt_schema)
    assert not receipt_errors, receipt_errors

    # Self-reported client identity must not affect authenticated system identity.
    spoofed = json.loads(json.dumps(capture))
    params = spoofed["interactions"][0]["request"]["body"]["params"]
    params["_meta"]["io.modelcontextprotocol/clientInfo"] = {
        "name": "claimed-super-admin",
        "version": "999.0",
    }
    spoofed_record = build_record(spoofed, context)
    assert spoofed_record == record

    # Successful execution without separate authorization remains unknown.
    missing_auth = json.loads(json.dumps(context))
    missing_auth["authorization_by_request_id"] = {}
    missing_auth_record = build_record(capture, missing_auth)
    action = missing_auth_record["events"][0]
    assert action["authorization"] == "unknown"
    missing_auth_receipt = derive_receipt(missing_auth_record)
    assert validate_derived_receipt(missing_auth_receipt, receipt_schema)

    # Header/body routing metadata must agree.
    mismatched = json.loads(json.dumps(capture))
    mismatched["interactions"][0]["request"]["headers"]["Mcp-Name"] = "other_tool"
    try:
        build_record(mismatched, context)
    except ValueError as exc:
        assert "Mcp-Name" in str(exc)
    else:
        raise AssertionError("Mcp-Name mismatch was not rejected")

    # Duplicate case-insensitive routing headers are ambiguous and must fail.
    duplicate_header = json.loads(json.dumps(capture))
    duplicate_header["interactions"][0]["request"]["headers"]["mcp-name"] = "send_email"
    try:
        build_record(duplicate_header, context)
    except ValueError as exc:
        assert "duplicate case-insensitive MCP header" in str(exc)
    else:
        raise AssertionError("duplicate case-insensitive MCP header was not rejected")

    # JSON-RPC version must be explicit and correct on request and response.
    bad_jsonrpc = json.loads(json.dumps(capture))
    bad_jsonrpc["interactions"][0]["request"]["body"]["jsonrpc"] = "1.0"
    try:
        build_record(bad_jsonrpc, context)
    except ValueError as exc:
        assert "jsonrpc must equal '2.0'" in str(exc)
    else:
        raise AssertionError("invalid JSON-RPC version was not rejected")

    # Sidecar collections must have explicit object/list shapes.
    malformed_sidecar = json.loads(json.dumps(context))
    malformed_sidecar["material_tools"] = "send_email"
    try:
        build_record(capture, malformed_sidecar)
    except ValueError as exc:
        assert "material_tools must be a list" in str(exc)
    else:
        raise AssertionError("string material_tools was not rejected")

    # Stale sidecar evidence for an unknown request must fail closed.
    dangling_auth = json.loads(json.dumps(context))
    dangling_auth["authorization_by_request_id"]["no-such-request"] = {
        "authorization": "approved"
    }
    try:
        build_record(capture, dangling_auth)
    except ValueError as exc:
        assert "unknown request id" in str(exc)
    else:
        raise AssertionError("dangling authorization sidecar entry was not rejected")

    # Record/correlation IDs must not be stringified from arbitrary JSON values.
    bad_trace_id = json.loads(json.dumps(context))
    bad_trace_id["trace_id"] = {"unexpected": "object"}
    try:
        build_record(capture, bad_trace_id)
    except ValueError as exc:
        assert "trace_id must be a non-empty string" in str(exc)
    else:
        raise AssertionError("non-string trace_id was not rejected")

    # Arguments and response content are deliberately excluded from the record.
    rendered = json.dumps(record)
    assert "recipient@example.invalid" not in rendered
    assert "synthetic-secret-body" not in rendered
    assert "claimed-client" not in rendered
    assert "mail-server" not in rendered

    print("MCP 2026-07-28 adapter self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Adapt MCP 2026-07-28 tools/call capture into a candidate "
            "Canonical Activity Record."
        )
    )
    parser.add_argument("capture", nargs="?", help="MCP capture JSON file")
    parser.add_argument("--context", help="Sidecar authenticated authority context JSON")
    parser.add_argument("--output", help="Write canonical record JSON to this path")
    parser.add_argument("--receipt-output", help="Also write a derived Receipt JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    record_schema = load_json(DEFAULT_RECORD_SCHEMA)
    receipt_schema = load_json(DEFAULT_RECEIPT_SCHEMA)

    if args.self_test:
        return run_self_test(record_schema, receipt_schema)

    if not args.capture or not args.context:
        parser.error("provide a capture JSON file and --context, or use --self-test")

    try:
        capture = load_json(Path(args.capture))
        context = load_json(Path(args.context))
        if not isinstance(capture, dict) or not isinstance(context, dict):
            raise ValueError("capture and context must both be JSON objects")

        record = build_record(capture, context)
        errors = validate_record(record, record_schema)
        if errors:
            raise ValueError("; ".join(errors))

        if args.receipt_output:
            receipt = derive_receipt(record)
            receipt_errors = validate_derived_receipt(receipt, receipt_schema)
            if receipt_errors:
                raise ValueError("; ".join(receipt_errors))
            Path(args.receipt_output).write_text(
                json.dumps(receipt, indent=2) + "\n",
                encoding="utf-8",
            )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(record, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
