#!/usr/bin/env python3
"""Validate AR-P003 v0.3 methodology candidate impact coverage.

This tool does not select a methodology. It ensures that decision-support
material covers every candidate in the methodology ledger exactly once and
does not invent candidates that the ledger does not preserve.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark" / "arp003_v0_3"
SCHEMA = BENCH / "methodology-impact-map.schema.json"
IMPACT = BENCH / "methodology-impact-map.json"
LEDGER = BENCH / "methodology-decisions.current.json"


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
        output.append(f"STRUCTURE {path}: {error.message}")
    return output


def candidate_pairs(ledger: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (decision["decision_id"], candidate["candidate_id"])
        for decision in ledger["decisions"]
        for candidate in decision["candidates"]
    }


def map_pairs(impact: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (decision["decision_id"], candidate["candidate_id"])
        for decision in impact["decisions"]
        for candidate in decision["candidates"]
    ]


def semantic_errors(
    impact: dict[str, Any],
    ledger: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if impact["protocol_version"] != ledger["protocol_version"]:
        errors.append(
            "IMPACT-01 protocol_version does not match methodology ledger"
        )
    if impact["ledger_version"] != ledger["ledger_version"]:
        errors.append(
            "IMPACT-02 ledger_version does not match methodology ledger"
        )

    decision_ids = [item["decision_id"] for item in impact["decisions"]]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("IMPACT-03 decision_id values must be unique")

    pairs = map_pairs(impact)
    if len(pairs) != len(set(pairs)):
        errors.append("IMPACT-04 candidate entries must be unique")

    expected = candidate_pairs(ledger)
    actual = set(pairs)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(
            f"IMPACT-05 ledger candidate(s) missing from impact map: {missing!r}"
        )
    if extra:
        errors.append(
            f"IMPACT-06 impact map contains unknown candidate(s): {extra!r}"
        )

    for index, decision in enumerate(impact["decisions"]):
        for cindex, candidate in enumerate(decision["candidates"]):
            if not candidate["impacted_artifacts"]:
                errors.append(
                    f"IMPACT-07 decisions[{index}].candidates[{cindex}] "
                    "must identify at least one impacted artifact"
                )
            if not candidate["required_before_execution"]:
                errors.append(
                    f"IMPACT-08 decisions[{index}].candidates[{cindex}] "
                    "must identify at least one pre-execution requirement"
                )

    # The impact map is not a selection surface.
    if impact.get("status") != "decision_support_only_no_selection":
        errors.append("IMPACT-09 impact map must remain decision-support only")

    return errors


def validate(
    impact: Any,
    schema: dict[str, Any],
    ledger: Any,
) -> list[str]:
    errors = structural_errors(impact, schema)
    if errors:
        return errors
    if not isinstance(impact, dict) or not isinstance(ledger, dict):
        return ["STRUCTURE impact map and ledger must both be objects"]
    return semantic_errors(impact, ledger)


def run_self_test() -> int:
    schema = load_json(SCHEMA)
    impact = load_json(IMPACT)
    ledger = load_json(LEDGER)
    Draft202012Validator.check_schema(schema)

    errors = validate(impact, schema, ledger)
    assert not errors, errors

    missing = copy.deepcopy(impact)
    missing["decisions"][0]["candidates"].pop()
    errors = validate(missing, schema, ledger)
    assert any("IMPACT-05" in error for error in errors)

    unknown = copy.deepcopy(impact)
    unknown["decisions"][0]["candidates"][0]["candidate_id"] = "invented"
    errors = validate(unknown, schema, ledger)
    assert any("IMPACT-05" in error for error in errors)
    assert any("IMPACT-06" in error for error in errors)

    duplicate = copy.deepcopy(impact)
    duplicate["decisions"][0]["candidates"].append(
        copy.deepcopy(duplicate["decisions"][0]["candidates"][0])
    )
    errors = validate(duplicate, schema, ledger)
    assert any("IMPACT-04" in error for error in errors)

    mismatch = copy.deepcopy(impact)
    mismatch["protocol_version"] = "other"
    errors = validate(mismatch, schema, ledger)
    assert any("IMPACT-01" in error for error in errors)

    print(
        "AR-P003 methodology impact-map self-test passed: every preserved "
        "ledger candidate has exactly one non-selecting implementation-impact entry."
    )
    return 0


def main() -> int:
    try:
        schema = load_json(SCHEMA)
        impact = load_json(IMPACT)
        ledger = load_json(LEDGER)
        Draft202012Validator.check_schema(schema)
        if "--self-test" in sys.argv:
            return run_self_test()
        errors = validate(impact, schema, ledger)
    except (OSError, json.JSONDecodeError, SchemaError, AssertionError) as exc:
        print(f"ERROR: methodology impact-map validation failed: {exc}", file=sys.stderr)
        return 2

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "AR-P003 methodology impact map is complete and consistent with the "
        "current unresolved methodology ledger."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
