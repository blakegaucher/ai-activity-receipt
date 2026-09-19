#!/usr/bin/env python3
"""Deterministic repository security smoke checks.

These checks protect repository hygiene and CI/offline-runner boundaries only.
They are not a vulnerability scanner or production security audit.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "validate-receipts.yml"
CODEQL_WORKFLOW = ROOT / ".github" / "workflows" / "codeql.yml"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
SECURITY = ROOT / "SECURITY.md"
GITIGNORE = ROOT / ".gitignore"
RUNNER = ROOT / "benchmark" / "arp003_v0_3" / "offline_runner.html"

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".json",
    ".yml",
    ".yaml",
    ".html",
    ".txt",
    ".cff",
}

HIGH_CONFIDENCE_SECRET_PATTERNS = [
    (
        "private-key PEM block",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
    ("GitHub classic token", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    ("OpenAI-style secret key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def external_action_errors(workflow: str) -> list[str]:
    errors: list[str] = []
    action_re = re.compile(
        r"^\s*uses:\s*([^@\s]+)@([^\s#]+)",
        re.MULTILINE,
    )
    for match in action_re.finditer(workflow):
        action, ref = match.groups()
        if action.startswith("./"):
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            errors.append(
                f"external Action {action!r} is not pinned to a 40-hex commit SHA"
            )
    return errors


def checkout_hardening_errors(workflow: str) -> list[str]:
    lines = workflow.splitlines()
    errors: list[str] = []
    found_checkout = False
    for index, line in enumerate(lines):
        if re.search(r"uses:\s*actions/checkout@[0-9a-f]{40}", line):
            found_checkout = True
            block = "\n".join(lines[index : index + 8])
            if "persist-credentials: false" not in block:
                errors.append(
                    "actions/checkout must set persist-credentials: false"
                )
    if not found_checkout:
        errors.append("primary validation workflow has no pinned actions/checkout step")
    return errors


def tracked_secret_errors() -> list[str]:
    errors: list[str] = []
    skip_parts = {".git", ".venv", "venv", "__pycache__"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in skip_parts for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(
                    f"{label} marker found in tracked text path "
                    f"{path.relative_to(ROOT)}"
                )
    return errors


def main() -> int:
    errors: list[str] = []

    required_paths = [
        WORKFLOW,
        CODEQL_WORKFLOW,
        DEPENDABOT,
        CODEOWNERS,
        SECURITY,
        GITIGNORE,
        RUNNER,
    ]
    for path in required_paths:
        if not path.is_file():
            errors.append(f"required security/governance file missing: {path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    workflow = read(WORKFLOW)
    if "pull_request_target:" in workflow:
        errors.append(
            "primary validation workflow must not use pull_request_target"
        )
    if not re.search(
        r"(?m)^permissions:\s*$\n\s+contents:\s+read\s*$",
        workflow,
    ):
        errors.append(
            "primary validation workflow must explicitly grant contents: read"
        )
    if re.search(r"(?m)^\s+[A-Za-z0-9_-]+:\s+write\s*$", workflow):
        errors.append(
            "primary validation workflow unexpectedly grants a write permission"
        )
    if "timeout-minutes:" not in workflow:
        errors.append("primary validation job must have a finite timeout")
    else:
        for raw in re.findall(r"timeout-minutes:\s*(\d+)", workflow):
            if int(raw) > 30:
                errors.append(
                    f"workflow timeout {raw} minutes exceeds 30-minute guardrail"
                )
    if "cancel-in-progress: true" not in workflow:
        errors.append(
            "primary validation workflow must cancel obsolete in-progress runs"
        )

    errors.extend(external_action_errors(workflow))
    errors.extend(checkout_hardening_errors(workflow))

    codeql = read(CODEQL_WORKFLOW)
    if "pull_request_target:" in codeql:
        errors.append("CodeQL workflow must not use pull_request_target")
    if not re.search(
        r"(?m)^permissions:\s*$\n\s+contents:\s+read\s*$\n\s+security-events:\s+write\s*$",
        codeql,
    ):
        errors.append(
            "CodeQL workflow must grant only contents: read and security-events: write"
        )
    unexpected_codeql_writes = [
        line.strip()
        for line in codeql.splitlines()
        if re.fullmatch(r"[A-Za-z0-9_-]+:\s+write", line.strip())
        and line.strip() != "security-events: write"
    ]
    if unexpected_codeql_writes:
        errors.append(
            "CodeQL workflow has unexpected write permissions: "
            + ", ".join(unexpected_codeql_writes)
        )
    for marker in ("python", "javascript-typescript"):
        if marker not in codeql:
            errors.append(f"CodeQL workflow missing language {marker!r}")
    if "github/codeql-action/init@" not in codeql:
        errors.append("CodeQL workflow has no init action")
    if "github/codeql-action/analyze@" not in codeql:
        errors.append("CodeQL workflow has no analyze action")
    if "timeout-minutes:" not in codeql:
        errors.append("CodeQL workflow must have a finite timeout")
    errors.extend(external_action_errors(codeql))
    errors.extend(checkout_hardening_errors(codeql))

    dependabot = read(DEPENDABOT)
    for required in (
        'package-ecosystem: "pip"',
        'package-ecosystem: "github-actions"',
        'interval: "weekly"',
    ):
        if required not in dependabot:
            errors.append(f"Dependabot config missing {required!r}")

    codeowners = read(CODEOWNERS)
    if "* @blakegaucher" not in codeowners:
        errors.append("CODEOWNERS has no default @blakegaucher owner")

    security = read(SECURITY).lower()
    if "private vulnerability reporting" not in security:
        errors.append(
            "SECURITY.md must explain the private vulnerability reporting path"
        )
    if "production security product" not in security:
        errors.append(
            "SECURITY.md must preserve the non-production evidence boundary"
        )

    gitignore = read(GITIGNORE)
    for required in (
        "benchmark/arp003_v0_3/private_study_data/",
        "benchmark/arp003_v0_3/**/*-responses.json",
        "benchmark/arp003_v0_3/**/analysis/runner-analysis.json",
    ):
        if required not in gitignore:
            errors.append(f".gitignore missing private-study guard {required!r}")

    runner = read(RUNNER)
    strict_csp_markers = (
        "default-src 'none'",
        "connect-src 'none'",
        "object-src 'none'",
        "frame-src 'none'",
        "worker-src 'none'",
        "base-uri 'none'",
        "form-action 'none'",
    )
    for marker in strict_csp_markers:
        if marker not in runner:
            errors.append(f"offline runner CSP missing {marker!r}")

    for marker in (
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "sendBeacon",
        "<script src=",
        "http://",
        "https://",
    ):
        if marker in runner:
            errors.append(
                f"offline runner contains network/external marker {marker!r}"
            )

    for marker in (
        "const MAX_BUNDLE_BYTES",
        "const MAX_CASES",
        "const MAX_ARTIFACT_CHARS",
        "file.size > MAX_BUNDLE_BYTES",
        "textContent = artifact.content",
    ):
        if marker not in runner:
            errors.append(
                f"offline runner missing defensive input/rendering marker {marker!r}"
            )

    errors.extend(tracked_secret_errors())

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        "Repository security smoke test passed: least-privilege/pinned primary "
        "CI, pinned CodeQL workflow, credential persistence guards, "
        "Dependabot/CODEOWNERS metadata, strict "
        "offline-runner boundaries, private-study ignore rules, and high-"
        "confidence secret markers are consistent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
