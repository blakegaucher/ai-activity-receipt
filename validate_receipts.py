#!/usr/bin/env python3
"""
Candidate validator for the AI Activity Receipt project.

Two layers are checked:
1. Structural validity against activity-receipt.schema.json
2. An executable subset of the candidate semantic invariants in
   docs/INVARIANTS.md

Run with no arguments to execute the repository fixture manifest:

    python validate_receipts.py

Or validate one or more arbitrary Receipt files:

    python validate_receipts.py path/to/receipt.json [more.json ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parent
DEFAULT_SCHEMA = ROOT / "activity-receipt.schema.json"
DEFAULT_FIXTURE_MANIFEST = ROOT / "examples" / "fixture-manifest.json"

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


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    # Candidate schema timestamps use RFC 3339 date-time values. Returning None
    # for offset-naive values prevents accidental aware/naive comparisons when
    # this helper is called outside the schema-gated validation path.
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


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
    valid_from = parse_datetime(authority.get("valid_from"))
    valid_until = parse_datetime(authority.get("valid_until"))
    generated_at = parse_datetime((receipt.get("integrity") or {}).get("generated_at"))

    # INV-06 — The authority window itself must be coherent.
    if valid_from and valid_until and valid_from > valid_until:
        violations.append(
            {
                "invariant": "INV-06",
                "path": "$.authority",
                "reason": "authority.valid_from occurs after authority.valid_until.",
            }
        )

    sources = receipt.get("material_sources") or []
    source_values = [
        source.get("source_id")
        for source in sources
        if isinstance(source, dict) and source.get("source_id")
    ]
    source_ids = set(source_values)

    # INV-02 — Registered, unambiguous material sources.
    for source_id, count in Counter(source_values).items():
        if count > 1:
            violations.append(
                {
                    "invariant": "INV-02",
                    "path": "$.material_sources",
                    "reason": f"Source identifier {source_id!r} is duplicated.",
                }
            )

    actions = receipt.get("material_actions") or []
    event_values = [
        action.get("event_id")
        for action in actions
        if isinstance(action, dict) and action.get("event_id")
    ]
    action_event_ids = set(event_values)

    # INV-11 — Stable event identity.
    for event_id, count in Counter(event_values).items():
        if count > 1:
            violations.append(
                {
                    "invariant": "INV-11",
                    "path": "$.material_actions",
                    "reason": f"Material-action event_id {event_id!r} is duplicated.",
                }
            )

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

        # INV-03 — Completed consequential actions require approved,
        # in-scope, prior authority.
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

            decision_raw = action.get("authorization_decided_at")
            occurred_at = parse_datetime(action.get("occurred_at"))
            if not decision_raw:
                violations.append(
                    {
                        "invariant": "INV-03",
                        "path": f"$.material_actions[{index}].authorization_decided_at",
                        "reason": "Completed consequential action has no recorded authorization decision time.",
                    }
                )
            else:
                decided_at = parse_datetime(decision_raw)
                if decided_at and occurred_at and decided_at > occurred_at:
                    violations.append(
                        {
                            "invariant": "INV-03",
                            "path": f"$.material_actions[{index}].authorization_decided_at",
                            "reason": "Authorization decision occurs after the consequential action.",
                        }
                    )

        # INV-04 — Explicitly prohibited operations cannot be represented as
        # approved successful execution under the same authority.
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

        # INV-05 — Material blocked/failed activity preserves linked incident evidence.
        incidents = receipt.get("incidents") or []
        materially_failed = (
            action.get("status") in {"blocked", "failed"}
            and (
                action.get("consequential") is True
                or action.get("authorization") == "denied"
            )
        )
        if materially_failed:
            event_id = action.get("event_id")
            linked = [
                incident
                for incident in incidents
                if isinstance(incident, dict)
                and (not event_id or incident.get("event_id") == event_id)
            ]
            if not linked:
                violations.append(
                    {
                        "invariant": "INV-05",
                        "path": f"$.material_actions[{index}]",
                        "reason": "Material blocked/failed activity has no linked incident record.",
                    }
                )

        # INV-06 — Action time must fall inside the authority window.
        occurred_at = parse_datetime(action.get("occurred_at"))
        if occurred_at and valid_from and occurred_at < valid_from:
            violations.append(
                {
                    "invariant": "INV-06",
                    "path": f"$.material_actions[{index}].occurred_at",
                    "reason": "Material action occurred before authority.valid_from.",
                }
            )
        if occurred_at and valid_until and occurred_at > valid_until:
            violations.append(
                {
                    "invariant": "INV-06",
                    "path": f"$.material_actions[{index}].occurred_at",
                    "reason": "Material action occurred after authority.valid_until.",
                }
            )

        # INV-15 — The Receipt cannot be generated before activity it represents.
        if occurred_at and generated_at and occurred_at > generated_at:
            violations.append(
                {
                    "invariant": "INV-15",
                    "path": f"$.material_actions[{index}].occurred_at",
                    "reason": "Material action occurs after integrity.generated_at.",
                }
            )

        decided_at = parse_datetime(action.get("authorization_decided_at"))
        if decided_at and generated_at and decided_at > generated_at:
            violations.append(
                {
                    "invariant": "INV-15",
                    "path": f"$.material_actions[{index}].authorization_decided_at",
                    "reason": "Authorization decision occurs after integrity.generated_at.",
                }
            )

    # INV-07 — Verification evidence must exist and resolve.
    known_evidence_ids = source_ids | action_event_ids
    verification = receipt.get("verification") or {}
    evidence_refs = verification.get("evidence_refs") or []
    if verification.get("state") == "confirmed" and not evidence_refs:
        violations.append(
            {
                "invariant": "INV-07",
                "path": "$.verification.evidence_refs",
                "reason": "Confirmed verification has no supporting evidence reference.",
            }
        )
    for evidence_ref in evidence_refs:
        if evidence_ref not in known_evidence_ids:
            violations.append(
                {
                    "invariant": "INV-07",
                    "path": "$.verification.evidence_refs",
                    "reason": f"Verification reference {evidence_ref!r} cannot be resolved.",
                }
            )

    # INV-08 — Incident event references must resolve.
    incidents = receipt.get("incidents") or []
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

    # INV-09 — Direct-delegation profile.
    # The candidate v0.2 public schema represents one acting system and one
    # direct delegate. Richer delegation chains remain future work.
    delegate = authority.get("delegate")
    system = receipt.get("system") or {}
    agent_id = system.get("agent_id")
    if delegate and agent_id and delegate != agent_id:
        violations.append(
            {
                "invariant": "INV-09",
                "path": "$.authority.delegate",
                "reason": (
                    f"authority.delegate {delegate!r} does not match "
                    f"system.agent_id {agent_id!r} in the direct-delegation profile."
                ),
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

    # Semantic invariants assume the candidate schema's object shapes. Running
    # them against structurally invalid data can turn a useful schema rejection
    # into a Python type error (for example authority=[]). Keep one defensive
    # diagnostic independent of schema validity: private-reasoning exclusion.
    if structural:
        semantic = (
            walk_for_private_reasoning_keys(receipt)
            if isinstance(receipt, (dict, list))
            else []
        )
    else:
        semantic = invariant_violations(receipt) if isinstance(receipt, dict) else []

    return {
        "file": str(path),
        "schema_valid": not structural,
        "semantic_valid": not structural and not semantic,
        "schema_errors": structural,
        "violations": semantic,
    }


def print_result(
    result: dict[str, Any],
    expected_schema: bool | None = None,
    expected_semantic: bool | None = None,
) -> None:
    name = result["file"]
    schema_ok = result["schema_valid"]
    semantic_ok = result["semantic_valid"]

    if expected_schema is None or expected_semantic is None:
        status = "PASS" if schema_ok and semantic_ok else "FAIL"
        print(f"{status}: {name}")
    else:
        expectation_ok = schema_ok == expected_schema and semantic_ok == expected_semantic
        status = "PASS" if expectation_ok else "FAIL"
        print(
            f"{status}: {name} "
            f"(expected schema={expected_schema}, semantic={expected_semantic})"
        )

    for error in result["schema_errors"]:
        print(f"  SCHEMA {error['path']}: {error['reason']}")

    for violation in result["violations"]:
        print(
            f"  {violation['invariant']} {violation['path']}: "
            f"{violation['reason']}"
        )


def run_fixtures(schema: dict[str, Any], manifest_path: Path) -> int:
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load fixture manifest {manifest_path}: {exc}", file=sys.stderr)
        return 2

    fixtures = manifest.get("fixtures") if isinstance(manifest, dict) else None
    if not isinstance(fixtures, list) or not fixtures:
        print("ERROR: fixture manifest has no fixtures.", file=sys.stderr)
        return 2

    failed = False

    for fixture in fixtures:
        if not isinstance(fixture, dict) or not fixture.get("path"):
            print(f"FAIL: malformed fixture entry: {fixture!r}")
            failed = True
            continue

        relative = fixture["path"]
        expected_schema = bool(fixture.get("expected_schema_valid"))
        expected_semantic = bool(fixture.get("expected_semantic_valid"))
        expected_invariants = set(fixture.get("expected_invariants") or [])

        path = ROOT / relative
        if not path.exists():
            print(f"FAIL: missing fixture {relative}")
            failed = True
            continue

        result = validate(path, schema)
        print_result(
            result,
            expected_schema=expected_schema,
            expected_semantic=expected_semantic,
        )

        triggered = {v["invariant"] for v in result["violations"]}
        outcome_ok = (
            result["schema_valid"] == expected_schema
            and result["semantic_valid"] == expected_semantic
        )
        invariant_ok = expected_invariants.issubset(triggered)

        if not outcome_ok:
            failed = True
        if not invariant_ok:
            print(
                "  EXPECTATION: missing expected invariant(s): "
                + ", ".join(sorted(expected_invariants - triggered))
            )
            failed = True

    if failed:
        print("\nFixture validation failed.")
        return 1

    print(f"\nAll {len(fixtures)} candidate fixture expectations passed.")
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
    parser.add_argument(
        "--fixture-manifest",
        default=str(DEFAULT_FIXTURE_MANIFEST),
        help="Path to the fixture expectation manifest.",
    )
    args = parser.parse_args()

    schema_path = Path(args.schema)
    try:
        schema = load_json(schema_path)
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load/validate schema {schema_path}: {exc}", file=sys.stderr)
        return 2

    if not args.files:
        return run_fixtures(schema, Path(args.fixture_manifest))

    failed = False
    for raw_path in args.files:
        result = validate(Path(raw_path), schema)
        print_result(result)
        if not (result["schema_valid"] and result["semantic_valid"]):
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
