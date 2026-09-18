#!/usr/bin/env python3
"""Standalone multi-hop delegation-chain prototype validator.

This validates the candidate design in docs/MULTI-AGENT-DELEGATION.md without
changing candidate-record-v0.1. It is a research prototype, not an authorization
server or token validator.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "research" / "delegation-chain.schema.json"
DEFAULT_EXAMPLE = ROOT / "research" / "delegation-chain-example.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_time(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid RFC 3339 timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    return parsed


def structural_errors(value: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"STRUCTURE {path}: {error.message}")
    return output


def semantic_errors(doc: dict[str, Any]) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []

    actors = set(doc["actors"])
    root = doc["root_principal"]
    current_actor = doc["current_actor"]
    hops = doc["hops"]
    action = doc["action"]

    if root not in actors:
        errors.append("DLG-09 root_principal does not resolve to a known actor")
    if current_actor not in actors:
        errors.append("DLG-09 current_actor does not resolve to a known actor")

    hop_ids = [hop["hop_id"] for hop in hops]
    if len(set(hop_ids)) != len(hop_ids):
        errors.append("DLG-00 hop_id values must be unique")

    if hops[0]["delegator"] != root:
        errors.append("DLG-02 first hop delegator must equal root_principal")

    for index in range(1, len(hops)):
        if hops[index - 1]["delegate"] != hops[index]["delegator"]:
            errors.append(
                "DLG-01 adjacent delegation hops do not form a continuous chain "
                f"at index {index}"
            )

    if hops[-1]["delegate"] != current_actor:
        errors.append("DLG-03 final hop delegate must equal current_actor")

    for index, hop in enumerate(hops):
        if hop["delegator"] not in actors:
            errors.append(
                f"DLG-09 hop {index} delegator {hop['delegator']!r} is unknown"
            )
        if hop["delegate"] not in actors:
            errors.append(
                f"DLG-09 hop {index} delegate {hop['delegate']!r} is unknown"
            )

    path = [root] + [hop["delegate"] for hop in hops]
    if len(path) != len(set(path)):
        errors.append("DLG-04 active delegation path must not contain a cycle")

    action_time = parse_time(action["occurred_at"], "action.occurred_at")
    effective_scope: set[str] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    for index, hop in enumerate(hops):
        hop_from = parse_time(hop["valid_from"], f"hops[{index}].valid_from")
        hop_until = parse_time(hop["valid_until"], f"hops[{index}].valid_until")
        hop_decided = parse_time(hop["decided_at"], f"hops[{index}].decided_at")

        if hop_from > hop_until:
            errors.append(
                f"DLG-07 hop {index} valid_from is later than valid_until"
            )

        if hop_decided > action_time:
            errors.append(
                f"DLG-08 hop {index} delegation decision occurs after the action"
            )

        if hop["state"] != "active":
            errors.append(
                f"DLG-12 hop {index} is not active at evaluation time "
                f"(state={hop['state']!r})"
            )

        hop_scope = set(hop["scope"])
        if effective_scope is None:
            effective_scope = set(hop_scope)
        else:
            if not hop_scope.issubset(effective_scope):
                amplified = sorted(hop_scope - effective_scope)
                errors.append(
                    f"DLG-05 hop {index} amplifies authority with {amplified!r}"
                )
            effective_scope &= hop_scope

        effective_from = (
            hop_from
            if effective_from is None
            else max(effective_from, hop_from)
        )
        effective_until = (
            hop_until
            if effective_until is None
            else min(effective_until, hop_until)
        )

    assert effective_scope is not None
    assert effective_from is not None
    assert effective_until is not None

    if effective_from > effective_until:
        errors.append("DLG-07 effective delegation time window is empty")

    if not (effective_from <= action_time <= effective_until):
        errors.append("DLG-07 action occurs outside the effective delegation window")

    if action["actor_id"] != current_actor:
        errors.append("DLG-03 action.actor_id must equal current_actor")

    if action["actor_id"] not in actors:
        errors.append("DLG-09 action.actor_id does not resolve to a known actor")

    if action["status"] == "completed" and action["consequential"] is True:
        if action["operation"] not in effective_scope:
            errors.append(
                "DLG-10 completed consequential action is outside effective scope"
            )

        if action["authorization"] != "approved":
            errors.append(
                "DLG-10 completed consequential action requires approved authorization"
            )

        auth_decided_raw = action.get("authorization_decided_at")
        if not isinstance(auth_decided_raw, str) or not auth_decided_raw:
            errors.append(
                "DLG-10 completed consequential action requires "
                "authorization_decided_at"
            )
        else:
            auth_decided = parse_time(
                auth_decided_raw,
                "action.authorization_decided_at",
            )
            if auth_decided > action_time:
                errors.append(
                    "DLG-10 action authorization decision occurs after action"
                )

    summary = {
        "actor_path": path,
        "effective_scope": sorted(effective_scope),
        "effective_valid_from": effective_from.isoformat().replace("+00:00", "Z"),
        "effective_valid_until": effective_until.isoformat().replace("+00:00", "Z"),
    }

    return errors, summary


def validate_document(
    doc: Any,
    schema: dict[str, Any],
) -> tuple[list[str], dict[str, Any] | None]:
    errors = structural_errors(doc, schema)
    if errors:
        return errors, None
    if not isinstance(doc, dict):
        return ["STRUCTURE $: document must be an object"], None
    try:
        return semantic_errors(doc)
    except ValueError as exc:
        return [f"SEMANTIC timestamp error: {exc}"], None


def run_self_test(schema: dict[str, Any], example: dict[str, Any]) -> int:
    errors, summary = validate_document(example, schema)
    assert not errors, errors
    assert summary == {
        "actor_path": [
            "user-2",
            "agent-orchestrator-4",
            "agent-specialist-7",
        ],
        "effective_scope": ["analyze", "read"],
        "effective_valid_from": "2026-09-18T12:02:00Z",
        "effective_valid_until": "2026-09-18T12:30:00Z",
    }

    cases: list[tuple[str, str, Any]] = []

    broken = copy.deepcopy(example)
    broken["hops"][1]["delegator"] = "other-agent"
    broken["actors"].append("other-agent")
    cases.append(("broken-continuity", "DLG-01", broken))

    cycle = copy.deepcopy(example)
    cycle["hops"][1]["delegate"] = "user-2"
    cycle["current_actor"] = "user-2"
    cycle["action"]["actor_id"] = "user-2"
    cases.append(("cycle", "DLG-04", cycle))

    amplified = copy.deepcopy(example)
    amplified["hops"][1]["scope"].append("send_email")
    cases.append(("scope-amplification", "DLG-05", amplified))

    late_hop = copy.deepcopy(example)
    late_hop["hops"][1]["decided_at"] = "2026-09-18T12:11:00Z"
    cases.append(("late-hop-decision", "DLG-08", late_hop))

    revoked = copy.deepcopy(example)
    revoked["hops"][1]["state"] = "revoked"
    cases.append(("revoked-hop", "DLG-12", revoked))

    outside_window = copy.deepcopy(example)
    outside_window["action"]["occurred_at"] = "2026-09-18T12:31:00Z"
    outside_window["action"]["authorization_decided_at"] = "2026-09-18T12:29:00Z"
    cases.append(("outside-window", "DLG-07", outside_window))

    wrong_actor = copy.deepcopy(example)
    wrong_actor["action"]["actor_id"] = "agent-orchestrator-4"
    cases.append(("wrong-current-actor", "DLG-03", wrong_actor))

    out_of_scope = copy.deepcopy(example)
    out_of_scope["action"]["operation"] = "send_email"
    cases.append(("out-of-scope-action", "DLG-10", out_of_scope))

    late_action_auth = copy.deepcopy(example)
    late_action_auth["action"]["authorization_decided_at"] = (
        "2026-09-18T12:11:00Z"
    )
    cases.append(("late-action-auth", "DLG-10", late_action_auth))

    unknown_actor = copy.deepcopy(example)
    unknown_actor["actors"].remove("agent-specialist-7")
    cases.append(("unknown-actor", "DLG-09", unknown_actor))

    for label, expected_code, candidate in cases:
        candidate_errors, _ = validate_document(candidate, schema)
        assert candidate_errors, f"{label}: invalid case was accepted"
        assert any(
            expected_code in error for error in candidate_errors
        ), f"{label}: expected {expected_code}, got {candidate_errors!r}"

    print(
        "Delegation-chain prototype self-test passed: "
        f"1 valid + {len(cases)} adversarial cases."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the standalone multi-hop delegation-chain prototype."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=str(DEFAULT_EXAMPLE),
        help="Delegation-chain JSON document.",
    )
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA),
        help="Delegation-chain JSON Schema.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        schema = load_json(Path(args.schema))
        Draft202012Validator.check_schema(schema)
        doc = load_json(Path(args.input))
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load prototype/schema: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        if not isinstance(doc, dict):
            print("ERROR: self-test example must be an object", file=sys.stderr)
            return 2
        return run_self_test(schema, doc)

    errors, summary = validate_document(doc, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(json.dumps({"valid": True, "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
