#!/usr/bin/env python3
"""Development-only source-to-record fidelity pilot for scientific model calls."""

from __future__ import annotations

import json
from pathlib import Path

from derive_receipt import (
    derive_receipt,
    record_semantic_errors,
    validate_derived_receipt,
    validate_record_structure,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "research" / "scientific-model-provenance"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    record_schema = load(ROOT / "activity-record.schema.json")
    receipt_schema = load(ROOT / "activity-receipt.schema.json")
    reference_record = load(FIXTURES / "reference-only-record.json")
    overloaded_record = load(FIXTURES / "invalid-overloaded-record.json")

    structural = validate_record_structure(reference_record, record_schema)
    assert not structural, structural

    semantic = record_semantic_errors(reference_record)
    assert not semantic, semantic

    receipt = derive_receipt(reference_record)
    receipt_errors = validate_derived_receipt(receipt, receipt_schema)
    assert not receipt_errors, receipt_errors

    serialized_receipt = json.dumps(receipt, sort_keys=True)
    for forbidden_detail in (
        "mcp_public_bpka",
        "1.4.0",
        "7.6891093254",
        "out_of_domain",
        "low_confidence",
    ):
        assert forbidden_detail not in serialized_receipt, (
            f"reference-only mapping unexpectedly retained {forbidden_detail!r}"
        )

    overload_errors = validate_record_structure(overloaded_record, record_schema)
    assert overload_errors, "closed event schema unexpectedly accepted overload"
    joined = "\n".join(overload_errors)
    assert "Additional properties are not allowed" in joined, joined
    assert "model_id" in joined
    assert "model_version" in joined
    assert "prediction" in joined

    print(
        json.dumps(
            {
                "reference_only_record": "structural_and_semantic_pass",
                "derived_receipt": "pass",
                "typed_scientific_result_in_receipt": False,
                "overloaded_event": "rejected_as_expected",
                "decision": "mapping_gap_confirmed_without_schema_change",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
