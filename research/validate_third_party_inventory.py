#!/usr/bin/env python3
"""Deterministic completeness checks for the repository third-party inventory.

This does not validate legal compatibility. It detects drift between direct
Python requirements / GitHub Actions repositories and the documented inventory,
verifies the exact lock-package name snapshot, and guards the deliberate
Apache-2.0 repository-license state and its private/third-party boundaries.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research" / "third-party-inventory.json"
REQUIREMENTS = ROOT / "requirements.txt"
LOCK = ROOT / "requirements-lock.txt"
WORKFLOWS = [
    ROOT / ".github" / "workflows" / "validate-receipts.yml",
    ROOT / ".github" / "workflows" / "codeql.yml",
]
LICENSING_DOC = ROOT / "docs" / "LICENSING.md"
LICENSE_FILE = ROOT / "LICENSE"
NOTICE_FILE = ROOT / "NOTICE"


def requirement_name(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    match = re.match(r"^([A-Za-z0-9_.-]+)", line)
    return match.group(1).lower().replace("_", "-") if match else None


def workflow_repositories(text: str) -> set[str]:
    repos: set[str] = set()
    for match in re.finditer(r"^\s*uses:\s*([^@\s]+)@", text, flags=re.MULTILINE):
        target = match.group(1)
        parts = target.split("/")
        if len(parts) >= 2:
            repos.add("/".join(parts[:2]))
    return repos


def main() -> int:
    try:
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        requirements_text = REQUIREMENTS.read_text(encoding="utf-8")
        lock_text = LOCK.read_text(encoding="utf-8")
        workflow_text = "\n".join(path.read_text(encoding="utf-8") for path in WORKFLOWS)
        licensing_text = LICENSING_DOC.read_text(encoding="utf-8")
        license_text = LICENSE_FILE.read_text(encoding="utf-8")
        notice_text = NOTICE_FILE.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load license-preflight inputs: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    if inventory.get("repository_license_status") != "apache-2.0":
        errors.append("repository_license_status must remain apache-2.0 after the explicit 2026 owner licensing decision")

    direct_required = {name for line in requirements_text.splitlines() if (name := requirement_name(line))}
    direct_documented = {str(item.get("package", "")).lower().replace("_", "-") for item in inventory.get("direct_python_dependencies") or []}
    if direct_required != direct_documented:
        errors.append(f"direct requirement inventory differs: required_only={sorted(direct_required-direct_documented)!r}, inventory_only={sorted(direct_documented-direct_required)!r}")

    workflow_used = workflow_repositories(workflow_text)
    workflow_documented = {str(item.get("repository", "")) for item in inventory.get("github_actions") or []}
    if workflow_used != workflow_documented:
        errors.append(f"workflow Action inventory differs: used_only={sorted(workflow_used-workflow_documented)!r}, inventory_only={sorted(workflow_documented-workflow_used)!r}")

    lock_packages = {name for line in lock_text.splitlines() if (name := requirement_name(line))}
    snapshot_packages = {str(name).lower().replace("_", "-") for name in inventory.get("transitive_python_snapshot_packages") or []}
    if lock_packages != snapshot_packages:
        errors.append(f"transitive lock-package snapshot differs: lock_only={sorted(lock_packages-snapshot_packages)!r}, inventory_only={sorted(snapshot_packages-lock_packages)!r}")

    for section in ("direct_python_dependencies", "github_actions", "referenced_protocol_implementations"):
        for index, item in enumerate(inventory.get(section) or []):
            if item.get("vendored_source") is not False:
                errors.append(f"{section}[{index}] vendored_source must be explicitly false")
            if not item.get("observed_license"):
                errors.append(f"{section}[{index}] has no observed_license")
            if not item.get("upstream_repository") and section != "github_actions":
                errors.append(f"{section}[{index}] has no upstream_repository")

    if not license_text.lstrip().startswith("Apache License\n"):
        errors.append("top-level LICENSE does not start with the standard Apache License text")
    if "Version 2.0, January 2004" not in license_text or "END OF TERMS AND CONDITIONS" not in license_text:
        errors.append("top-level LICENSE appears incomplete or is not Apache-2.0")
    if "Copyright 2026 Blake Gaucher" not in notice_text:
        errors.append("NOTICE does not contain the owner copyright attribution")

    for phrase in (
        "licensed under the **Apache License 2.0**",
        "human-study or participant data",
        "Third-party material remains governed",
        "does not grant trademark rights",
    ):
        if phrase not in licensing_text:
            errors.append(f"docs/LICENSING.md missing required boundary phrase: {phrase!r}")

    if inventory.get("private_human_study_material_auto_released") is not False:
        errors.append("inventory must state that private human-study material is not auto-released")
    if inventory.get("third_party_terms_preserved") is not True:
        errors.append("inventory must preserve third-party terms")
    if inventory.get("trademark_rights_granted") is not False:
        errors.append("inventory must not claim trademark rights")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Third-party inventory preflight passed: direct requirements, workflow Action repositories, lock-package names, non-vendoring status, Apache-2.0 LICENSE/NOTICE state, and private/third-party boundaries are internally consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
