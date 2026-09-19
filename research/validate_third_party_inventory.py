#!/usr/bin/env python3
"""Deterministic completeness checks for the repository third-party inventory.

This does not validate legal compatibility. It only detects obvious drift between
the direct Python requirements / GitHub Actions repositories and the documented
inventory, and verifies the exact lock-package name snapshot remains listed.
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
        workflow_text = "\n".join(
            path.read_text(encoding="utf-8") for path in WORKFLOWS
        )
        licensing_text = LICENSING_DOC.read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to load license-preflight inputs: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []

    if inventory.get("repository_license_status") != "not_selected":
        errors.append(
            "repository_license_status changed; owner license choice must be "
            "handled as an explicit governance update"
        )

    direct_required = {
        name
        for line in requirements_text.splitlines()
        if (name := requirement_name(line))
    }
    direct_documented = {
        str(item.get("package", "")).lower().replace("_", "-")
        for item in inventory.get("direct_python_dependencies") or []
    }
    missing_direct = sorted(direct_required - direct_documented)
    extra_direct = sorted(direct_documented - direct_required)
    if missing_direct:
        errors.append(f"direct requirement(s) missing from inventory: {missing_direct!r}")
    if extra_direct:
        errors.append(
            f"inventory marks non-direct package(s) as direct: {extra_direct!r}"
        )

    workflow_used = workflow_repositories(workflow_text)
    workflow_documented = {
        str(item.get("repository", ""))
        for item in inventory.get("github_actions") or []
    }
    missing_actions = sorted(workflow_used - workflow_documented)
    extra_actions = sorted(workflow_documented - workflow_used)
    if missing_actions:
        errors.append(f"GitHub Action repo(s) missing from inventory: {missing_actions!r}")
    if extra_actions:
        errors.append(
            f"inventory lists unused GitHub Action repo(s): {extra_actions!r}"
        )

    lock_packages = {
        name
        for line in lock_text.splitlines()
        if (name := requirement_name(line))
    }
    snapshot_packages = {
        str(name).lower().replace("_", "-")
        for name in inventory.get("transitive_python_snapshot_packages") or []
    }
    if lock_packages != snapshot_packages:
        errors.append(
            "transitive lock-package name snapshot differs from inventory: "
            f"lock_only={sorted(lock_packages - snapshot_packages)!r}, "
            f"inventory_only={sorted(snapshot_packages - lock_packages)!r}"
        )

    for section in (
        "direct_python_dependencies",
        "github_actions",
        "referenced_protocol_implementations",
    ):
        for index, item in enumerate(inventory.get(section) or []):
            if item.get("vendored_source") is not False:
                errors.append(
                    f"{section}[{index}] vendored_source must be explicitly false "
                    "for the current inventory snapshot"
                )
            if not item.get("observed_license"):
                errors.append(f"{section}[{index}] has no observed_license")
            if not item.get("upstream_repository") and section != "github_actions":
                errors.append(f"{section}[{index}] has no upstream_repository")

    if "does not currently include an explicit open-source license" not in licensing_text:
        errors.append(
            "docs/LICENSING.md no longer states the current no-license status; "
            "update inventory/validator deliberately if the owner selects terms"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "Third-party inventory preflight passed: direct requirements, workflow "
        "Action repositories, lock-package names, vendoring status, and current "
        "no-license boundary are internally consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
