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
REVIEWER_INSTRUCTIONS_PATH = (
    ROOT / "docs" / "AR-P003-V0.3-REVIEWER-INSTRUCTIONS-DRAFT.md"
)
RECRUITMENT_ELIGIBILITY_PATH = (
    ROOT / "docs" / "AR-P003-V0.3-RECRUITMENT-ELIGIBILITY.md"
)

REQUIRED_DECISIONS = {
    "comparison_conditions",
    "primary_endpoint",
    "primary_timing_clock",
    "challenge_design",
    "reviewer_population",
    "effect_precision_target",
}

REVIEWER_POPULATION_CANDIDATE = "relevant_professional_reviewers"
REVIEWER_POPULATION_DOMAINS = [
    "technical_audit",
    "cybersecurity",
    "compliance",
    "ai_governance",
    "incident_investigation_or_review",
    "software_or_system_operations",
    "technical_assurance",
    "closely_related_evidence_review_work",
]
REVIEWER_EXPERIENCE_BANDS = [
    "1_to_2_years",
    "3_to_5_years",
    "6_plus_years",
]
REVIEWER_EXCLUSIONS = [
    "constructed_or_materially_edited_sealed_evaluation_cases",
    "created_or_accessed_hidden_gold_answers",
    "participated_in_scoring_rule_development_using_sealed_cases",
    "scored_confirmatory_responses",
    "accessed_protected_confirmatory_analysis_before_assigned_cases_complete",
]
REVIEWER_ASSISTANCE_RULE = {
    "external_web_search": "prohibited",
    "external_ai_assistants": "prohibited",
    "another_person": "prohibited",
    "outside_tools_or_evidence_not_supplied_by_study": "prohibited",
    "amendment_rule": (
        "only_an_explicitly_versioned_protocol_amendment_before_"
        "confirmatory_execution_may_authorize_an_exception"
    ),
}
REVIEWER_SCOPE_RULE = (
    "claims_limited_to_the_relevant_professional_population_actually_recruited_"
    "no_generalization_from_a_convenience_or_unrepresentative_sample"
)

PRIMARY_ENDPOINT_CANDIDATE = "correct_completion_by_180s"
PRIMARY_ENDPOINT_DEADLINE = 180
PRIMARY_TIMING_CANDIDATES = [
    "active_time_primary",
    "wall_deadline_with_hidden_sensitivity",
]

REVIEWER_DOCUMENTATION_MARKERS = {
    "reviewer instructions": (
        "relevant professional reviewers",
        "at least 1 year",
        "1–2 years",
        "3–5 years",
        "6+ years",
        "sufficient English proficiency",
        "No particular degree, certification, or job title is required",
        "Prior general familiarity with AI Activity Receipt is permitted and recorded",
        "external web search",
        "external AI assistant",
        "another person",
        "outside tool or evidence not supplied by the study",
        "recruitment is not authorized",
    ),
    "recruitment eligibility": (
        "relevant professional or practical experience",
        "at least 1 year",
        "1–2 years",
        "3–5 years",
        "6+ years",
        "sufficient English proficiency",
        "A degree, certification, or particular job title is not required",
        "prior general familiarity with AI Activity Receipt",
        "external web search",
        "external AI assistants",
        "another person",
        "outside tools/evidence not supplied by the study",
        "No reviewer recruitment or human execution is authorized",
    ),
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
    decisions_by_id: dict[str, dict[str, Any]] = {}

    for index, decision in enumerate(decisions):
        decisions_by_id[decision["decision_id"]] = decision
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

    reviewer_decision = decisions_by_id.get("reviewer_population")
    if reviewer_decision and reviewer_decision.get("status") == "selected":
        if reviewer_decision.get("selected_candidate") != REVIEWER_POPULATION_CANDIDATE:
            errors.append(
                "LEDGER-13 selected reviewer_population must resolve to "
                f"{REVIEWER_POPULATION_CANDIDATE!r} for this protocol version"
            )
        population = protocol.get("reviewer_population")
        if not isinstance(population, dict):
            errors.append(
                "LEDGER-14 selected reviewer_population requires a structured "
                "protocol.json reviewer_population object"
            )
        else:
            expected_values = {
                "decision_id": "reviewer_population",
                "selected_candidate": REVIEWER_POPULATION_CANDIDATE,
                "target_population": REVIEWER_POPULATION_CANDIDATE,
                "eligible_domains": REVIEWER_POPULATION_DOMAINS,
                "minimum_relevant_experience_years": 1,
                "experience_bands": REVIEWER_EXPERIENCE_BANDS,
                "english_proficiency_rule": (
                    "sufficient_to_understand_technical_evidence_instructions_"
                    "and_structured_response_interface"
                ),
                "degree_required": False,
                "certification_required": False,
                "specific_job_title_required": False,
                "prior_general_ai_activity_receipt_familiarity": (
                    "permitted_and_recorded"
                ),
                "exclusions": REVIEWER_EXCLUSIONS,
                "study_case_assistance": REVIEWER_ASSISTANCE_RULE,
                "scope_of_inference": REVIEWER_SCOPE_RULE,
                "recruitment_authorized": False,
            }
            for key, expected in expected_values.items():
                if population.get(key) != expected:
                    errors.append(
                        "LEDGER-15 protocol reviewer_population field "
                        f"{key!r} does not match the selected frozen design"
                    )

    endpoint_decision = decisions_by_id.get("primary_endpoint")
    if endpoint_decision and endpoint_decision.get("status") == "selected":
        if endpoint_decision.get("selected_candidate") != PRIMARY_ENDPOINT_CANDIDATE:
            errors.append(
                "LEDGER-16 selected primary_endpoint must resolve to "
                f"{PRIMARY_ENDPOINT_CANDIDATE!r} for this protocol version"
            )

        endpoint = protocol.get("primary_endpoint")
        if not isinstance(endpoint, dict):
            errors.append(
                "LEDGER-17 selected primary_endpoint requires a structured "
                "protocol.json primary_endpoint object"
            )
        else:
            expected_endpoint = {
                "decision_id": "primary_endpoint",
                "selected_candidate": PRIMARY_ENDPOINT_CANDIDATE,
                "endpoint_id": PRIMARY_ENDPOINT_CANDIDATE,
                "outcome_type": "binary",
                "deadline_seconds": PRIMARY_ENDPOINT_DEADLINE,
                "required_judgments_rule": (
                    "case_specific_frozen_primary_endpoint_contract"
                ),
                "acceptable_evidence_rule": (
                    "each_required_judgment_must_have_at_least_one_prespecified_"
                    "acceptable_support_set_for_the_assigned_condition"
                ),
                "primary_timing_clock": "unresolved",
                "timing_candidates": PRIMARY_TIMING_CANDIDATES,
                "confirmatory_derivation_status": (
                    "blocked_until_primary_timing_clock_selected"
                ),
                "component_endpoints_role": "secondary_diagnostic_not_co_primary",
                "critical_false_clearance_role": (
                    "separate_prespecified_safety_endpoint"
                ),
                "critical_false_clearance_threshold": (
                    "unresolved_effect_precision_target"
                ),
            }
            for key, expected in expected_endpoint.items():
                if endpoint.get(key) != expected:
                    errors.append(
                        "LEDGER-18 protocol primary_endpoint field "
                        f"{key!r} does not match the selected design"
                    )

            contingency = endpoint.get("development_only_contingency") or {}
            if contingency.get("allowed_before_confirmatory_freeze_only") is not True:
                errors.append("LEDGER-19 endpoint contingency must be pre-freeze only")
            if contingency.get("automatic_component_endpoint_promotion") is not False:
                errors.append(
                    "LEDGER-19 endpoint contingency must prohibit automatic "
                    "component-endpoint promotion"
                )
            if contingency.get("confirmatory_outcome_inspection_allowed") is not False:
                errors.append(
                    "LEDGER-19 endpoint contingency must prohibit confirmatory "
                    "outcome inspection"
                )

        timing_decision = decisions_by_id.get("primary_timing_clock") or {}
        if (
            timing_decision.get("status") != "unresolved"
            or timing_decision.get("selected_candidate") is not None
        ):
            errors.append(
                "LEDGER-20 selecting primary_endpoint must not silently select "
                "primary_timing_clock"
            )
        effect_decision = decisions_by_id.get("effect_precision_target") or {}
        if (
            effect_decision.get("status") != "unresolved"
            or effect_decision.get("selected_candidate") is not None
        ):
            errors.append(
                "LEDGER-21 selecting primary_endpoint must not select "
                "effect_precision_target"
            )
        timing = protocol.get("timing") or {}
        if timing.get("primary_timing_clock") != "unresolved":
            errors.append(
                "LEDGER-22 protocol timing must remain unresolved until the "
                "separate timing decision is selected"
            )
        if timing.get("candidates") != PRIMARY_TIMING_CANDIDATES:
            errors.append("LEDGER-22 protocol timing candidate set changed")

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


def reviewer_documentation_errors(
    instructions: str,
    recruitment: str,
) -> list[str]:
    errors: list[str] = []
    documents = {
        "reviewer instructions": instructions,
        "recruitment eligibility": recruitment,
    }
    for label, markers in REVIEWER_DOCUMENTATION_MARKERS.items():
        text = documents[label]
        for marker in markers:
            if marker not in text:
                errors.append(
                    f"LEDGER-DOC-01 {label} is missing selected-population marker "
                    f"{marker!r}"
                )
    return errors


def run_self_test() -> int:
    schema = load_json(SCHEMA_PATH)
    ledger = load_json(LEDGER_PATH)
    protocol = load_json(PROTOCOL_PATH)
    instructions = REVIEWER_INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    recruitment = RECRUITMENT_ELIGIBILITY_PATH.read_text(encoding="utf-8")
    Draft202012Validator.check_schema(schema)

    errors = validate(ledger, schema, protocol)
    assert not errors, errors
    errors = reviewer_documentation_errors(instructions, recruitment)
    assert not errors, errors

    missing_instruction_rule = instructions.replace(
        "external AI assistant", "outside automated helper", 1
    )
    errors = reviewer_documentation_errors(missing_instruction_rule, recruitment)
    assert any("LEDGER-DOC-01" in error for error in errors), errors

    missing_recruitment_rule = recruitment.replace(
        "No reviewer recruitment or human execution is authorized",
        "Recruitment status is pending",
        1,
    )
    errors = reviewer_documentation_errors(instructions, missing_recruitment_rule)
    assert any("LEDGER-DOC-01" in error for error in errors), errors

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
    unresolved_target = next(
        item
        for item in unresolved_with_selection["decisions"]
        if item["status"] == "unresolved"
    )
    unresolved_target["selected_candidate"] = unresolved_target["candidates"][0][
        "candidate_id"
    ]
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

    wrong_population_candidate = copy.deepcopy(ledger)
    population_decision = next(
        item
        for item in wrong_population_candidate["decisions"]
        if item["decision_id"] == "reviewer_population"
    )
    population_decision["selected_candidate"] = "population_to_be_selected"
    errors = validate(wrong_population_candidate, schema, protocol)
    assert any("LEDGER-13" in error for error in errors), errors

    missing_population = copy.deepcopy(protocol)
    missing_population.pop("reviewer_population")
    errors = validate(ledger, schema, missing_population)
    assert any("LEDGER-14" in error for error in errors), errors

    population_mutations = (
        ("minimum_relevant_experience_years", 0),
        ("experience_bands", ["1_to_2_years", "6_plus_years"]),
        ("prior_general_ai_activity_receipt_familiarity", "prohibited"),
        ("exclusions", REVIEWER_EXCLUSIONS[:-1]),
        ("study_case_assistance", {"external_web_search": "permitted"}),
        ("recruitment_authorized", True),
    )
    for key, value in population_mutations:
        mutated_protocol = copy.deepcopy(protocol)
        mutated_protocol["reviewer_population"][key] = value
        errors = validate(ledger, schema, mutated_protocol)
        assert any("LEDGER-15" in error for error in errors), (key, errors)

    endpoint_mutations = (
        ("deadline_seconds", 181),
        ("primary_timing_clock", "active_time_primary"),
        ("component_endpoints_role", "co_primary"),
        ("critical_false_clearance_role", "folded_into_primary"),
    )
    for key, value in endpoint_mutations:
        mutated_protocol = copy.deepcopy(protocol)
        mutated_protocol["primary_endpoint"][key] = value
        errors = validate(ledger, schema, mutated_protocol)
        assert any("LEDGER-18" in error for error in errors), (key, errors)

    selected_timing = copy.deepcopy(ledger)
    timing_decision = next(
        item for item in selected_timing["decisions"]
        if item["decision_id"] == "primary_timing_clock"
    )
    timing_decision["status"] = "selected"
    timing_decision["selected_candidate"] = "active_time_primary"
    timing_decision["rationale"] = "Synthetic invalid mutation."
    errors = validate(selected_timing, schema, protocol)
    assert any("LEDGER-20" in error for error in errors), errors

    bad_contingency = copy.deepcopy(protocol)
    bad_contingency["primary_endpoint"]["development_only_contingency"][
        "automatic_component_endpoint_promotion"
    ] = True
    errors = validate(ledger, schema, bad_contingency)
    assert any("LEDGER-19" in error for error in errors), errors

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
        if decision["decision_id"] == "reviewer_population":
            decision["selected_candidate"] = REVIEWER_POPULATION_CANDIDATE
        elif decision["decision_id"] == "primary_endpoint":
            decision["selected_candidate"] = PRIMARY_ENDPOINT_CANDIDATE
        else:
            decision["selected_candidate"] = decision["candidates"][0]["candidate_id"]
        decision["rationale"] = "Synthetic self-test selection only."
        decision["evidence_refs"] = ["synthetic://methodology-selection"]
    for test_protocol in (protocol, frozen_protocol):
        errors = validate(resolved, schema, test_protocol)
        assert not errors, errors

    print(
        "AR-P003 methodology-decision ledger self-test passed: current mixed "
        "selected/unresolved state, valid synthetic selections, and adversarial mutations."
    )
    return 0


def main() -> int:
    try:
        schema = load_json(SCHEMA_PATH)
        ledger = load_json(LEDGER_PATH)
        protocol = load_json(PROTOCOL_PATH)
        instructions = REVIEWER_INSTRUCTIONS_PATH.read_text(encoding="utf-8")
        recruitment = RECRUITMENT_ELIGIBILITY_PATH.read_text(encoding="utf-8")
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
    errors.extend(reviewer_documentation_errors(instructions, recruitment))
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
