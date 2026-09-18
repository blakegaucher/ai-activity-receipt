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


def attributes_to_dict(attributes: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if not isinstance(attributes, list):
        return result
    for item in attributes:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        if not isinstance(key, str) or not key:
            continue
        result[key] = decode_any_value(item.get("value"))
    return result


def flatten_spans(otlp: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for resource_span in otlp.get("resourceSpans") or []:
        if not isinstance(resource_span, dict):
            continue
        resource = resource_span.get("resource") or {}
        resource_attrs = attributes_to_dict(resource.get("attributes"))
        for scope_span in resource_span.get("scopeSpans") or []:
            if not isinstance(scope_span, dict):
                continue
            scope = scope_span.get("scope") or {}
            for span in scope_span.get("spans") or []:
                if not isinstance(span, dict):
                    continue
                flattened.append(
                    {
                        "resource_attributes": resource_attrs,
                        "scope": scope,
                        "span": span,
                        "attributes": attributes_to_dict(span.get("attributes")),
                    }
                )
    return flattened


def unix_nano_to_iso(value: Any) -> str:
    try:
        total = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid OTLP Unix-nanosecond timestamp: {value!r}") from exc
    if total < 0:
        raise ValueError("OTLP Unix-nanosecond timestamp must be non-negative")

    seconds, nanos = divmod(total, 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).replace(
        microsecond=nanos // 1000
    )
    if dt.microsecond:
        return dt.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


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


def span_status(span: dict[str, Any], attrs: dict[str, Any]) -> str:
    status = span.get("status") or {}
    code = status.get("code")
    if code == 2 or attrs.get("error.type") not in (None, ""):
        return "failed"
    if not span.get("endTimeUnixNano"):
        return "pending"
    return "completed"


def event_operation(attrs: dict[str, Any], span: dict[str, Any]) -> str:
    op = attrs.get("gen_ai.operation.name")
    if op == "execute_tool" and attrs.get("gen_ai.tool.name"):
        return str(attrs["gen_ai.tool.name"])
    if op:
        return str(op)
    return str(span.get("name") or "unknown")


def event_id(span: dict[str, Any]) -> str:
    span_id = span.get("spanId")
    if not isinstance(span_id, str) or not span_id:
        raise ValueError("every adapted OTLP span must include spanId")
    return f"otel-span:{span_id.lower()}"


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
        str(item["span"].get("traceId")).lower()
        for item in genai_spans
        if item["span"].get("traceId")
    }
    if len(trace_ids) != 1:
        raise ValueError(
            "candidate adapter expects exactly one GenAI trace per record; "
            f"found {sorted(trace_ids)!r}"
        )
    trace_id = next(iter(trace_ids))

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

    principal = context.get("principal")
    if not isinstance(principal, str) or not principal:
        raise ValueError("sidecar context must provide a non-empty principal")

    authority = context.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("sidecar context must provide authority")
    for required in ("scope", "valid_from", "valid_until"):
        if required not in authority:
            raise ValueError(f"sidecar authority is missing {required!r}")

    scope = authority.get("scope")
    if not isinstance(scope, list) or not all(
        isinstance(item, str) and item for item in scope
    ):
        raise ValueError("sidecar authority.scope must be a list of non-empty strings")

    prohibited = authority.get("prohibited") or []
    if not isinstance(prohibited, list) or not all(
        isinstance(item, str) and item for item in prohibited
    ):
        raise ValueError("sidecar authority.prohibited must be a list of strings")

    material_operations = set(context.get("material_operations") or [])
    consequential_operations = set(context.get("consequential_operations") or [])
    material_source_ids = set(context.get("material_source_ids") or [])
    source_roles = context.get("source_roles") or {}
    if not isinstance(source_roles, dict):
        raise ValueError("source_roles must be an object when supplied")

    authorization_by_span_id = context.get("authorization_by_span_id") or {}
    source_refs_by_span_id = context.get("source_refs_by_span_id") or {}
    status_by_span_id = context.get("status_by_span_id") or {}

    data_source_ids: set[str] = set()
    for item in genai_spans:
        source_id = item["attributes"].get("gen_ai.data_source.id")
        if isinstance(source_id, str) and source_id:
            data_source_ids.add(source_id)

    for refs in source_refs_by_span_id.values():
        if not isinstance(refs, list):
            raise ValueError("source_refs_by_span_id values must be lists")
        for ref in refs:
            if not isinstance(ref, str) or not ref:
                raise ValueError("source_refs_by_span_id entries must be non-empty strings")
            data_source_ids.add(ref)

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
        span_id = str(span.get("spanId") or "").lower()
        if not span_id:
            raise ValueError("every adapted GenAI span must include spanId")

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
        if isinstance(data_source_id, str) and data_source_id and data_source_id not in refs:
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
        "agent_id": str(agent_id),
        "version": str(agent_version),
    }
    if provider not in (None, ""):
        system["provider"] = str(provider)
    if model not in (None, ""):
        system["model"] = str(model)

    record: dict[str, Any] = {
        "record_id": str(context.get("record_id") or f"record-otel-{trace_id}"),
        "record_schema_version": "candidate-record-v0.1",
        "trace_id": trace_id,
        "system": system,
        "actors": [
            {"actor_id": principal, "kind": "human", "role": "principal"},
            {"actor_id": str(agent_id), "kind": "agent", "role": "delegate"},
        ],
        "authority": {
            "principal": principal,
            "delegate": str(agent_id),
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
