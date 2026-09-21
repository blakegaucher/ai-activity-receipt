# Repository Security Hardening

> **Status:** Repository-level defense-in-depth for an early-stage research project.  
> **Verified state date:** 2026-09-20  
> These controls do not make AI Activity Receipt a production security product, compliance control, or certified secure implementation.

## Threats this repository can realistically reduce

The public repository can reduce risk from:

- accidental credential or private-key commits;
- overly broad GitHub Actions permissions;
- mutable third-party Action tags;
- CI credential persistence after checkout;
- unbounded reviewer-bundle inputs in the offline AR-P003 runner;
- unintended network access from the offline runner;
- accidental reviewer/gold-analysis data mixing;
- stale Python or GitHub Actions dependencies;
- direct or unreviewed changes to protected `main`;
- avoidable clear-text diagnostic exposure from malformed/adversarial inputs.

It cannot, by repository configuration alone, establish the truth of captured AI activity, protect production signing keys, authenticate external evidence, or secure a deployment that does not yet exist.

## Implemented repository controls

### Protected main branch

The repository ruleset `Protect main` is active and targets `refs/heads/main`.

Verified rules:

- pull request required before merge;
- required approving reviews: 0;
- no Code Owner approval requirement;
- no most-recent-push approval requirement;
- no extra approval for unattributed Copilot PRs;
- required status checks:
  - `Schema, invariant, and benchmark smoke tests`;
  - `Analyze python`;
  - `Analyze javascript-typescript`;
- branch deletion blocked;
- non-fast-forward / force-push updates blocked;
- bypass actors: none.

The ruleset is intentionally not weakened to simplify development.

### GitHub Actions

The primary validation workflow:

- grants the workflow token only `contents: read`;
- pins external Actions to full commit SHAs;
- disables checkout credential persistence;
- has a finite job timeout;
- cancels obsolete in-progress runs for the same branch/ref;
- installs the exact tested dependency snapshot;
- runs deterministic schema/invariant/benchmark checks;
- runs a repository security smoke test;
- uploads the aggregate reproducibility report.

### CodeQL Advanced Setup

`.github/workflows/codeql.yml` remains the repository's CodeQL **Advanced Setup** for:

- Python;
- JavaScript/TypeScript.

The workflow:

- uses immutable Action commit pins;
- disables checkout credential persistence;
- grants only `contents: read` plus the CodeQL-required `security-events: write`;
- runs on pull requests, pushes to `main`, schedule, and manual dispatch.

Do not enable CodeQL default setup on top of this workflow unless there is a deliberate migration away from Advanced Setup.

### 2026-09-20 CodeQL diagnostic hardening

Before the change, GitHub Security showed two open High findings on `main`, both under **Clear-text logging of sensitive information**:

- alert #2 — `research/validate_attestation_policy.py`;
- alert #1 — `research/security_smoke_test.py`.

They were investigated separately.

#### Attestation-policy validator

The policy CLI accepts malformed/adversarial policy/schema inputs. Its earlier structural diagnostics used raw `jsonschema.ValidationError.message`, and several semantic diagnostics reproduced unknown role/payload values. Those paths could carry input-derived values into stderr.

PR #72 changed that path to:

- emit a whitelisted structural location and validator category instead of raw `ValidationError.message`;
- avoid echoing unknown role/payload values;
- use fixed load-error categories rather than raw exception text;
- test that synthetic sensitive-looking input is absent from rendered diagnostics.

This was treated as a real diagnostic-exposure hardening issue, not dismissed as a false positive.

#### Repository security smoke test

The high-confidence tracked-secret scanner already reported only:

- fixed secret type/label;
- tracked relative file path.

It did **not** append the matched secret value.

The same generic stderr sink, however, also received other source-controlled workflow fragments such as Action names and unexpected permission lines. PR #72 removed those unnecessary raw echoes while preserving secret detection and useful structural context. A regression test now injects a synthetic sensitive-looking source-controlled Action name and requires the diagnostic not to reproduce it.

This was fixed conservatively rather than weakening or deleting the scanner.

#### Verification

PR #72 merged as commit:

`4788dc4f39a19b01e68e89c2f39a7e7c6dce7fb4`

Required protected-branch checks passed on the final PR head:

- `Schema, invariant, and benchmark smoke tests`;
- `Analyze python`;
- `Analyze javascript-typescript`.

Post-merge `main` runs also completed successfully for the validation workflow and both CodeQL language jobs.

The connected repository tooling does not expose the authenticated CodeQL alert list. Therefore successful SARIF upload and green jobs are recorded as execution evidence, but the dashboard alert count is not inferred. The two alerts require final GitHub Security UI verification before issue #37 can be closed.

### Dependency maintenance

`.github/dependabot.yml` remains unchanged:

- pip: weekly Monday 06:00 `America/Toronto`;
- GitHub Actions: weekly Monday 06:15 `America/Toronto`;
- open PR limit: 5;
- grouped version updates;
- commit prefix: `deps`.

Dependabot alerts and Dependabot security updates are enabled. Grouped security updates remain off because no concrete need to alter that setting was established.

### Secret scanning / vulnerability reporting

Verified owner/admin state includes:

- Private vulnerability reporting enabled;
- Security advisories enabled;
- Secret scanning alerts enabled;
- secret protection enabled;
- push protection enabled.

The repository security smoke test remains a narrow deterministic supplement, not a replacement for GitHub secret scanning.

### Ownership metadata

`.github/CODEOWNERS` names the repository owner for all files and repeats ownership for security/evidence-sensitive paths.

The current ruleset does not require Code Owner review. CODEOWNERS therefore remains routing/ownership metadata rather than an approval gate.

### Offline AR-P003 runner

The development runner uses a strict CSP and explicit local resource limits. Reviewer bundle/response/analysis schemas have bounded case, event, evidence, label, option, and content sizes.

These are defensive resource limits for a local development runner; they are not a browser sandbox guarantee.

## Remaining admin verification

The owner/admin configuration work is materially complete.

One evidence item remains deliberately open in repository documentation:

- verify the post-remediation CodeQL dashboard state for alerts #1 and #2 after the successful `main` CodeQL run.

If owner security-alert notification delivery has not already been explicitly checked, record that separately; do not infer it from the other enabled settings.

## Human-study data boundary

Do not commit:

- identifiable participant information;
- reviewer response exports;
- hidden analysis/gold bundles;
- recruitment/contact lists;
- consent records;
- secrets or credentials;
- private chain-of-thought.

The AR-P003 development runner remains unfrozen. Security hardening must not be used to imply ethics approval, participant-data readiness, or a completed human study.

## Incident handling

Use GitHub Private vulnerability reporting for sensitive repository vulnerability reports.

Non-sensitive reproducibility or correctness bugs may use normal GitHub issues.

## Evidence boundary

Repository security controls were hardened and the configured static-analysis findings were addressed in code. Green CI and CodeQL execution are not:

- penetration testing;
- an independent security audit;
- proof that no vulnerabilities remain;
- CodeQL certification;
- supply-chain certification;
- production key-management validation;
- legal or regulatory compliance.


## 2026-09-20 authenticated CodeQL inventory correction and alert #1 second remediation

Newer authenticated owner evidence from **Security → Code scanning**, filtered with `is:open branch:main`, supersedes the earlier pending inventory wording.

Verified inventory before this second remediation:

- **1 open**;
- **1 closed**;
- remaining open finding: alert **#1**, High, **Clear-text logging of sensitive information**;
- file: `research/security_smoke_test.py`;
- GitHub showed the generic stderr sink around the former line ~290;
- alert #2 in `research/validate_attestation_policy.py` is closed.

This conflicts with any earlier prose that could be read as implying both original findings were already closed. The earlier remediation work remains historical implementation evidence; the authenticated dashboard is the authority for actual alert state.

### Remaining alert #1 dataflow

Current source inspection identified the remaining secret-dependent path as:

```text
tracked repository text
→ path.read_text(...)
→ pattern.search(text)
→ tracked_secret_errors() creates a diagnostic after a secret-pattern match
→ errors.extend(...)
→ generic stderr loop
```

The previous implementation did not echo the matched secret bytes, but it still coupled secret detection with construction of a diagnostic carrying fixed pattern-label text and a dynamic repository path before returning that string into the generic error sink.

### Second remediation principle

Branch:

`codeql-alert-1-detection-state-separation`

First code commit:

`8b387a314500c1436dded92832cc8084229470e7`

The scanner now returns only a fixed integer **detection-state bitmask**. It does not return scanned text, match objects, or scanned paths.

User-facing diagnostics are generated separately from a fixed allowlist keyed by those bits.

The high-confidence patterns, repository-wide tracked-text scan, and failure semantics are preserved.

Synthetic regression coverage now requires:

- a constructed GitHub-token-looking value to be detected;
- a safe failure diagnostic to be produced;
- the exact synthetic value not to appear in diagnostics;
- arbitrary scanned source text not to appear;
- the dynamic source filename not to appear.

This is a code-remediation attempt only. Alert #1 remains open until authenticated post-merge CodeQL inventory evidence shows otherwise.

### Acceptance boundary

Do not close issue #37 until both conditions are independently verified:

1. no unresolved original CodeQL alert remains on `main`;
2. the repository owner's Security-alert notification setting/delivery is confirmed.

Green CodeQL workflow execution alone is not evidence of a zero-alert inventory.


### Alert #1 heuristic-source follow-up after PR #75

PR #75 merged as `b8e10da52be098fe7bf2b68e065e7fae5dcb6263` and post-merge validation run #162 plus CodeQL run #79 succeeded.

A subsequent review of the upstream Python CodeQL query implementation found that the clear-text logging query does not rely only on runtime secret bytes. Its sensitive-data model also heuristically marks values assigned to names containing `secret`, and it models sensitive-looking function names and string literals.

That matters because PR #75 still used diagnostic-side identifiers such as `SAFE_SECRET_DIAGNOSTICS` and `secret_diagnostic_regression_errors`. The fixed allowlisted strings were runtime-safe, but the **right-hand side assigned to a sensitive-looking variable name** can itself be modeled as a sensitive source and then flow through the generic `errors` list to stderr.

Fresh follow-up branch:

`codeql-alert-1-heuristic-source-hardening`

The follow-up keeps `HIGH_CONFIDENCE_SECRET_PATTERNS` and the repository-wide scan unchanged, but removes heuristic-sensitive naming and wording from the printable diagnostic path. It also routes the synthetic probe through the real generic stderr renderer using an in-memory capture and asserts that the probe value, arbitrary scanned text, and dynamic filename are absent.

This is a source-model hardening refinement. It is not a dismissal, CodeQL suppression, reduction in scanner coverage, or claim that the authenticated dashboard is already clear.
