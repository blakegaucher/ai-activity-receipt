#!/usr/bin/env python3
"""Validate the candidate machine-readable interoperability crosswalk."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAPPING = ROOT / "mappings" / "interoperability-v0.1.json"
DEFAULT_MAPPING_SCHEMA = ROOT / "mappings" / "interoperability-map.schema.json"
DEFAULT_RECORD_SCHEMA = ROOT / "activity-record.schema.json"

SENSITIVE_IDENTITY_TARGETS = {
    "system.agent_id",
    "authority.principal",
    "authority.delegate",
}
SELF_REPORTED_IDENTITY_MARKERS = (
    "clientinfo",
    "serverinfo",
    "agent card",
)
SENSITIVE_CONTENT_MARKERS = (
    "gen_ai.tool.call.arguments",
    "gen_ai.tool.call.result",
    "params.arguments",
    "response result.content",
    "access token",
    "refresh token",
    "client secret",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_target_path(record_schema: dict[str, Any], path: str) -> bool:
    """Resolve dotted record paths such as events[].operation against JSON Schema."""
    current: dict[str, Any] = record_schema

    for component in path.split("."):
        is_array = component.endswith("[]")
        name = component[:-2] if is_array else component

        properties = current.get("properties")
        if not isinstance(properties, dict) or name not in properties:
            return False

        node = properties[name]
        if not isinstance(node, dict):
            return False

        if is_array:
            if node.get("type") != "array":
                return False
            items = node.get("items")
            if not isinstance(items, dict):
                return False
            current = items
        else:
            current = node

    return True


def semantic_errors(
    mapping_doc: dict[str, Any],
    record_schema: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    profile_ids: set[str] = set()
    mapping_ids: set[str] = set()

    expected_profile = mapping_doc.get("record_schema_profile")
    schema_comment = str(record_schema.get("$comment") or "")
    if expected_profile and expected_profile not in schema_comment:
        errors.append(
            "record_schema_profile does not match activity-record.schema.json $comment"
        )

    for profile_index, profile in enumerate(mapping_doc.get("profiles") or []):
        if not isinstance(profile, dict):
            continue

        profile_id = profile.get("profile_id")
        if profile_id in profile_ids:
            errors.append(f"duplicate profile_id {profile_id!r}")
        elif isinstance(profile_id, str):
            profile_ids.add(profile_id)

        if profile.get("status") == "implemented_adapter":
            adapter_path = profile.get("adapter_path")
            if not isinstance(adapter_path, str) or not (ROOT / adapter_path).is_file():
                errors.append(
                    f"profiles[{profile_index}] implemented adapter path "
                    f"{adapter_path!r} does not resolve"
                )

        for mapping_index, mapping in enumerate(profile.get("mappings") or []):
            if not isinstance(mapping, dict):
                continue

            where = (
                f"profiles[{profile_index}].mappings[{mapping_index}]"
            )
            mapping_id = mapping.get("mapping_id")
            if mapping_id in mapping_ids:
                errors.append(f"{where}: duplicate mapping_id {mapping_id!r}")
            elif isinstance(mapping_id, str):
                mapping_ids.add(mapping_id)

            target_path = mapping.get("target_path")
            if isinstance(target_path, str) and not resolve_target_path(
                record_schema, target_path
            ):
                errors.append(
                    f"{where}: target_path {target_path!r} does not resolve "
                    "against activity-record.schema.json"
                )

            source_expression = str(mapping.get("source_expression") or "")
            source_lower = source_expression.lower()
            decision = mapping.get("decision")

            if (
                any(marker in source_lower for marker in SELF_REPORTED_IDENTITY_MARKERS)
                and target_path in SENSITIVE_IDENTITY_TARGETS
                and decision in {"map", "support"}
            ):
                errors.append(
                    f"{where}: self-reported descriptive identity cannot directly "
                    f"populate security-sensitive target {target_path!r}"
                )

            if (
                any(marker in source_lower for marker in SENSITIVE_CONTENT_MARKERS)
                and decision != "exclude"
            ):
                errors.append(
                    f"{where}: sensitive payload/credential content must be excluded"
                )

    return errors


def schema_errors(
    mapping_doc: Any,
    mapping_schema: dict[str, Any],
) -> list[str]:
    validator = Draft202012Validator(
        mapping_schema,
        format_checker=FormatChecker(),
    )
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(mapping_doc),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def validate(
    mapping_doc: Any,
    mapping_schema: dict[str, Any],
    record_schema: dict[str, Any],
) -> list[str]:
    errors = schema_errors(mapping_doc, mapping_schema)
    if errors:
        return errors
    if not isinstance(mapping_doc, dict):
        return ["$: mapping document must be an object"]
    return semantic_errors(mapping_doc, record_schema)


def run_self_test(
    mapping_doc: dict[str, Any],
    mapping_schema: dict[str, Any],
    record_schema: dict[str, Any],
) -> int:
    errors = validate(mapping_doc, mapping_schema, record_schema)
    assert not errors, errors

    # A mapping target must actually exist in the current canonical record schema.
    bad_target = copy.deepcopy(mapping_doc)
    bad_target["profiles"][0]["mappings"][0]["target_path"] = "system.no_such_field"
    target_errors = validate(bad_target, mapping_schema, record_schema)
    assert any("does not resolve" in error for error in target_errors)

    # Self-reported implementation metadata must not become authenticated identity.
    unsafe_identity = copy.deepcopy(mapping_doc)
    mcp_profile = next(
        profile
        for profile in unsafe_identity["profiles"]
        if profile["profile_id"] == "mcp-2026-07-28"
    )
    client_info = next(
        mapping
        for mapping in mcp_profile["mappings"]
        if mapping["mapping_id"] == "mcp.client-info"
    )
    client_info["decision"] = "map"
    client_info["target_path"] = "system.agent_id"
    identity_errors = validate(unsafe_identity, mapping_schema, record_schema)
    assert any("self-reported descriptive identity" in error for error in identity_errors)

    # Sensitive tool payloads/credentials must remain excluded.
    unsafe_content = copy.deepcopy(mapping_doc)
    otel_profile = next(
        profile
        for profile in unsafe_content["profiles"]
        if profile["profile_id"] == "opentelemetry-genai"
    )
    tool_args = next(
        mapping
        for mapping in otel_profile["mappings"]
        if mapping["mapping_id"] == "otel.tool-arguments"
    )
    tool_args["decision"] = "support"
    tool_args["target_path"] = "sources[].uri"
    content_errors = validate(unsafe_content, mapping_schema, record_schema)
    assert any("sensitive payload/credential content" in error for error in content_errors)

    # Implemented-adapter profiles must refer to a repository file.
    missing_adapter = copy.deepcopy(mapping_doc)
    missing_adapter["profiles"][0]["adapter_path"] = "adapters/no_such_adapter.py"
    adapter_errors = validate(missing_adapter, mapping_schema, record_schema)
    assert any("does not resolve" in error for error in adapter_errors)

    print(
        "Interoperability mapping self-test passed: "
        f"{sum(len(p['mappings']) for p in mapping_doc['profiles'])} mappings "
        f"across {len(mapping_doc['profiles'])} profiles."
    )
    return 0


def main() -> int:
    try:
        mapping_doc = load_json(DEFAULT_MAPPING)
        mapping_schema = load_json(DEFAULT_MAPPING_SCHEMA)
        record_schema = load_json(DEFAULT_RECORD_SCHEMA)
        Draft202012Validator.check_schema(mapping_schema)
        Draft202012Validator.check_schema(record_schema)
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        print(f"ERROR: unable to load mapping/schema: {exc}", file=sys.stderr)
        return 2

    if not isinstance(mapping_doc, dict):
        print("ERROR: mapping document must be a JSON object", file=sys.stderr)
        return 1

    errors = validate(mapping_doc, mapping_schema, record_schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return run_self_test(mapping_doc, mapping_schema, record_schema)


if __name__ == "__main__":
    raise SystemExit(main())
