#!/usr/bin/env python3
"""Deterministic repository security smoke checks.

These checks protect repository hygiene and CI/offline-runner boundaries only.
They are not a vulnerability scanner or production security audit.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


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

SECRET_PATTERN_BITS = {
    "private_key_pem": 1 << 0,
    "github_classic_token": 1 << 1,
    "github_fine_grained_token": 1 << 2,
    "openai_style_secret_key": 1 << 3,
}

HIGH_CONFIDENCE_SECRET_PATTERNS = [
    (
        "private_key_pem",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
    ("github_classic_token", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b")),
    (
        "github_fine_grained_token",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    ),
    (
        "openai_style_secret_key",
        re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    ),
]

SAFE_SECRET_DIAGNOSTICS = {
    SECRET_PATTERN_BITS["private_key_pem"]:
        "tracked text contains a private-key PEM marker",
    SECRET_PATTERN_BITS["github_classic_token"]:
        "tracked text contains a GitHub classic-token marker",
    SECRET_PATTERN_BITS["github_fine_grained_token"]:
        "tracked text contains a GitHub fine-grained-token marker",
    SECRET_PATTERN_BITS["openai_style_secret_key"]:
        "tracked text contains an OpenAI-style secret-key marker",
}


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
            line_number = workflow.count("\n", 0, match.start()) + 1
            errors.append(
                f"external Action entry at line {line_number} is not pinned "
                "to a 40-hex commit SHA"
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


def tracked_secret_detection_mask(root: Path = ROOT) -> int:
    """Return only fixed detection-state bits, never scanned text or paths."""
    detected = 0
    skip_parts = {".git", ".venv", "venv", "__pycache__"}
    for path in root.rglob("*"):
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
        for pattern_id, pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
            if pattern.search(text):
                detected |= SECRET_PATTERN_BITS[pattern_id]
    return detected


def append_safe_secret_diagnostics(errors: list[str], detection_mask: int) -> None:
    """Render only allowlisted fixed diagnostics from a detection bitmask."""
    for bit, message in SAFE_SECRET_DIAGNOSTICS.items():
        if detection_mask & bit:
            errors.append(message)


def secret_diagnostic_regression_errors() -> list[str]:
    """Prove synthetic secret/source text never reaches rendered diagnostics."""
    errors: list[str] = []
    synthetic_sensitive = "ghp_" + ("A" * 36)
    arbitrary_source_text = "ARBITRARY_SOURCE_TEXT_MUST_NOT_BE_ECHOED"

    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        dynamic_name = "source-controlled-name-must-not-be-echoed.txt"
        test_path = temp_root / dynamic_name
        test_path.write_text(
            synthetic_sensitive + "\n" + arbitrary_source_text + "\n",
            encoding="utf-8",
        )

        detection_mask = tracked_secret_detection_mask(temp_root)
        expected_bit = SECRET_PATTERN_BITS["github_classic_token"]
        if not detection_mask & expected_bit:
            errors.append(
                "secret diagnostic regression test did not detect the synthetic "
                "GitHub classic-token marker"
            )

        rendered: list[str] = []
        append_safe_secret_diagnostics(rendered, detection_mask)
        if not rendered:
            errors.append(
                "secret diagnostic regression test produced no safe diagnostic "
                "for a detected synthetic secret"
            )

        diagnostic_text = "\n".join(rendered)
        for prohibited_value in (
            synthetic_sensitive,
            arbitrary_source_text,
            dynamic_name,
        ):
            if prohibited_value in diagnostic_text:
                errors.append(
                    "secret diagnostic regression test echoed scanned source data"
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
                    "workflow timeout exceeds 30-minute guardrail"
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
            "CodeQL workflow has unexpected write permission entries"
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

    secret_detection_mask = tracked_secret_detection_mask()
    append_safe_secret_diagnostics(errors, secret_detection_mask)
    errors.extend(secret_diagnostic_regression_errors())

    synthetic_sensitive = "ghp_" + ("A" * 36)
    synthetic_workflow = (
        "steps:\n"
        "  - name: synthetic\n"
        f"    uses: owner/{synthetic_sensitive}@main\n"
    )
    synthetic_errors = external_action_errors(synthetic_workflow)
    if not synthetic_errors:
        errors.append(
            "security diagnostic regression test did not detect an unpinned "
            "external Action"
        )
    elif any(synthetic_sensitive in error for error in synthetic_errors):
        errors.append(
            "security diagnostic regression test echoed a sensitive-looking "
            "source-controlled value"
        )

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
