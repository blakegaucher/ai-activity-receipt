#!/usr/bin/env python3
"""Candidate OpenTelemetry GenAI -> canonical Activity Record adapter.

The adapter consumes OTLP/JSON trace data plus a separate sidecar context file.
Telemetry is treated as observed execution evidence, not as proof of authority.
Authorization, materiality, and authority-window information must come from the
sidecar context rather than being inferred from a successful span.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
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


ADAPTER_VERSION = "otel-genai-v0.1"
DEFAULT_RECORD_SCHEMA = ROOT / "activity-record.schema.json"
DEFAULT_RECEIPT_SCHEMA = ROOT / "activity-receipt.schema.json"
DEFAULT_OTLP_FIXTURE = ROOT / "examples" / "otel-genai-traces.json"
DEFAULT_CONTEXT_FIXTURE = ROOT / "examples" / "otel-adapter-context.json"
DEFAULT_EXPECTED_RECORD = ROOT / "examples" / "otel-derived-record.json"
DEFAULT_EXPECTED_RECEIPT = ROOT / "examples" / "otel-derived-receipt.json"

TRACE_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")
SPAN_ID_RE = re.compile(r"^[0-9a-fA-F]{16}$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def decode_any_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return None
    if "stringValue" in value:
        return value["stringValue"]
    if "boolValue" in value:
        return value["boolValue"]
    if "intValue" in value:
        raw = value["intValue"]
        try:
            return int(raw)
        except (TypeError, ValueError):
            return raw
    if "doubleValue" in value:
        return value["doubleValue"]
    if "bytesValue" in value:
        return value["bytesValue"]
    if "arrayValue" in value:
        values = (value["arrayValue"] or {}).get("values") or []
        return [decode_any_value(item) for item in values]
    if "kvlistValue" in value:
        items = (value["kvlistValue"] or {}).get("values") or []
        return {
            item.get("key"): decode_any_value(item.get("value"))
            for item in items
            if isinstance(item, dict) and item.get("key")
        }
    return None


def attributes_to_dict(attributes: Any, *, label: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if attributes is None:
        return result
    if not isinstance(attributes, list):
        raise ValueError(f"{label} must be a list when supplied")

    for index, item in enumerate(attributes):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{index}] must be an object")
        key = item.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError(f"{label}[{index}].key must be a non-empty string")
        if key in result:
            raise ValueError(f"{label} contains duplicate attribute key {key!r}")
        result[key] = decode_any_value(item.get("value"))
    return result


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{label} entries must be objects")
    return list(value)


def flatten_spans(otlp: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for resource_index, resource_span in enumerate(
        _object_list(otlp.get("resourceSpans"), "resourceSpans")
    ):
        resource = resource_span.get("resource") or {}
        if not isinstance(resource, dict):
            raise ValueError(
                f"resourceSpans[{resource_index}].resource must be an object"
            )
        resource_attrs = attributes_to_dict(
            resource.get("attributes"),
            label=f"resourceSpans[{resource_index}].resource.attributes",
        )
        for scope_index, scope_span in enumerate(
            _object_list(
                resource_span.get("scopeSpans"),
                f"resourceSpans[{resource_index}].scopeSpans",
            )
        ):
            scope = scope_span.get("scope") or {}
            if not isinstance(scope, dict):
                raise ValueError(
                    "scope must be an object at "
                    f"resourceSpans[{resource_index}].scopeSpans[{scope_index}]"
                )
            for span_index, span in enumerate(
                _object_list(
                    scope_span.get("spans"),
                    "resourceSpans"
                    f"[{resource_index}].scopeSpans[{scope_index}].spans",
                )
            ):
                flattened.append(
                    {
                        "resource_attributes": resource_attrs,
                        "scope": scope,
                        "span": span,
                        "attributes": attributes_to_dict(
                            span.get("attributes"),
                            label=(
                                "resourceSpans"
                                f"[{resource_index}].scopeSpans[{scope_index}]"
                                f".spans[{span_index}].attributes"
                            ),
                        ),
                    }
                )
    return flattened


def unix_nano_int(value: Any) -> int:
    try:
        total = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid OTLP Unix-nanosecond timestamp: {value!r}") from exc
    if total < 0:
        raise ValueError("OTLP Unix-nanosecond timestamp must be non-negative")
    return total


def unix_nano_to_iso(value: Any) -> str:
    total = unix_nano_int(value)

    seconds, nanos = divmod(total, 1_000_000_000)
    try:
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError(
            f"OTLP Unix-nanosecond timestamp is outside supported range: {value!r}"
        ) from exc
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    if nanos:
        # OTLP timestamps are Unix nanoseconds. Preserve all significant
        # fractional digits rather than truncating to Python datetime's
        # microsecond precision.
        fraction = f"{nanos:09d}".rstrip("0")
        return f"{base}.{fraction}Z"
    return f"{base}Z"


def normalize_trace_id(value: Any) -> str:
    if not isinstance(value, str) or not TRACE_ID_RE.fullmatch(value):
        raise ValueError(
            "OTLP traceId must be a 32-hex-character string"
        )
    normalized = value.lower()
    if normalized == "0" * 32:
        raise ValueError("OTLP traceId must contain at least one non-zero byte")
    return normalized


def normalize_span_id(value: Any) -> str:
    if not isinstance(value, str) or not SPAN_ID_RE.fullmatch(value):
        raise ValueError(
            "OTLP spanId must be a 16-hex-character string"
        )
    normalized = value.lower()
    if normalized == "0" * 16:
        raise ValueError("OTLP spanId must contain at least one non-zero byte")
    return normalized


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


def normalize_span_key_mapping(value: Any, label: str) -> dict[str, Any]:
    raw = require_mapping(value, label)
    normalized: dict[str, Any] = {}
    for key, item in raw.items():
        span_id = normalize_span_id(key)
        if span_id in normalized:
            raise ValueError(
                f"{label} contains duplicate span id after normalization: {span_id!r}"
            )
        normalized[span_id] = item
    return normalized


def one_value(
    values: list[Any],
    *,
    label: str,
    explicit: Any = None,
    required: bool = False,
) -> Any:
    if explicit not in (None, ""):
        return explicit

    present = [value for value in values if value not in (None, "")]
    distinct: list[Any] = []
    for value in present:
        if value not in distinct:
            distinct.append(value)

    if len(distinct) > 1:
        raise ValueError(
            f"multiple {label} values found in telemetry; provide an explicit "
            f"sidecar value: {distinct!r}"
        )
    if distinct:
        return distinct[0]
    if required:
        raise ValueError(
            f"no {label} was found in telemetry and no explicit sidecar value was supplied"
        )
    return None


def validate_span_time_order(span: dict[str, Any]) -> None:
    start = unix_nano_int(span.get("startTimeUnixNano"))
    end_raw = span.get("endTimeUnixNano")
    if end_raw in (None, ""):
        return
    end = unix_nano_int(end_raw)
    if end < start:
        raise ValueError("OTLP span endTimeUnixNano must not precede startTimeUnixNano")


def span_status(span: dict[str, Any], attrs: dict[str, Any]) -> str:
    status = span.get("status") or {}
    if not isinstance(status, dict):
        raise ValueError("OTLP span.status must be an object when supplied")
    code = status.get("code")
    if code == 2 or attrs.get("error.type") not in (None, ""):
        return "failed"
    if not span.get("endTimeUnixNano"):
        return "pending"
    return "completed"


def event_operation(attrs: dict[str, Any], span: dict[str, Any]) -> str:
    op = attrs.get("gen_ai.operation.name")
    if not isinstance(op, str) or not op:
        raise ValueError("gen_ai.operation.name must be a non-empty string")
    if op == "execute_tool":
        tool_name = attrs.get("gen_ai.tool.name")
        if not isinstance(tool_name, str) or not tool_name:
            raise ValueError(
                "execute_tool spans must provide non-empty gen_ai.tool.name"
            )
        return tool_name
    return op


def event_id(span: dict[str, Any]) -> str:
    return f"otel-span:{normalize_span_id(span.get('spanId'))}"


def build_record(otlp: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    spans = flatten_spans(otlp)
    genai_spans = [
        item
        for item in spans
        if item["attributes"].get("gen_ai.operation.name")
    ]
    if not genai_spans:
        raise ValueError("no spans with gen_ai.operation.name were found")

    trace_ids = {
        normalize_trace_id(item["span"].get("traceId"))
        for item in genai_spans
    }
    if len(trace_ids) != 1:
        raise ValueError(
            "candidate adapter expects exactly one GenAI trace per record; "
            f"found {sorted(trace_ids)!r}"
        )
    trace_id = next(iter(trace_ids))

    span_ids = [normalize_span_id(item["span"].get("spanId")) for item in genai_spans]
    if len(set(span_ids)) != len(span_ids):
        raise ValueError("candidate adapter requires unique spanId values per trace")

    agent_id = one_value(
        [item["attributes"].get("gen_ai.agent.id") for item in genai_spans],
        label="gen_ai.agent.id",
        explicit=context.get("agent_id"),
        required=True,
    )
    agent_version = one_value(
        [item["attributes"].get("gen_ai.agent.version") for item in genai_spans]
        + [
            item["resource_attributes"].get("service.version")
            for item in genai_spans
        ],
        label="agent/service version",
        explicit=context.get("agent_version"),
        required=True,
    )
    provider = one_value(
        [item["attributes"].get("gen_ai.provider.name") for item in genai_spans],
        label="gen_ai.provider.name",
        explicit=context.get("provider"),
    )
    model = one_value(
        [item["attributes"].get("gen_ai.request.model") for item in genai_spans],
        label="gen_ai.request.model",
        explicit=context.get("model"),
    )

    for label, value in (
        ("agent_id", agent_id),
        ("agent_version", agent_version),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} must resolve to a non-empty string")
    for label, value in (("provider", provider), ("model", model)):
        if value is not None and (not isinstance(value, str) or not value):
            raise ValueError(f"{label} must resolve to a non-empty string when present")

    principal = context.get("principal")
    if not isinstance(principal, str) or not principal:
        raise ValueError("sidecar context must provide a non-empty principal")

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

    material_operations = set(
        require_string_list(
            context.get("material_operations"), "material_operations"
        )
    )
    consequential_operations = set(
        require_string_list(
            context.get("consequential_operations"),
            "consequential_operations",
        )
    )
    material_source_ids = set(
        require_string_list(
            context.get("material_source_ids"), "material_source_ids"
        )
    )

    source_roles = require_mapping(context.get("source_roles"), "source_roles")
    for source_id, role in source_roles.items():
        if not isinstance(role, str) or not role:
            raise ValueError(
                f"source_roles[{source_id!r}] must be a non-empty string"
            )

    authorization_by_span_id = normalize_span_key_mapping(
        context.get("authorization_by_span_id"),
        "authorization_by_span_id",
    )
    source_refs_by_span_id = normalize_span_key_mapping(
        context.get("source_refs_by_span_id"),
        "source_refs_by_span_id",
    )
    status_by_span_id = normalize_span_key_mapping(
        context.get("status_by_span_id"),
        "status_by_span_id",
    )

    for span_id, info in authorization_by_span_id.items():
        if not isinstance(info, dict):
            raise ValueError(
                "authorization_by_span_id values must be objects; "
                f"span {span_id!r} is invalid"
            )

    for span_id, refs in source_refs_by_span_id.items():
        if not isinstance(refs, list) or not all(
            isinstance(ref, str) and ref for ref in refs
        ):
            raise ValueError(
                "source_refs_by_span_id values must be lists of non-empty "
                f"strings; span {span_id!r} is invalid"
            )

    data_source_ids: set[str] = set()
    for item in genai_spans:
        source_id = item["attributes"].get("gen_ai.data_source.id")
        if source_id is not None:
            if not isinstance(source_id, str) or not source_id:
                raise ValueError(
                    "gen_ai.data_source.id must be a non-empty string when present"
                )
            data_source_ids.add(source_id)

    for refs in source_refs_by_span_id.values():
        data_source_ids.update(refs)

    observed_span_ids = set(span_ids)
    for label, mapping in (
        ("authorization_by_span_id", authorization_by_span_id),
        ("source_refs_by_span_id", source_refs_by_span_id),
        ("status_by_span_id", status_by_span_id),
    ):
        unknown = sorted(set(mapping) - observed_span_ids)
        if unknown:
            raise ValueError(
                f"{label} contains unknown span id(s): {unknown!r}"
            )

    unknown_material_sources = sorted(material_source_ids - data_source_ids)
    if unknown_material_sources:
        raise ValueError(
            "material_source_ids contains source id(s) not present in telemetry "
            f"or source_refs_by_span_id: {unknown_material_sources!r}"
        )

    unknown_source_roles = sorted(set(source_roles) - data_source_ids)
    if unknown_source_roles:
        raise ValueError(
            "source_roles contains source id(s) not present in telemetry or "
            f"source_refs_by_span_id: {unknown_source_roles!r}"
        )

    sources = [
        {
            "source_id": source_id,
            "role": str(source_roles.get(source_id) or "telemetry_data_source"),
            "material": source_id in material_source_ids,
        }
        for source_id in sorted(data_source_ids)
    ]

    events: list[dict[str, Any]] = []
    incidents: list[dict[str, Any]] = []

    for item in genai_spans:
        span = item["span"]
        attrs = item["attributes"]
        span_id = normalize_span_id(span.get("spanId"))
        validate_span_time_order(span)

        operation = event_operation(attrs, span)
        status = status_by_span_id.get(span_id) or span_status(span, attrs)
        if status not in {"completed", "blocked", "failed", "pending", "unknown"}:
            raise ValueError(f"unsupported status override for span {span_id!r}: {status!r}")

        material = operation in material_operations
        consequential = operation in consequential_operations

        auth_info = authorization_by_span_id.get(span_id) or {}
        if not isinstance(auth_info, dict):
            raise ValueError("authorization_by_span_id values must be objects")

        authorization = auth_info.get("authorization")
        if authorization is None:
            authorization = "unknown" if consequential else "not_required"
        if authorization not in {"approved", "denied", "not_required", "unknown"}:
            raise ValueError(
                f"unsupported authorization state for span {span_id!r}: "
                f"{authorization!r}"
            )

        refs = list(source_refs_by_span_id.get(span_id) or [])
        data_source_id = attrs.get("gen_ai.data_source.id")
        if (
            isinstance(data_source_id, str)
            and data_source_id
            and data_source_id not in refs
        ):
            refs.append(data_source_id)

        event: dict[str, Any] = {
            "event_id": event_id(span),
            "occurred_at": unix_nano_to_iso(span.get("startTimeUnixNano")),
            "actor_id": str(agent_id),
            "operation": operation,
            "status": status,
            "authorization": authorization,
            "consequential": consequential,
            "material": material,
        }
        if refs:
            event["source_refs"] = sorted(set(refs))
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

    verification = context.get("verification") or {"state": "pending"}
    if not isinstance(verification, dict):
        raise ValueError("verification must be an object when supplied")

    generated_at = context.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at:
        raise ValueError(
            "sidecar context must provide generated_at; the adapter does not "
            "invent a record-generation timestamp"
        )

    system: dict[str, Any] = {
        "agent_id": agent_id,
        "version": agent_version,
    }
    if provider not in (None, ""):
        system["provider"] = provider
    if model not in (None, ""):
        system["model"] = model

    record_id = context.get("record_id")
    if record_id is None:
        record_id = f"record-otel-{trace_id}"
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("record_id must be a non-empty string when supplied")

    record: dict[str, Any] = {
        "record_id": record_id,
        "record_schema_version": "candidate-record-v0.1",
        "trace_id": trace_id,
        "system": system,
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
        "sources": sources,
        "events": events,
        "verification": verification,
        "incidents": incidents,
        "integrity": {"generated_at": generated_at},
        "notes": (
            f"Adapted by {ADAPTER_VERSION} from OTLP/JSON GenAI telemetry. "
            "Authority and materiality are sidecar evidence; telemetry success "
            "is not treated as authorization."
        ),
    }

    return record


def validate_record(record: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = validate_record_structure(record, schema)
    errors.extend(f"semantic: {item}" for item in record_semantic_errors(record))
    return errors


def run_self_test(
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> int:
    otlp = load_json(DEFAULT_OTLP_FIXTURE)
    context = load_json(DEFAULT_CONTEXT_FIXTURE)
    expected_record = load_json(DEFAULT_EXPECTED_RECORD)
    expected_receipt = load_json(DEFAULT_EXPECTED_RECEIPT)

    record = build_record(otlp, context)
    assert record == expected_record, "OTLP adapter record differs from expected fixture"

    errors = validate_record(record, record_schema)
    assert not errors, errors

    receipt = derive_receipt(record)
    assert receipt == expected_receipt, "OTLP-derived Receipt differs from expected fixture"

    receipt_errors = validate_derived_receipt(receipt, receipt_schema)
    assert not receipt_errors, receipt_errors

    # Authorization must never be inferred from a successful span.
    missing_auth = json.loads(json.dumps(context))
    missing_auth["authorization_by_span_id"] = {}
    missing_auth_record = build_record(otlp, missing_auth)
    consequential = [
        event
        for event in missing_auth_record["events"]
        if event["consequential"] is True
    ]
    assert consequential and consequential[0]["authorization"] == "unknown"
    missing_auth_receipt = derive_receipt(missing_auth_record)
    assert validate_derived_receipt(missing_auth_receipt, receipt_schema)

    # Preserve OTLP nanosecond precision rather than truncating to microseconds.
    assert unix_nano_to_iso("1789711500123456789") == (
        "2026-09-18T06:05:00.123456789Z"
    )
    assert unix_nano_to_iso("1789711500123000000") == (
        "2026-09-18T06:05:00.123Z"
    )

    # Trace/span identifiers must have the OpenTelemetry widths and be non-zero.
    zero_trace = json.loads(json.dumps(otlp))
    zero_trace["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["traceId"] = "0" * 32
    try:
        build_record(zero_trace, context)
    except ValueError as exc:
        assert "traceId" in str(exc)
    else:
        raise AssertionError("all-zero traceId was not rejected")

    zero_span = json.loads(json.dumps(otlp))
    zero_span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["spanId"] = "0" * 16
    try:
        build_record(zero_span, context)
    except ValueError as exc:
        assert "spanId" in str(exc)
    else:
        raise AssertionError("all-zero spanId was not rejected")

    short_span = json.loads(json.dumps(otlp))
    short_span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["spanId"] = "abcd"
    try:
        build_record(short_span, context)
    except ValueError as exc:
        assert "16-hex-character" in str(exc)
    else:
        raise AssertionError("short spanId was not rejected")

    # Sidecar collections must have explicit list/object shapes.
    malformed_sidecar = json.loads(json.dumps(context))
    malformed_sidecar["material_operations"] = "send_email"
    try:
        build_record(otlp, malformed_sidecar)
    except ValueError as exc:
        assert "material_operations must be a list" in str(exc)
    else:
        raise AssertionError("string material_operations was not rejected")

    # Stale sidecar evidence for an unknown span must fail closed.
    dangling_auth = json.loads(json.dumps(context))
    dangling_auth["authorization_by_span_id"]["3333333333333333"] = {
        "authorization": "approved"
    }
    try:
        build_record(otlp, dangling_auth)
    except ValueError as exc:
        assert "unknown span id" in str(exc)
    else:
        raise AssertionError("dangling authorization sidecar entry was not rejected")

    # Duplicate semantic-convention attributes are ambiguous.
    duplicate_attr = json.loads(json.dumps(otlp))
    duplicate_attr["resourceSpans"][0]["scopeSpans"][0]["spans"][0][
        "attributes"
    ].append(
        {
            "key": "gen_ai.agent.id",
            "value": {"stringValue": "other-agent"},
        }
    )
    try:
        build_record(duplicate_attr, context)
    except ValueError as exc:
        assert "duplicate attribute key" in str(exc)
    else:
        raise AssertionError("duplicate OTLP attribute key was not rejected")

    # Span timing must be internally coherent.
    inverted_time = json.loads(json.dumps(otlp))
    inverted_time["resourceSpans"][0]["scopeSpans"][0]["spans"][1][
        "endTimeUnixNano"
    ] = "1789711499000000000"
    try:
        build_record(inverted_time, context)
    except ValueError as exc:
        assert "must not precede startTimeUnixNano" in str(exc)
    else:
        raise AssertionError("inverted OTLP span time was not rejected")

    # Duplicate span IDs would collapse canonical event identity.
    duplicate_span = json.loads(json.dumps(otlp))
    duplicate_span["resourceSpans"][0]["scopeSpans"][0]["spans"][1]["spanId"] = (
        duplicate_span["resourceSpans"][0]["scopeSpans"][0]["spans"][0]["spanId"]
    )
    try:
        build_record(duplicate_span, context)
    except ValueError as exc:
        assert "unique spanId" in str(exc)
    else:
        raise AssertionError("duplicate spanId was not rejected")

    # Unsupported timestamp magnitudes must fail as validation errors, not crash.
    try:
        unix_nano_to_iso("999999999999999999999999999999999999")
    except ValueError as exc:
        assert "outside supported range" in str(exc)
    else:
        raise AssertionError("out-of-range OTLP timestamp was not rejected")

    # Sensitive tool arguments/results are intentionally not copied.
    rendered = json.dumps(record)
    assert "gen_ai.tool.call.arguments" not in rendered
    assert "gen_ai.tool.call.result" not in rendered
    assert "recipient@example.invalid" not in rendered

    print("OpenTelemetry GenAI adapter self-test passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Adapt one OTLP/JSON GenAI trace into a candidate Activity Record."
    )
    parser.add_argument("otlp", nargs="?", help="OTLP/JSON traces file")
    parser.add_argument("--context", help="Sidecar authority/materiality context JSON")
    parser.add_argument("--output", help="Write canonical record JSON to this path")
    parser.add_argument("--receipt-output", help="Also write a derived Receipt JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    record_schema = load_json(DEFAULT_RECORD_SCHEMA)
    receipt_schema = load_json(DEFAULT_RECEIPT_SCHEMA)

    if args.self_test:
        return run_self_test(record_schema, receipt_schema)

    if not args.otlp or not args.context:
        parser.error("provide an OTLP JSON file and --context, or use --self-test")

    try:
        otlp = load_json(Path(args.otlp))
        context = load_json(Path(args.context))
        if not isinstance(otlp, dict) or not isinstance(context, dict):
            raise ValueError("OTLP input and context must both be JSON objects")
        record = build_record(otlp, context)
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
