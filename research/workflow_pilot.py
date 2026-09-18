#!/usr/bin/env python3
"""Synthetic heterogeneous workflow derivation pilot.

The pilot combines:
- four direct candidate Canonical Activity Records spanning different workflows;
- the existing OpenTelemetry GenAI adapter fixture;
- the existing MCP 2026-07-28 adapter fixture.

It is intentionally synthetic. Passing this pilot demonstrates derivation and
validation consistency across varied workflow shapes/evidence paths, not
real-world effectiveness or capture fidelity.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DIR = ROOT / "adapters"
for path in (ROOT, ADAPTER_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from derive_receipt import (  # noqa: E402
    derive_receipt,
    record_semantic_errors,
    validate_derived_receipt,
    validate_record_structure,
)
from mcp_2026 import (  # noqa: E402
    DEFAULT_CAPTURE_FIXTURE as MCP_CAPTURE,
    DEFAULT_CONTEXT_FIXTURE as MCP_CONTEXT,
    build_record as build_mcp_record,
)
from otel_genai import (  # noqa: E402
    DEFAULT_CONTEXT_FIXTURE as OTEL_CONTEXT,
    DEFAULT_OTLP_FIXTURE as OTEL_TRACE,
    build_record as build_otel_record,
)


RECORD_SCHEMA = ROOT / "activity-record.schema.json"
RECEIPT_SCHEMA = ROOT / "activity-receipt.schema.json"
MANIFEST = ROOT / "research" / "workflow-pilot" / "manifest.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_and_derive(
    record: dict[str, Any],
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> dict[str, Any]:
    structural = validate_record_structure(record, record_schema)
    if structural:
        raise AssertionError(f"record structure invalid: {structural!r}")

    semantic = record_semantic_errors(record)
    if semantic:
        raise AssertionError(f"record semantics invalid: {semantic!r}")

    first = derive_receipt(record)
    second = derive_receipt(record)
    if first != second:
        raise AssertionError("Receipt derivation is not deterministic")

    receipt_errors = validate_derived_receipt(first, receipt_schema)
    if receipt_errors:
        raise AssertionError(f"derived Receipt invalid: {receipt_errors!r}")

    return first


def summarize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_id": receipt["receipt_id"],
        "trace_id": receipt["trace_id"],
        "operations": [
            action["operation"] for action in receipt["material_actions"]
        ],
        "statuses": [
            action["status"] for action in receipt["material_actions"]
        ],
        "authorizations": [
            action["authorization"] for action in receipt["material_actions"]
        ],
        "material_sources": [
            source["source_id"] for source in receipt["material_sources"]
        ],
        "incidents": [
            incident["type"] for incident in receipt["incidents"]
        ],
        "verification": receipt["verification"]["state"],
        "record_hash": receipt["integrity"]["record_hash"],
    }


def run_direct_cases(
    manifest: dict[str, Any],
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for entry in manifest["direct_records"]:
        path = ROOT / entry["path"]
        record = load_json(path)
        if not isinstance(record, dict):
            raise AssertionError(f"{path}: record must be an object")

        receipt = validate_and_derive(record, record_schema, receipt_schema)

        operations = [
            action["operation"] for action in receipt["material_actions"]
        ]
        source_ids = [
            source["source_id"] for source in receipt["material_sources"]
        ]
        incident_types = [
            incident["type"] for incident in receipt["incidents"]
        ]
        receipt_event_ids = {
            action["event_id"] for action in receipt["material_actions"]
        }

        assert operations == entry["expected_operations"], (
            path,
            operations,
            entry["expected_operations"],
        )
        assert source_ids == entry["expected_material_sources"], (
            path,
            source_ids,
            entry["expected_material_sources"],
        )
        assert incident_types == entry["expected_incidents"], (
            path,
            incident_types,
            entry["expected_incidents"],
        )
        assert receipt["verification"]["state"] == entry["expected_verification"]

        for excluded in entry.get("excluded_event_ids") or []:
            assert excluded not in receipt_event_ids, (
                f"{path}: non-material event {excluded!r} leaked into Receipt"
            )

        results.append(
            {
                "kind": "direct_canonical_record",
                "source": entry["path"],
                **summarize_receipt(receipt),
            }
        )

    return results


def run_adapter_cases(
    record_schema: dict[str, Any],
    receipt_schema: dict[str, Any],
) -> list[dict[str, Any]]:
    otel_record = build_otel_record(
        load_json(OTEL_TRACE),
        load_json(OTEL_CONTEXT),
    )
    mcp_record = build_mcp_record(
        load_json(MCP_CAPTURE),
        load_json(MCP_CONTEXT),
    )

    otel_receipt = validate_and_derive(
        otel_record, record_schema, receipt_schema
    )
    mcp_receipt = validate_and_derive(
        mcp_record, record_schema, receipt_schema
    )

    assert any(
        action["operation"] == "send_email"
        for action in otel_receipt["material_actions"]
    )
    assert any(
        action["operation"] == "send_email"
        for action in mcp_receipt["material_actions"]
    )

    return [
        {
            "kind": "opentelemetry_genai_adapter",
            "source": str(OTEL_TRACE.relative_to(ROOT)),
            **summarize_receipt(otel_receipt),
        },
        {
            "kind": "mcp_2026_adapter",
            "source": str(MCP_CAPTURE.relative_to(ROOT)),
            **summarize_receipt(mcp_receipt),
        },
    ]


def run_pilot() -> dict[str, Any]:
    record_schema = load_json(RECORD_SCHEMA)
    receipt_schema = load_json(RECEIPT_SCHEMA)
    manifest = load_json(MANIFEST)

    if not isinstance(manifest, dict):
        raise AssertionError("workflow pilot manifest must be an object")

    direct = run_direct_cases(manifest, record_schema, receipt_schema)
    adapters = run_adapter_cases(record_schema, receipt_schema)
    cases = direct + adapters

    assert len(direct) == 4
    assert len(adapters) == 2
    assert len(cases) == 6

    # Ensure the direct pilot actually spans the workflow states it is meant
    # to exercise rather than accidentally collapsing into one happy path.
    all_statuses = {
        status
        for case in cases
        for status in case["statuses"]
    }
    all_authorizations = {
        authorization
        for case in cases
        for authorization in case["authorizations"]
    }
    all_incidents = {
        incident
        for case in cases
        for incident in case["incidents"]
    }
    verification_states = {case["verification"] for case in cases}

    assert {"completed", "failed", "blocked", "pending"}.issubset(all_statuses)
    assert {"approved", "denied", "unknown", "not_required"}.issubset(
        all_authorizations
    )
    assert {"tool_failure", "blocked_unauthorized_action"}.issubset(
        all_incidents
    )
    assert {"confirmed", "failed", "pending", "uncertain"}.issubset(
        verification_states
    )

    return {
        "pilot_version": manifest["pilot_version"],
        "status": "synthetic_development_pilot",
        "n_cases": len(cases),
        "evidence_paths": [
            "direct_canonical_record",
            "opentelemetry_genai_adapter",
            "mcp_2026_adapter",
        ],
        "coverage": {
            "statuses": sorted(all_statuses),
            "authorizations": sorted(all_authorizations),
            "incident_types": sorted(all_incidents),
            "verification_states": sorted(verification_states),
        },
        "cases": cases,
        "evidence_boundary": (
            "Synthetic workflow diversity and deterministic derivation only; "
            "not real-world workflow fidelity or human audit benefit."
        ),
    }


def main() -> int:
    try:
        result = run_pilot()
    except (
        OSError,
        json.JSONDecodeError,
        AssertionError,
        ValueError,
    ) as exc:
        print(f"ERROR: workflow pilot failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    print(
        "Heterogeneous workflow derivation pilot passed: "
        f"{result['n_cases']} synthetic cases."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
