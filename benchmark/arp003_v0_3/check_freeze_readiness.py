#!/usr/bin/env python3
"""Validate AR-P003 v0.3 machine-readable freeze readiness.

This tool is intentionally conservative. It prevents repository metadata from
calling the study ready/frozen while required gates are unresolved. It does not
make methodology decisions for the project owner and does not substitute for
ethics review, browser testing, sealed corpus construction, or human evidence.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "freeze-readiness.schema.json"
CURRENT = ROOT / "benchmark" / "arp003_v0_3" / "freeze-readiness.current.json"
PROTOCOL = ROOT / "benchmark" / "arp003_v0_3" / "protocol.json"

ALL_GATES = (
    "comparison_conditions",
    "reviewer_population",
    "primary_endpoints",
    "effect_or_precision_target",
    "crossed_design_power",
    "sample_allocation_stopping",
    "sealed_corpus",
    "leakage_validation",
    "challenge_strata",
    "browser_smoke",
    "reviewer_instructions",
    "assignment",
    "timing_exclusions",
    "scorer_analysis_plan",
    "ethics_determination",
    "freeze_manifest",
)

PRE_FREEZE_GATES = tuple(g for g in ALL_GATES if g != "freeze_manifest")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
        output.append(f"{path}: {error.message}")
    return output


def is_resolved(gate: dict[str, Any]) -> bool:
    return gate["status"] in {"complete", "not_applicable"}


def semantic_errors(
    readiness: dict[str, Any],
    protocol: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if readiness["protocol_version"] != protocol.get("version"):
        errors.append(
            "readiness protocol_version does not match protocol.json version"
        )

    for gate_id, gate in readiness["gates"].items():
        if gate["status"] in {"complete", "not_applicable"}:
            if not gate["evidence_refs"]:
                errors.append(
                    f"gate {gate_id!r} is {gate['status']!r} but has no evidence_refs"
                )

    status = readiness["study_status"]

    unresolved_pre = [
        gate_id
        for gate_id in PRE_FREEZE_GATES
        if not is_resolved(readiness["gates"][gate_id])
    ]
    unresolved_all = [
        gate_id
        for gate_id in ALL_GATES
        if not is_resolved(readiness["gates"][gate_id])
    ]

    if status == "ready_for_freeze" and unresolved_pre:
        errors.append(
            "study_status='ready_for_freeze' but pre-freeze gates remain unresolved: "
            + ", ".join(unresolved_pre)
        )

    if status == "frozen" and unresolved_all:
        errors.append(
            "study_status='frozen' but gates remain unresolved: "
            + ", ".join(unresolved_all)
        )

    protocol_frozen = protocol.get("frozen") is True
    if status == "frozen" and not protocol_frozen:
        errors.append(
            "readiness claims frozen but protocol.json still has frozen=false"
        )
    if protocol_frozen and status != "frozen":
        errors.append(
            "protocol.json has frozen=true but freeze-readiness state is not frozen"
        )

    if status == "development_not_ready" and protocol_frozen:
        errors.append(
            "development_not_ready cannot coexist with a frozen protocol"
        )

    ethics = readiness["gates"]["ethics_determination"]
    if ethics["status"] == "not_applicable":
        refs = " ".join(ethics["evidence_refs"]).lower()
        if "determination" not in refs and "ethics" not in refs and "reb" not in refs and "irb" not in refs:
            errors.append(
                "ethics_determination marked not_applicable without a clearly named "
                "determination evidence reference"
            )

    freeze_gate = readiness["gates"]["freeze_manifest"]
    if freeze_gate["status"] == "complete":
        refs = " ".join(freeze_gate["evidence_refs"]).lower()
        if "manifest" not in refs:
            errors.append(
                "freeze_manifest marked complete without a manifest-like evidence reference"
            )

    return errors


def validate(
    readiness: Any,
    schema: dict[str, Any],
    protocol: dict[str, Any],
) -> list[str]:
    errors = structural_errors(readiness, schema)
    if errors:
        return errors
    if not isinstance(readiness, dict):
        return ["$: readiness state must be an object"]
    if not isinstance(protocol, dict):
        return ["protocol.json must be an object"]
    return semantic_errors(readiness, protocol)


def synthetic_ready_state(
    current: dict[str, Any],
    protocol: dict[str, Any],
    *,
    frozen: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    readiness = copy.deepcopy(current)
    protocol_copy = copy.deepcopy(protocol)

    for gate_id, gate in readiness["gates"].items():
        gate["status"] = "complete"
        gate["evidence_refs"] = [f"synthetic://evidence/{gate_id}"]
        gate["notes"] = "Synthetic self-test evidence only."

    readiness["gates"]["ethics_determination"]["evidence_refs"] = [
        "synthetic://ethics-determination"
    ]
    readiness["gates"]["freeze_manifest"]["evidence_refs"] = [
        "synthetic://FREEZE-MANIFEST.json"
    ]

    if frozen:
        readiness["study_status"] = "frozen"
        protocol_copy["frozen"] = True
        protocol_copy["status"] = "synthetic_frozen_self_test"
    else:
        readiness["study_status"] = "ready_for_freeze"
        readiness["gates"]["freeze_manifest"]["status"] = "prepared"
        readiness["gates"]["freeze_manifest"]["evidence_refs"] = [
            "benchmark/arp003_v0_3/freeze_manifest.py"
        ]
        protocol_copy["frozen"] = False

    return readiness, protocol_copy


def run_self_test() -> int:
    schema = load_json(SCHEMA)
    current = load_json(CURRENT)
    protocol = load_json(PROTOCOL)
    Draft202012Validator.check_schema(schema)

    errors = validate(current, schema, protocol)
    assert not errors, errors
    assert current["study_status"] == "development_not_ready"
    assert not all(
        is_resolved(current["gates"][gate_id])
        for gate_id in PRE_FREEZE_GATES
    )

    premature = copy.deepcopy(current)
    premature["study_status"] = "ready_for_freeze"
    errors = validate(premature, schema, protocol)
    assert any("pre-freeze gates remain unresolved" in error for error in errors)

    premature_frozen = copy.deepcopy(current)
    premature_frozen["study_status"] = "frozen"
    errors = validate(premature_frozen, schema, protocol)
    assert any("gates remain unresolved" in error for error in errors)
    assert any("protocol.json still has frozen=false" in error for error in errors)

    complete_without_evidence = copy.deepcopy(current)
    complete_without_evidence["gates"]["reviewer_population"]["status"] = "complete"
    complete_without_evidence["gates"]["reviewer_population"]["evidence_refs"] = []
    errors = validate(complete_without_evidence, schema, protocol)
    assert any("has no evidence_refs" in error for error in errors)

    ready, ready_protocol = synthetic_ready_state(current, protocol, frozen=False)
    errors = validate(ready, schema, ready_protocol)
    assert not errors, errors

    frozen, frozen_protocol = synthetic_ready_state(current, protocol, frozen=True)
    errors = validate(frozen, schema, frozen_protocol)
    assert not errors, errors

    protocol_drift = copy.deepcopy(protocol)
    protocol_drift["version"] = "other-version"
    errors = validate(current, schema, protocol_drift)
    assert any("protocol_version does not match" in error for error in errors)

    print(
        "AR-P003 freeze-readiness self-test passed: current draft remains "
        "development_not_ready; premature readiness/freeze claims are rejected."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate AR-P003 v0.3 freeze readiness."
    )
    parser.add_argument(
        "readiness",
        nargs="?",
        default=str(CURRENT),
        help="Freeze-readiness JSON file.",
    )
    parser.add_argument(
        "--protocol",
        default=str(PROTOCOL),
        help="Protocol JSON used for version/frozen-state cross-check.",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero unless all pre-freeze gates are resolved.",
    )
    parser.add_argument(
        "--require-frozen",
        action="store_true",
        help="Exit non-zero unless the state and protocol are fully frozen.",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        schema = load_json(SCHEMA)
        Draft202012Validator.check_schema(schema)
        readiness = load_json(Path(args.readiness))
        protocol = load_json(Path(args.protocol))
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load readiness/protocol/schema: {exc}", file=sys.stderr)
        return 2

    if args.self_test:
        return run_self_test()

    errors = validate(readiness, schema, protocol)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.require_ready:
        unresolved = [
            gate_id
            for gate_id in PRE_FREEZE_GATES
            if not is_resolved(readiness["gates"][gate_id])
        ]
        if unresolved:
            print(
                "ERROR: AR-P003 is not ready for freeze; unresolved pre-freeze "
                "gates: " + ", ".join(unresolved),
                file=sys.stderr,
            )
            return 1

    if args.require_frozen and readiness["study_status"] != "frozen":
        print(
            "ERROR: AR-P003 is not frozen according to freeze-readiness state.",
            file=sys.stderr,
        )
        return 1

    resolved = sum(
        1 for gate_id in ALL_GATES if is_resolved(readiness["gates"][gate_id])
    )
    print(
        f"AR-P003 freeze-readiness state is internally valid: "
        f"{resolved}/{len(ALL_GATES)} gates resolved; "
        f"study_status={readiness['study_status']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
