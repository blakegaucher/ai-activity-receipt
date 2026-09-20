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

GitHub **Private vulnerability reporting is enabled** for this repository. Use that path for sensitive vulnerability reports.

For non-sensitive bugs and reproducibility mismatches, a normal GitHub issue is appropriate.

## Response expectations

This is an independently maintained research project, not a staffed security program. Reports will be evaluated as capacity allows. Acknowledgement of a report does not imply a production-security certification or compliance status.

## Supported versions

The repository currently develops one public candidate line plus separate versioned research profiles. Security fixes should target the current `main` branch unless a historical frozen artifact must remain unchanged for evidentiary reasons.

Frozen benchmark history should not be rewritten. If a historical artifact contains a security-relevant limitation, document the limitation and create a new versioned artifact when a change is required.

## Repository hardening status

Repository controls are documented in [Repository Security Hardening](docs/SECURITY-HARDENING.md).

Verified repository/admin state on 2026-09-20 includes:

- active `Protect main` ruleset targeting `refs/heads/main`;
- pull requests required before merging;
- required GitHub Actions checks:
  - `Schema, invariant, and benchmark smoke tests`;
  - `Analyze python`;
  - `Analyze javascript-typescript`;
- branch deletion and force-push/non-fast-forward updates blocked;
- no bypass actors configured;
- private vulnerability reporting enabled;
- Dependabot alerts enabled;
- Dependabot security updates enabled;
- weekly Dependabot version updates retained from `.github/dependabot.yml`;
- code scanning enabled with CodeQL **Advanced Setup** retained for Python and JavaScript/TypeScript;
- secret scanning alerts enabled;
- secret protection and push protection enabled;
- repository Security policy and Security advisories enabled.

The CodeQL Advanced Setup workflow remains pinned and least-privilege. Default setup has **not** replaced it.

On 2026-09-20, two High CodeQL findings for clear-text logging of sensitive information were investigated separately and addressed through PR #72. The change sanitized input-derived policy diagnostics and source-controlled security-smoke diagnostics without weakening secret detection. The protected PR checks and the post-merge `main` validation/CodeQL runs completed successfully.

A successful CodeQL run means the configured analysis completed. It does **not** prove that no vulnerabilities remain. The connected repository tooling cannot read the authenticated CodeQL alert inventory, so the final open/closed state of those two dashboard alerts requires explicit GitHub Security UI verification before it is recorded as closed.

## Evidence boundary

Repository security controls were hardened and the configured static-analysis findings were addressed in code. This is not:

- a penetration test;
- an independent security audit;
- proof of vulnerability-free software;
- CodeQL or security certification;
- production key-management validation;
- standards certification;
- legal or regulatory compliance;
- production-security readiness.
