#!/usr/bin/env python3
"""Create a content-bound SHA-256 freeze manifest for AR-P003 artifacts.

This is a deterministic integrity record, not a digital signature, trusted
timestamp, ethics determination, or evidence that the study is ready to run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark" / "arp003_v0_3"
DEFAULT_PROTOCOL = BENCH / "protocol.json"
MANIFEST_SCHEMA = BENCH / "freeze-manifest.schema.json"
MANIFEST_VERSION = "AR-P003-v0.3-freeze-manifest-v0.2"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def relative_inside(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"artifact is outside root {root}: {path}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def make_manifest(
    paths: list[Path],
    root: Path,
    *,
    protocol_path: Path,
    generated_at: str | None = None,
    require_protocol_frozen: bool = False,
) -> dict[str, Any]:
    root_resolved = root.resolve()
    protocol_resolved = protocol_path.resolve()

    if not protocol_resolved.is_file():
        raise ValueError(f"protocol file does not exist: {protocol_path}")

    protocol = load_json(protocol_resolved)
    if not isinstance(protocol, dict):
        raise ValueError("protocol file must contain a JSON object")
    if protocol.get("protocol_id") != "AR-P003":
        raise ValueError("protocol_id must equal 'AR-P003'")
    protocol_version = protocol.get("version")
    if not isinstance(protocol_version, str) or not protocol_version:
        raise ValueError("protocol version must be a non-empty string")
    protocol_frozen = protocol.get("frozen")
    if not isinstance(protocol_frozen, bool):
        raise ValueError("protocol frozen field must be boolean")
    if require_protocol_frozen and not protocol_frozen:
        raise ValueError(
            "final freeze requested but protocol.json still has frozen=false"
        )

    protocol_relative = relative_inside(protocol_resolved, root_resolved)
    protocol_sha = "sha256:" + sha256_file(protocol_resolved)

    artifacts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_file():
            raise ValueError(f"not a file: {path}")
        relative = relative_inside(resolved, root_resolved)
        if relative in seen:
            raise ValueError(f"duplicate artifact path: {relative}")
        seen.add(relative)
        artifacts.append(
            {
                "path": relative,
                "bytes": resolved.stat().st_size,
                "sha256": sha256_file(resolved),
            }
        )

    if not artifacts:
        raise ValueError("freeze manifest requires at least one artifact")

    artifacts.sort(key=lambda item: item["path"])
    artifact_set_sha = "sha256:" + sha256_text(canonical_json(artifacts))

    identity_payload = {
        "manifest_version": MANIFEST_VERSION,
        "protocol_id": "AR-P003",
        "protocol_version": protocol_version,
        "protocol_sha256": protocol_sha,
        "artifacts": artifacts,
    }
    freeze_content_id = "sha256:" + sha256_text(
        canonical_json(identity_payload)
    )

    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )

    return {
        "manifest_version": MANIFEST_VERSION,
        "protocol_id": "AR-P003",
        "protocol_version": protocol_version,
        "protocol_frozen": protocol_frozen,
        "protocol_path": protocol_relative,
        "protocol_sha256": protocol_sha,
        "generated_at": timestamp,
        "hash_algorithm": "sha256",
        "artifact_set_sha256": artifact_set_sha,
        "freeze_content_id": freeze_content_id,
        "artifacts": artifacts,
    }


def validate_manifest(manifest: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )
    output: list[str] = []
    for error in sorted(
        validator.iter_errors(manifest),
        key=lambda item: list(item.absolute_path),
    ):
        path = "$"
        for part in error.absolute_path:
            path += f"[{part}]" if isinstance(part, int) else f".{part}"
        output.append(f"{path}: {error.message}")
    return output


def run_self_test() -> int:
    schema = load_json(MANIFEST_SCHEMA)
    Draft202012Validator.check_schema(schema)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        protocol = root / "protocol.json"
        protocol.write_text(
            json.dumps(
                {
                    "protocol_id": "AR-P003",
                    "version": "v0.3-test",
                    "frozen": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        sample = root / "sample.txt"
        sample.write_bytes(b"abc")

        manifest = make_manifest(
            [sample],
            root,
            protocol_path=protocol,
            generated_at="2026-09-19T12:00:00Z",
        )
        errors = validate_manifest(manifest, schema)
        assert not errors, errors

        entry = manifest["artifacts"][0]
        assert entry["path"] == "sample.txt"
        assert entry["bytes"] == 3
        assert (
            entry["sha256"]
            == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )
        assert manifest["protocol_version"] == "v0.3-test"
        assert manifest["protocol_frozen"] is False
        assert manifest["protocol_path"] == "protocol.json"
        assert manifest["protocol_sha256"] == "sha256:" + sha256_file(protocol)

        # generated_at is excluded from the deterministic freeze content ID.
        later = make_manifest(
            [sample],
            root,
            protocol_path=protocol,
            generated_at="2026-09-19T13:00:00Z",
        )
        assert manifest["freeze_content_id"] == later["freeze_content_id"]
        assert manifest["artifact_set_sha256"] == later["artifact_set_sha256"]

        # Changing artifact bytes changes both artifact-set and freeze IDs.
        sample.write_bytes(b"abcd")
        changed_artifact = make_manifest(
            [sample],
            root,
            protocol_path=protocol,
            generated_at="2026-09-19T12:00:00Z",
        )
        assert (
            changed_artifact["artifact_set_sha256"]
            != manifest["artifact_set_sha256"]
        )
        assert (
            changed_artifact["freeze_content_id"]
            != manifest["freeze_content_id"]
        )

        # Protocol version/content drift is bound into the freeze content ID.
        sample.write_bytes(b"abc")
        protocol_doc = load_json(protocol)
        protocol_doc["version"] = "v0.3-test-2"
        protocol.write_text(
            json.dumps(protocol_doc, indent=2) + "\n",
            encoding="utf-8",
        )
        changed_protocol = make_manifest(
            [sample],
            root,
            protocol_path=protocol,
            generated_at="2026-09-19T12:00:00Z",
        )
        assert changed_protocol["protocol_version"] == "v0.3-test-2"
        assert (
            changed_protocol["freeze_content_id"]
            != manifest["freeze_content_id"]
        )

        # A final-freeze invocation must fail while protocol.frozen=false.
        try:
            make_manifest(
                [sample],
                root,
                protocol_path=protocol,
                require_protocol_frozen=True,
            )
        except ValueError as exc:
            assert "frozen=false" in str(exc)
        else:
            raise AssertionError("unfrozen protocol accepted for final freeze")

        protocol_doc["frozen"] = True
        protocol.write_text(
            json.dumps(protocol_doc, indent=2) + "\n",
            encoding="utf-8",
        )
        final_manifest = make_manifest(
            [sample],
            root,
            protocol_path=protocol,
            generated_at="2026-09-19T14:00:00Z",
            require_protocol_frozen=True,
        )
        assert final_manifest["protocol_frozen"] is True
        assert not validate_manifest(final_manifest, schema)

        try:
            make_manifest(
                [sample, sample],
                root,
                protocol_path=protocol,
            )
        except ValueError as exc:
            assert "duplicate artifact" in str(exc)
        else:
            raise AssertionError("duplicate manifest artifact was accepted")

    print(
        "AR-P003 freeze-manifest v0.2 self-test passed: protocol version/hash "
        "binding, deterministic content ID, artifact drift, duplicate rejection, "
        "and final-freeze frozen-protocol gate."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a content-bound SHA-256 manifest for AR-P003 artifacts."
    )
    parser.add_argument("files", nargs="*", help="Files to include in the manifest")
    parser.add_argument(
        "--root",
        default=".",
        help="Root used for relative manifest paths (default: repository cwd)",
    )
    parser.add_argument(
        "--protocol",
        default=str(DEFAULT_PROTOCOL),
        help="Protocol JSON to bind into the manifest.",
    )
    parser.add_argument(
        "--require-protocol-frozen",
        action="store_true",
        help="Fail unless the bound protocol declares frozen=true.",
    )
    parser.add_argument("--output", help="Write manifest JSON to this path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        try:
            return run_self_test()
        except (
            OSError,
            json.JSONDecodeError,
            SchemaError,
            AssertionError,
            ValueError,
        ) as exc:
            print(f"ERROR: freeze-manifest self-test failed: {exc}", file=sys.stderr)
            return 2

    if not args.files:
        parser.error("provide one or more files, or use --self-test")

    try:
        schema = load_json(MANIFEST_SCHEMA)
        Draft202012Validator.check_schema(schema)
        manifest = make_manifest(
            [Path(item) for item in args.files],
            Path(args.root),
            protocol_path=Path(args.protocol),
            require_protocol_frozen=args.require_protocol_frozen,
        )
        errors = validate_manifest(manifest, schema)
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2
    except (OSError, json.JSONDecodeError, SchemaError, ValueError) as exc:
        print(f"ERROR: unable to create freeze manifest: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
