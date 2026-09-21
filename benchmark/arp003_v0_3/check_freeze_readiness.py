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
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

import validate_methodology_decisions as methodology_validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "benchmark" / "arp003_v0_3" / "freeze-readiness.schema.json"
CURRENT = ROOT / "benchmark" / "arp003_v0_3" / "freeze-readiness.current.json"
PROTOCOL = ROOT / "benchmark" / "arp003_v0_3" / "protocol.json"
METHODOLOGY = (
    ROOT / "benchmark" / "arp003_v0_3" / "methodology-decisions.current.json"
)

METHODOLOGY_GATE_MAP = {
    "comparison_conditions": "comparison_conditions",
    "reviewer_population": "reviewer_population",
    "primary_endpoints": "primary_endpoint",
    "effect_or_precision_target": "effect_precision_target",
    "challenge_strata": "challenge_design",
    "timing_exclusions": "primary_timing_clock",
}

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


def methodology_status_map(methodology: dict[str, Any]) -> dict[str, str]:
    # validate() checks the complete ledger before this projection. In
    # particular, duplicate IDs must not be hidden by dictionary replacement.
    return {item["decision_id"]: item["status"] for item in methodology["decisions"]}


def semantic_errors(
    readiness: dict[str, Any],
    protocol: dict[str, Any],
    methodology: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if readiness["protocol_version"] != protocol.get("version"):
        errors.append(
            "readiness protocol_version does not match protocol.json version"
        )

    if methodology.get("protocol_version") != protocol.get("version"):
        errors.append(
            "methodology ledger protocol_version does not match protocol.json version"
        )

    methodology_status = methodology_status_map(methodology)
    for gate_id, decision_id in METHODOLOGY_GATE_MAP.items():
        if decision_id not in methodology_status:
            errors.append(
                f"methodology ledger is missing decision {decision_id!r} "
                f"required by freeze gate {gate_id!r}"
            )
            continue
        if is_resolved(readiness["gates"][gate_id]) and methodology_status[decision_id] != "selected":
            errors.append(
                f"freeze gate {gate_id!r} is resolved but methodology decision "
                f"{decision_id!r} is not selected"
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

    unresolved_methodology = sorted(
        item["decision_id"]
        for item in methodology["decisions"]
        if item["pre_freeze_required"] and item["status"] != "selected"
    )

    if status in {"ready_for_freeze", "frozen"} and methodology["status"] != "methodology_resolved":
        errors.append(
            f"study_status={status!r} requires methodology ledger status "
            "'methodology_resolved'"
        )

    if status == "ready_for_freeze" and unresolved_pre:
        errors.append(
            "study_status='ready_for_freeze' but pre-freeze gates remain unresolved: "
            + ", ".join(unresolved_pre)
        )
    if status == "ready_for_freeze" and unresolved_methodology:
        errors.append(
            "study_status='ready_for_freeze' but methodology decisions remain "
            "unresolved: " + ", ".join(unresolved_methodology)
        )

    if status == "frozen" and unresolved_all:
        errors.append(
            "study_status='frozen' but gates remain unresolved: "
            + ", ".join(unresolved_all)
        )
    if status == "frozen" and unresolved_methodology:
        errors.append(
            "study_status='frozen' but methodology decisions remain unresolved: "
            + ", ".join(unresolved_methodology)
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
    methodology: Any,
) -> list[str]:
    errors = structural_errors(readiness, schema)
    if errors:
        return errors
    if not isinstance(readiness, dict):
        return ["$: readiness state must be an object"]
    if not isinstance(protocol, dict):
        return ["protocol.json must be an object"]
    if not isinstance(methodology, dict):
        return ["methodology decision ledger must be an object"]

    # A status string alone is not evidence of a valid decision. Reuse the
    # canonical validator for candidate references, rationale, evidence, unique
    # IDs, and mandatory decisions before consulting the selected statuses.
    try:
        methodology_schema = load_json(methodology_validator.SCHEMA_PATH)
        Draft202012Validator.check_schema(methodology_schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        return [f"unable to load methodology schema: {exc}"]
    methodology_errors = methodology_validator.validate(
        methodology, methodology_schema, protocol
    )
    if methodology_errors:
        return [f"methodology ledger: {error}" for error in methodology_errors]
    return semantic_errors(readiness, protocol, methodology)


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


def synthetic_resolved_methodology(
    methodology: dict[str, Any],
) -> dict[str, Any]:
    resolved = copy.deepcopy(methodology)
    for decision in resolved["decisions"]:
        if decision.get("pre_freeze_required") is True:
            decision["status"] = "selected"
            decision["selected_candidate"] = decision["candidates"][0]["candidate_id"]
            decision["rationale"] = "Synthetic self-test selection only."
            decision["evidence_refs"] = ["synthetic://methodology-selection"]
    resolved["status"] = "methodology_resolved"
    return resolved


def run_self_test() -> int:
    schema = load_json(SCHEMA)
    current = load_json(CURRENT)
    protocol = load_json(PROTOCOL)
    methodology = load_json(METHODOLOGY)
    Draft202012Validator.check_schema(schema)

    errors = validate(current, schema, protocol, methodology)
    assert not errors, errors
    assert current["study_status"] == "development_not_ready"
    assert not all(
        is_resolved(current["gates"][gate_id])
        for gate_id in PRE_FREEZE_GATES
    )

    premature = copy.deepcopy(current)
    premature["study_status"] = "ready_for_freeze"
    errors = validate(premature, schema, protocol, methodology)
    assert any("pre-freeze gates remain unresolved" in error for error in errors)

    premature_frozen = copy.deepcopy(current)
    premature_frozen["study_status"] = "frozen"
    errors = validate(premature_frozen, schema, protocol, methodology)
    assert any("gates remain unresolved" in error for error in errors)
    assert any("protocol.json still has frozen=false" in error for error in errors)

    complete_without_evidence = copy.deepcopy(current)
    complete_without_evidence["gates"]["reviewer_population"]["status"] = "complete"
    complete_without_evidence["gates"]["reviewer_population"]["evidence_refs"] = []
    errors = validate(complete_without_evidence, schema, protocol, methodology)
    assert any("has no evidence_refs" in error for error in errors)

    ready, ready_protocol = synthetic_ready_state(current, protocol, frozen=False)
    errors = validate(ready, schema, ready_protocol, methodology)
    assert any("methodology decision" in error for error in errors)

    resolved_methodology = synthetic_resolved_methodology(methodology)
    errors = validate(ready, schema, ready_protocol, resolved_methodology)
    assert not errors, errors

    frozen, frozen_protocol = synthetic_ready_state(current, protocol, frozen=True)
    errors = validate(frozen, schema, frozen_protocol, methodology)
    assert any("methodology decision" in error for error in errors)

    errors = validate(frozen, schema, frozen_protocol, resolved_methodology)
    assert not errors, errors

    # Regression: selected labels must not conceal an invalid ledger, including
    # a custom ledger supplied through --methodology.
    for key, value, expected in (
        ("selected_candidate", "no_such_candidate", "LEDGER-05"),
        ("rationale", " ", "LEDGER-06"),
        ("evidence_refs", [], "LEDGER-07"),
        ("pre_freeze_required", False, "LEDGER-12"),
    ):
        invalid = copy.deepcopy(resolved_methodology)
        invalid["decisions"][0][key] = value
        errors = validate(ready, schema, ready_protocol, invalid)
        assert any(expected in error for error in errors), errors

    duplicate = copy.deepcopy(resolved_methodology)
    duplicate["decisions"].append(copy.deepcopy(duplicate["decisions"][0]))
    errors = validate(ready, schema, ready_protocol, duplicate)
    assert any("LEDGER-02" in error for error in errors), errors

    missing = copy.deepcopy(resolved_methodology)
    missing["decisions"] = missing["decisions"][1:]
    errors = validate(ready, schema, ready_protocol, missing)
    assert any("LEDGER-03" in error for error in errors), errors

    malformed = copy.deepcopy(resolved_methodology)
    malformed["decisions"] = "selected"
    errors = validate(ready, schema, ready_protocol, malformed)
    assert any("STRUCTURE" in error for error in errors), errors

    stale_status = copy.deepcopy(resolved_methodology)
    stale_status["status"] = "development_unresolved"
    errors = validate(ready, schema, ready_protocol, stale_status)
    assert any("requires methodology ledger status" in error for error in errors), errors

    # Additional required unresolved decisions must also block readiness.
    extra_required = copy.deepcopy(resolved_methodology)
    unresolved_template = next(
        item for item in methodology["decisions"]
        if item["status"] == "unresolved"
    )
    extra = copy.deepcopy(unresolved_template)
    extra["decision_id"] = "synthetic_additional_required_decision"
    extra_required["decisions"].append(extra)
    extra_required["status"] = "development_unresolved"
    errors = validate(ready, schema, ready_protocol, extra_required)
    assert any(extra["decision_id"] in error for error in errors), errors

    # Every mapped gate whose methodology decision is still unresolved is
    # cross-checked even before an overall ready claim. Already selected
    # comparison_conditions is intentionally excluded from this negative test.
    current_methodology_status = methodology_status_map(methodology)
    for gate_id, decision_id in METHODOLOGY_GATE_MAP.items():
        if current_methodology_status[decision_id] == "selected":
            continue
        for gate_status in ("complete", "not_applicable"):
            premature_gate = copy.deepcopy(current)
            premature_gate["gates"][gate_id]["status"] = gate_status
            premature_gate["gates"][gate_id]["evidence_refs"] = ["synthetic://gate"]
            errors = validate(premature_gate, schema, protocol, methodology)
            assert any("is not selected" in error for error in errors), errors

    protocol_drift = copy.deepcopy(protocol)
    protocol_drift["version"] = "other-version"
    errors = validate(current, schema, protocol_drift, methodology)
    assert any("protocol_version does not match" in error for error in errors)

    # Exercise the actual CLI with a custom ledger; validating only the
    # checked-in ledger in another CI step cannot protect this input path.
    with tempfile.TemporaryDirectory(prefix="arp003-readiness-selftest-") as tmp:
        directory = Path(tmp)
        ready_path = directory / "readiness.json"
        protocol_path = directory / "protocol.json"
        methodology_path = directory / "methodology.json"
        ready_path.write_text(json.dumps(ready), encoding="utf-8")
        protocol_path.write_text(json.dumps(ready_protocol), encoding="utf-8")
        methodology_path.write_text(json.dumps(resolved_methodology), encoding="utf-8")
        command = [
            sys.executable, str(Path(__file__).resolve()), str(ready_path),
            "--protocol", str(protocol_path),
            "--methodology", str(methodology_path), "--require-ready",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr

        invalid = copy.deepcopy(resolved_methodology)
        invalid["decisions"][0]["selected_candidate"] = "no_such_candidate"
        methodology_path.write_text(json.dumps(invalid), encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode == 1 and "LEDGER-05" in result.stderr, result.stderr

        methodology_path.unlink()
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode == 2, result.stderr

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
        "--methodology",
        default=str(METHODOLOGY),
        help="Methodology decision ledger used for freeze cross-check.",
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
        methodology = load_json(Path(args.methodology))
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(
            f"ERROR: unable to load readiness/protocol/methodology/schema: {exc}",
            file=sys.stderr,
        )
        return 2

    if args.self_test:
        return run_self_test()

    errors = validate(readiness, schema, protocol, methodology)
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
