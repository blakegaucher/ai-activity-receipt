#!/usr/bin/env python3
"""Validate the AR-P003 v0.3 methodology-decision ledger.

The ledger exists to preserve unresolved conflicts between the current
repository draft and earlier methodology recommendations. It prevents those
differences from being silently reconciled during later study preparation.

This validator does not choose a methodology. It only enforces explicit,
evidence-linked decision state before a confirmatory protocol can be frozen.
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
SCHEMA_PATH = (
    ROOT / "benchmark" / "arp003_v0_3" / "methodology-decisions.schema.json"
)
LEDGER_PATH = (
    ROOT / "benchmark" / "arp003_v0_3" / "methodology-decisions.current.json"
)
PROTOCOL_PATH = ROOT / "benchmark" / "arp003_v0_3" / "protocol.json"

REQUIRED_DECISIONS = {
    "comparison_conditions",
    "primary_endpoint",
    "primary_timing_clock",
    "challenge_design",
    "reviewer_population",
    "effect_precision_target",
}


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


def semantic_errors(
    ledger: dict[str, Any],
    protocol: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if ledger["protocol_version"] != protocol.get("version"):
        errors.append(
            "LEDGER-01 protocol_version does not match protocol.json "
            f"({ledger['protocol_version']!r} != {protocol.get('version')!r})"
        )

    decisions = ledger["decisions"]
    decision_ids = [item["decision_id"] for item in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("LEDGER-02 decision_id values must be unique")

    missing = sorted(REQUIRED_DECISIONS - set(decision_ids))
    if missing:
        errors.append(
            "LEDGER-03 required methodology decision(s) missing: "
            f"{missing!r}"
        )

    selected_required = 0
    required_total = 0

    for index, decision in enumerate(decisions):
        candidates = decision["candidates"]
        candidate_ids = [item["candidate_id"] for item in candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            errors.append(
                f"LEDGER-04 decisions[{index}] candidate_id values must be unique"
            )

        mandatory = decision["decision_id"] in REQUIRED_DECISIONS
        required = mandatory or decision["pre_freeze_required"]
        if mandatory and not decision["pre_freeze_required"]:
            errors.append(
                f"LEDGER-12 decisions[{index}] mandatory decision "
                f"{decision['decision_id']!r} must remain pre_freeze_required"
            )

        if required:
            required_total += 1

        status = decision["status"]
        selected = decision.get("selected_candidate")

        if status == "selected":
            if selected not in set(candidate_ids):
                errors.append(
                    f"LEDGER-05 decisions[{index}] selected_candidate "
                    f"{selected!r} does not resolve to a listed candidate"
                )
            if not str(decision.get("rationale") or "").strip():
                errors.append(
                    f"LEDGER-06 decisions[{index}] selected decision requires "
                    "a non-empty rationale"
                )
            if not decision.get("evidence_refs"):
                errors.append(
                    f"LEDGER-07 decisions[{index}] selected decision requires "
                    "decision-level evidence_refs"
                )
            if required:
                selected_required += 1

        elif status == "unresolved":
            if selected is not None:
                errors.append(
                    f"LEDGER-08 decisions[{index}] unresolved decision must not "
                    "carry selected_candidate"
                )

        elif status == "deferred":
            if required:
                errors.append(
                    f"LEDGER-09 decisions[{index}] pre-freeze-required decision "
                    "cannot be deferred"
                )
            if selected is not None:
                errors.append(
                    f"LEDGER-08 decisions[{index}] deferred decision must not "
                    "carry selected_candidate"
                )

    unresolved_required = required_total - selected_required

    if ledger["status"] == "methodology_resolved" and unresolved_required:
        errors.append(
            "LEDGER-10 methodology_resolved requires every pre-freeze "
            "methodology decision to be selected"
        )

    if protocol.get("frozen") is True and unresolved_required:
        errors.append(
            "LEDGER-11 protocol.json cannot be frozen while required "
            "methodology decisions remain unresolved"
        )

    return errors


def validate(
    ledger: Any,
    schema: dict[str, Any],
    protocol: Any,
) -> list[str]:
    errors = structural_errors(ledger, schema)
    if errors:
        return errors
    if not isinstance(ledger, dict):
        return ["STRUCTURE $: methodology ledger must be an object"]
    if not isinstance(protocol, dict):
        return ["PROTOCOL protocol.json must contain an object"]
    return semantic_errors(ledger, protocol)


def run_self_test() -> int:
    schema = load_json(SCHEMA_PATH)
    ledger = load_json(LEDGER_PATH)
    protocol = load_json(PROTOCOL_PATH)
    Draft202012Validator.check_schema(schema)

    errors = validate(ledger, schema, protocol)
    assert not errors, errors

    duplicate = copy.deepcopy(ledger)
    duplicate["decisions"].append(copy.deepcopy(duplicate["decisions"][0]))
    errors = validate(duplicate, schema, protocol)
    assert any("LEDGER-02" in error for error in errors)

    missing_decision = copy.deepcopy(ledger)
    missing_decision["decisions"] = [
        item
        for item in missing_decision["decisions"]
        if item["decision_id"] != "primary_endpoint"
    ]
    errors = validate(missing_decision, schema, protocol)
    assert any("LEDGER-03" in error for error in errors)

    duplicate_candidate = copy.deepcopy(ledger)
    target = duplicate_candidate["decisions"][0]
    target["candidates"].append(copy.deepcopy(target["candidates"][0]))
    errors = validate(duplicate_candidate, schema, protocol)
    assert any("LEDGER-04" in error for error in errors)

    bad_selection = copy.deepcopy(ledger)
    target = bad_selection["decisions"][0]
    target["status"] = "selected"
    target["selected_candidate"] = "no_such_candidate"
    target["rationale"] = "Synthetic self-test rationale."
    errors = validate(bad_selection, schema, protocol)
    assert any("LEDGER-05" in error for error in errors)

    missing_rationale = copy.deepcopy(ledger)
    target = missing_rationale["decisions"][0]
    target["status"] = "selected"
    target["selected_candidate"] = target["candidates"][0]["candidate_id"]
    target["rationale"] = ""
    errors = validate(missing_rationale, schema, protocol)
    assert any("LEDGER-06" in error for error in errors)

    unresolved_with_selection = copy.deepcopy(ledger)
    unresolved_with_selection["decisions"][0]["selected_candidate"] = (
        unresolved_with_selection["decisions"][0]["candidates"][0]["candidate_id"]
    )
    errors = validate(unresolved_with_selection, schema, protocol)
    assert any("LEDGER-08" in error for error in errors)

    prematurely_resolved = copy.deepcopy(ledger)
    prematurely_resolved["status"] = "methodology_resolved"
    errors = validate(prematurely_resolved, schema, protocol)
    assert any("LEDGER-10" in error for error in errors)

    frozen_protocol = copy.deepcopy(protocol)
    frozen_protocol["frozen"] = True
    errors = validate(ledger, schema, frozen_protocol)
    assert any("LEDGER-11" in error for error in errors)

    protocol_mismatch = copy.deepcopy(protocol)
    protocol_mismatch["version"] = "other-version"
    errors = validate(ledger, schema, protocol_mismatch)
    assert any("LEDGER-01" in error for error in errors)

    # Required decision IDs remain required even if an input flips their flags.
    optionalized = copy.deepcopy(ledger)
    for decision in optionalized["decisions"]:
        decision["pre_freeze_required"] = False
    optionalized["status"] = "methodology_resolved"
    errors = validate(optionalized, schema, frozen_protocol)
    for code in ("LEDGER-10", "LEDGER-11", "LEDGER-12"):
        assert any(code in error for error in errors), errors

    deferred = copy.deepcopy(ledger)
    deferred["decisions"][0]["pre_freeze_required"] = False
    deferred["decisions"][0]["status"] = "deferred"
    errors = validate(deferred, schema, protocol)
    assert any("LEDGER-09" in error for error in errors), errors
    assert any("LEDGER-12" in error for error in errors), errors

    # Positive control: valid synthetic selections still pass, including freeze.
    resolved = copy.deepcopy(ledger)
    resolved["status"] = "methodology_resolved"
    for decision in resolved["decisions"]:
        decision["status"] = "selected"
        decision["selected_candidate"] = decision["candidates"][0]["candidate_id"]
        decision["rationale"] = "Synthetic self-test selection only."
        decision["evidence_refs"] = ["synthetic://methodology-selection"]
    for test_protocol in (protocol, frozen_protocol):
        errors = validate(resolved, schema, test_protocol)
        assert not errors, errors

    print(
        "AR-P003 methodology-decision ledger self-test passed: current "
        "unresolved state, valid synthetic selections, and adversarial mutations."
    )
    return 0


def main() -> int:
    try:
        schema = load_json(SCHEMA_PATH)
        ledger = load_json(LEDGER_PATH)
        protocol = load_json(PROTOCOL_PATH)
        Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load methodology ledger/schema/protocol: {exc}", file=sys.stderr)
        return 2

    if "--self-test" in sys.argv[1:]:
        try:
            return run_self_test()
        except AssertionError as exc:
            print(f"ERROR: methodology self-test failed: {exc}", file=sys.stderr)
            return 1

    errors = validate(ledger, schema, protocol)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    unresolved = [
        item["decision_id"]
        for item in ledger["decisions"]
        if item["pre_freeze_required"] and item["status"] != "selected"
    ]
    print(
        "AR-P003 methodology-decision ledger is valid. "
        f"Unresolved pre-freeze decisions: {len(unresolved)}."
    )
    if unresolved:
        print("  " + "\n  ".join(unresolved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
