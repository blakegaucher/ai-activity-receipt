#!/usr/bin/env python3
"""Synthetic cross-adapter normalization parity check.

This test asks a narrow interoperability question: when OpenTelemetry GenAI and
MCP captures represent the same consequential tool operation under aligned
identity/authority context, do they normalize to the same governance/action
projection in the derived Activity Receipt?

Protocol-specific provenance, trace IDs, event IDs, and timestamps are
intentionally preserved and therefore are not expected to be byte-identical.
"""

from __future__ import annotations

import copy
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
)
from mcp_2026 import (  # noqa: E402
    DEFAULT_CAPTURE_FIXTURE,
    DEFAULT_CONTEXT_FIXTURE as DEFAULT_MCP_CONTEXT_FIXTURE,
    build_record as build_mcp_record,
)
from otel_genai import (  # noqa: E402
    DEFAULT_CONTEXT_FIXTURE as DEFAULT_OTEL_CONTEXT_FIXTURE,
    DEFAULT_OTLP_FIXTURE,
    build_record as build_otel_record,
)


DEFAULT_RECEIPT_SCHEMA = ROOT / "activity-receipt.schema.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def governance_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    """Return only fields expected to be substrate-independent in this test."""
    return {
        "system": {
            "agent_id": receipt["system"]["agent_id"],
            "version": receipt["system"]["version"],
        },
        "authority": {
            "principal": receipt["authority"]["principal"],
            "delegate": receipt["authority"]["delegate"],
            "scope": list(receipt["authority"]["scope"]),
            "prohibited": list(receipt["authority"]["prohibited"]),
        },
        "material_actions": [
            {
                "operation": action["operation"],
                "status": action["status"],
                "authorization": action["authorization"],
                "consequential": action["consequential"],
            }
            for action in receipt["material_actions"]
        ],
        "verification_state": receipt["verification"]["state"],
    }


def aligned_contexts() -> tuple[dict[str, Any], dict[str, Any]]:
    otel_context = copy.deepcopy(load_json(DEFAULT_OTEL_CONTEXT_FIXTURE))
    mcp_context = copy.deepcopy(load_json(DEFAULT_MCP_CONTEXT_FIXTURE))

    common_authority = {
        "scope": ["send_email"],
        "prohibited": [],
        "valid_from": "2026-09-18T05:55:00Z",
        "valid_until": "2026-09-18T07:30:00Z",
    }

    otel_context.update(
        {
            "record_id": "record-parity-otel",
            "principal": "user-parity",
            "agent_id": "agent-parity",
            "agent_version": "1.0.0",
            "authority": copy.deepcopy(common_authority),
            "verification": {"state": "pending"},
        }
    )

    mcp_context.update(
        {
            "record_id": "record-parity-mcp",
            "trace_id": "mcp-parity-trace",
            "principal": "user-parity",
            "authenticated_agent_id": "agent-parity",
            "agent_version": "1.0.0",
            "authority": copy.deepcopy(common_authority),
            "verification": {"state": "pending"},
        }
    )

    return otel_context, mcp_context


def run_self_test() -> int:
    otlp = load_json(DEFAULT_OTLP_FIXTURE)
    mcp_capture = load_json(DEFAULT_CAPTURE_FIXTURE)
    receipt_schema = load_json(DEFAULT_RECEIPT_SCHEMA)
    otel_context, mcp_context = aligned_contexts()

    otel_record = build_otel_record(otlp, otel_context)
    mcp_record = build_mcp_record(mcp_capture, mcp_context)

    otel_receipt = derive_receipt(otel_record)
    mcp_receipt = derive_receipt(mcp_record)

    assert not validate_derived_receipt(otel_receipt, receipt_schema)
    assert not validate_derived_receipt(mcp_receipt, receipt_schema)

    otel_projection = governance_projection(otel_receipt)
    mcp_projection = governance_projection(mcp_receipt)

    assert otel_projection == mcp_projection
    assert otel_projection["material_actions"] == [
        {
            "operation": "send_email",
            "status": "completed",
            "authorization": "approved",
            "consequential": True,
        }
    ]

    # The test is deliberately not claiming full-record equivalence. OTEL
    # carries a material retrieval source in its fixture; the MCP fixture does
    # not. Protocol/run identifiers and timestamps also remain substrate-specific.
    assert otel_receipt["material_sources"] != mcp_receipt["material_sources"]
    assert otel_receipt["trace_id"] != mcp_receipt["trace_id"]
    assert (
        otel_receipt["material_actions"][0]["occurred_at"]
        != mcp_receipt["material_actions"][0]["occurred_at"]
    )

    # Authorization parity must fail when one substrate loses its separate
    # authorization evidence. Successful MCP execution alone remains unknown.
    missing_auth_context = copy.deepcopy(mcp_context)
    missing_auth_context["authorization_by_request_id"] = {}
    missing_auth_record = build_mcp_record(mcp_capture, missing_auth_context)
    assert missing_auth_record["events"][0]["authorization"] == "unknown"

    semantic_errors = record_semantic_errors(missing_auth_record)
    assert any(
        "does not have approved authorization" in error
        for error in semantic_errors
    )

    try:
        derive_receipt(missing_auth_record)
    except ValueError as exc:
        assert "does not have approved authorization" in str(exc)
    else:
        raise AssertionError(
            "missing authorization evidence was not rejected before Receipt derivation"
        )

    print(
        "Cross-adapter normalization parity self-test passed: "
        "aligned OTEL/MCP governance-action projections match while "
        "protocol-specific evidence remains distinct."
    )
    return 0


def main() -> int:
    return run_self_test()


if __name__ == "__main__":
    raise SystemExit(main())
