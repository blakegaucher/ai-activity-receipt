#!/usr/bin/env python3
"""
Candidate validator for the AI Activity Receipt project.

Two layers are checked:
1. Structural validity against activity-receipt.schema.json
2. A small executable subset of the candidate semantic invariants in
   docs/INVARIANTS.md

Run with no arguments to execute the repository fixture checks:

    python validate_receipts.py

Or validate one or more arbitrary Receipt files:

    python validate_receipts.py path/to/receipt.json [more.json ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent
DEFAULT_SCHEMA = ROOT / "activity-receipt.schema.json"

FIXTURES = (
    ("examples/sample-receipt.json", True),
    ("examples/valid-completed-authorized-action.json", True),
    ("examples/invalid-completed-with-denied-authorization.json", False),
)

PRIVATE_REASONING_KEYS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "private_reasoning",
    "reasoning_trace",
    "scratchpad",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def json_path(parts: list[Any]) -> str:
    if not parts:
        return "$"
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}"
    return out


def schema_errors(receipt: Any, schema: dict[str, Any]) -> list[dict[str, str]]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[dict[str, str]] = []

    for error in sorted(validator.iter_errors(receipt), key=lambda e: list(e.absolute_path)):
        errors.append(
            {
                "layer": "schema",
                "path": json_path(list(error.absolute_path)),
                "reason": error.message,
            }
        )
    return errors


def walk_for_private_reasoning_keys(value: Any, path: str = "$") -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []

    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.lower() in PRIVATE_REASONING_KEYS:
                violations.append(
                    {
                        "invariant": "INV-14",
                        "path": child_path,
                        "reason": "Private-reasoning field is excluded from the Receipt.",
                    }
                )
            violations.extend(walk_for_private_reasoning_keys(child, child_path))

    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(walk_for_private_reasoning_keys(child, f"{path}[{index}]"))

    return violations


def invariant_violations(receipt: dict[str, Any]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []

    authority = receipt.get("authority") or {}
    scope = set(authority.get("scope") or [])
    prohibited = set(authority.get("prohibited") or [])

    sources = receipt.get("material_sources") or []
    source_ids = {
        source.get("source_id")
        for source in sources
        if isinstance(source, dict) and source.get("source_id")
    }

    actions = receipt.get("material_actions") or []
    action_event_ids = {
        action.get("event_id")
        for action in actions
        if isinstance(action, dict) and action.get("event_id")
    }

    # INV-02 — Registered material sources.
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        for source_ref in action.get("source_refs") or []:
            if source_ref not in source_ids:
                violations.append(
                    {
                        "invariant": "INV-02",
                        "path": f"$.material_actions[{index}].source_refs",
                        "reason": f"Source reference {source_ref!r} is not registered in material_sources.",
                    }
                )

    # INV-03 — Completed consequential actions require approved, in-scope authority.
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue

        if action.get("consequential") is True and action.get("status") == "completed":
            operation = action.get("operation")
            authorization = action.get("authorization")

            if authorization != "approved":
                violations.append(
                    {
                        "invariant": "INV-03",
                        "path": f"$.material_actions[{index}]",
                        "reason": (
                            "Consequential action is recorded as completed without "
                            "approved authorization."
                        ),
                    }
                )

            if operation and operation not in scope:
                violations.append(
                    {
                        "invariant": "INV-03",
                        "path": f"$.material_actions[{index}].operation",
                        "reason": f"Completed consequential operation {operation!r} is outside authority.scope.",
                    }
                )

    # INV-04 — Explicitly prohibited operations cannot be represented as
    # approved successful execution under the same authority.
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue

        operation = action.get("operation")
        if (
            operation in prohibited
            and action.get("status") == "completed"
            and action.get("authorization") == "approved"
        ):
            violations.append(
                {
                    "invariant": "INV-04",
                    "path": f"$.material_actions[{index}]",
                    "reason": (
                        f"Operation {operation!r} is explicitly prohibited but is "
                        "recorded as approved and completed."
                    ),
                }
            )

    # INV-05 — Material blocked/failed activity should preserve incident evidence.
    incidents = receipt.get("incidents") or []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue

        materially_failed = (
            action.get("status") in {"blocked", "failed"}
            and (
                action.get("consequential") is True
                or action.get("authorization") == "denied"
            )
        )
        if materially_failed and not incidents:
            violations.append(
                {
                    "invariant": "INV-05",
                    "path": f"$.material_actions[{index}]",
                    "reason": "Material blocked/failed activity has no incident record.",
                }
            )

    # INV-07 — Verification references must resolve to evidence known to this
    # candidate Receipt representation. We currently accept material source IDs
    # or material-action event IDs.
    known_evidence_ids = source_ids | action_event_ids
    verification = receipt.get("verification") or {}
    for evidence_ref in verification.get("evidence_refs") or []:
        if evidence_ref not in known_evidence_ids:
            violations.append(
                {
                    "invariant": "INV-07",
                    "path": "$.verification.evidence_refs",
                    "reason": f"Verification reference {evidence_ref!r} cannot be resolved.",
                }
            )

    # INV-08 — Incident event references must resolve.
    for index, incident in enumerate(incidents):
        if not isinstance(incident, dict):
            continue
        event_id = incident.get("event_id")
        if event_id and event_id not in action_event_ids:
            violations.append(
                {
                    "invariant": "INV-08",
                    "path": f"$.incidents[{index}].event_id",
                    "reason": f"Incident event_id {event_id!r} does not resolve to a material action.",
                }
            )

    # INV-14 — Private reasoning is excluded.
    violations.extend(walk_for_private_reasoning_keys(receipt))

    return violations


def validate(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    try:
        receipt = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "file": str(path),
            "schema_valid": False,
            "semantic_valid": False,
            "schema_errors": [
                {
                    "layer": "json",
                    "path": "$",
                    "reason": str(exc),
                }
            ],
            "violations": [],
        }

    structural = schema_errors(receipt, schema)
    semantic = invariant_violations(receipt) if not structural and isinstance(receipt, dict) else []

    return {
        "file": str(path),
        "schema_valid": not structural,
        "semantic_valid": not structural and not semantic,
        "schema_errors": structural,
        "violations": semantic,
    }


def print_result(result: dict[str, Any], expected_semantic: bool | None = None) -> None:
    name = result["file"]
    schema_ok = result["schema_valid"]
    semantic_ok = result["semantic_valid"]

    if expected_semantic is None:
        status = "PASS" if schema_ok and semantic_ok else "FAIL"
        print(f"{status}: {name}")
    else:
        expectation_ok = schema_ok and semantic_ok == expected_semantic
        status = "PASS" if expectation_ok else "FAIL"
        expected_text = "semantic-valid" if expected_semantic else "semantic-invalid"
        print(f"{status}: {name} (expected {expected_text})")

    for error in result["schema_errors"]:
        print(f"  SCHEMA {error['path']}: {error['reason']}")

    for violation in result["violations"]:
        print(
            f"  {violation['invariant']} {violation['path']}: "
            f"{violation['reason']}"
        )


def run_fixtures(schema: dict[str, Any]) -> int:
    failed = False

    for relative, expected_semantic in FIXTURES:
        path = ROOT / relative
        if not path.exists():
            print(f"FAIL: missing fixture {relative}")
            failed = True
            continue

        result = validate(path, schema)
        print_result(result, expected_semantic=expected_semantic)

        if not result["schema_valid"] or result["semantic_valid"] != expected_semantic:
            failed = True

    if failed:
        print("\nFixture validation failed.")
        return 1

    print("\nAll candidate fixture expectations passed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AI Activity Receipt JSON files.")
    parser.add_argument(
        "files",
        nargs="*",
        help="Receipt JSON files. If omitted, repository fixture expectations are tested.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
        help="Path to the candidate JSON Schema.",
    )
    args = parser.parse_args()

    schema_path = Path(args.schema)
    try:
        schema = load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load schema {schema_path}: {exc}", file=sys.stderr)
        return 2

    if not args.files:
        return run_fixtures(schema)

    failed = False
    for raw_path in args.files:
        result = validate(Path(raw_path), schema)
        print_result(result)
        if not (result["schema_valid"] and result["semantic_valid"]):
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
