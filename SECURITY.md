# Security Policy

AI Activity Receipt is an early-stage research repository. Security reports are useful, but the project should not be treated as a production security product or compliance control.

## Scope

Security-relevant reports can include issues in:

- parsers and validators;
- canonical-record / Receipt derivation;
- adapter input handling;
- path handling and local file packaging;
- offline AR-P003 runner data separation;
- research signing / verification prototypes;
- CI or reproducibility configuration.

The DSSE/Ed25519 code in this repository is explicitly a **research prototype using test-oriented trust material**, not a production key-management system.

## Sensitive reports

Do **not** place the following in a public issue:

- passwords, API keys, tokens, credentials, or private keys;
- identifiable human-participant data;
- reviewer response exports;
- hidden gold labels or private analysis bundles;
- private chain-of-thought;
- exploit material that would unnecessarily expose another system.

If GitHub private vulnerability reporting is available for this repository, use that path. Otherwise contact the repository owner through a private channel before sharing sensitive details.

For non-sensitive bugs and reproducibility mismatches, a normal GitHub issue is appropriate.

## Response expectations

This is an independently maintained research project, not a staffed security program. Reports will be evaluated as capacity allows. Acknowledgement of a report does not imply a production-security certification or compliance status.

## Supported versions

The repository currently develops one public candidate line plus separate versioned research profiles. Security fixes should target the current `main` branch unless a historical frozen artifact must remain unchanged for evidentiary reasons.

Frozen benchmark history should not be rewritten. If a historical artifact contains a security-relevant limitation, document the limitation and create a new versioned artifact when a change is required.


## Repository hardening status

Repository-file controls and remaining GitHub-admin gates are documented in [Repository Security Hardening](docs/SECURITY-HARDENING.md).

The repository now includes least-privilege/pinned primary CI, disabled checkout credential persistence, a finite CI timeout, stale-run cancellation, a deterministic security smoke test, weekly Dependabot version-update configuration, CODEOWNERS metadata, private-study ignore rules, and stricter offline-runner CSP/resource limits.

GitHub API inspection on 2026-09-19 returned no repository rulesets. Main-branch ruleset/protection, CodeQL default setup, private vulnerability reporting, and confirmation of Dependabot security alerts/security updates remain repository-admin settings and must not be described as enabled until verified.
