# AI Activity Receipt — Security Continuity Update

> **Snapshot date:** 2026-09-20  
> **Type:** Additive security/governance continuity update  
> **Supersedes:** security/admin state only where this document is newer than `PROJECT-CONTINUITY-2026-09-20.md`  
> Historical benchmark evidence, AR-P003 claim gates, product maturity, and cross-project boundaries are unchanged.

## Lane → Status → Authority → Allowed next action → Protected boundary

**Lane:** AI Activity Receipt → repository security hardening.

**Status:** Main-branch protection is active; owner/admin security controls were verified; two High CodeQL sensitive-logging findings were investigated and remediated in code; protected PR and post-merge validation/CodeQL runs are green. Final CodeQL dashboard alert-state verification remains external to the connected repository tooling.

**Authority used:**

1. live GitHub `main`, ruleset, files, issue #37, pull request #72, Actions and CodeQL workflow runs;
2. owner/admin verification of repository Security settings;
3. the existing dated project continuity and frozen research evidence.

**Allowed next action:** verify the post-remediation CodeQL alert dashboard; then update/close issue #37 only if its remaining acceptance conditions are genuinely satisfied.

**Protected boundary:** do not weaken `Protect main`, CodeQL Advanced Setup, Dependabot/secret scanning, validation semantics, or tracked-secret detection; do not rewrite frozen evidence; do not convert repository hardening into claims of production security or vulnerability-free software.

## 1. Main protection verified

Repository ruleset:

`Protect main`

Ruleset ID:

`23740042`

Verified live state:

- enforcement: active;
- target: `refs/heads/main`;
- bypass actors: none;
- pull request required before merge;
- required approving reviews: 0;
- no Code Owner review requirement;
- no most-recent-push approval requirement;
- no extra approval for unattributed Copilot changes;
- required status checks:
  - `Schema, invariant, and benchmark smoke tests`;
  - `Analyze python`;
  - `Analyze javascript-typescript`;
- deletion blocked;
- non-fast-forward / force-push updates blocked.

The ruleset was not modified during CodeQL remediation.

## 2. Owner/admin security state verified

As of this update, verified repository/security state includes:

- Security policy enabled;
- Security advisories enabled;
- Private vulnerability reporting enabled;
- Dependabot alerts enabled;
- Dependabot security updates enabled;
- Dependabot version updates retained under the existing weekly configuration;
- code scanning alerts enabled;
- CodeQL Advanced Setup retained;
- secret scanning alerts enabled;
- secret protection enabled;
- push protection enabled.

The existing `.github/dependabot.yml` was intentionally left unchanged.

## 3. CodeQL state before remediation

GitHub Security showed:

- **2 open**;
- **0 closed**;
- both High severity;
- rule: **Clear-text logging of sensitive information**.

Locations:

- alert #2 — `research/validate_attestation_policy.py`;
- alert #1 — `research/security_smoke_test.py`.

These findings were not dismissed merely to clear the dashboard.

## 4. Alert #2 — attestation-policy diagnostics

Dataflow inspection found that malformed/adversarial policy documents could influence diagnostics reaching stderr.

Relevant pre-fix paths included:

- raw `jsonschema.ValidationError.message`;
- unknown role/payload values interpolated into semantic errors;
- raw schema/policy load exception text.

Because the policy schema includes identity, key ID, verification-material URI, notes and other potentially sensitive/identifying fields, raw input-derived error strings were treated as an avoidable disclosure surface.

Resolution:

- use whitelisted structural paths;
- use whitelisted validation-rule categories;
- stop echoing unknown role/payload values;
- replace raw load exception output with fixed categories;
- add synthetic sensitive-looking regression cases proving those values are not reproduced in rendered diagnostics.

Disposition: **code hardened; not dismissed as false positive**.

## 5. Alert #1 — security-smoke diagnostics

The tracked-secret scanner itself was already value-safe: it reports a fixed secret type/label and the relative tracked file path, not the matched secret.

The surrounding generic error sink nevertheless also received source-controlled strings from other checks, including Action names/references and permission-line content.

Resolution:

- preserve all high-confidence secret detection patterns;
- preserve label + relative-path scanner diagnostics;
- remove unnecessary raw source-controlled Action/permission/timeout echoes;
- retain structural context with fixed categories/line location;
- add a synthetic token-looking Action-name regression case and require that the diagnostic does not echo it.

Disposition: **code hardened; scanner not weakened; no CodeQL suppression**.

## 6. Pull request and validation evidence

Remediation branch:

`codeql-sensitive-diagnostics-hardening`

Final branch head:

`f98a7a6da2588b422eabea5786264f5e2890001e`

Pull request:

`#72 — Harden diagnostics for CodeQL sensitive-logging findings`

Final PR required checks:

- validation run #155 / run ID `35542400831`: success;
- CodeQL run #72 / run ID `35542400728`:
  - `Analyze python`: success;
  - `Analyze javascript-typescript`: success.

PR #72 merged normally through protected `main` as:

`4788dc4f39a19b01e68e89c2f39a7e7c6dce7fb4`

Post-merge `main` evidence:

- validation run #156 / run ID `35542529916`: success;
- CodeQL run #73 / run ID `35542529937`:
  - `Analyze python`: success;
  - `Analyze javascript-typescript`: success.

No protection rule or required check was bypassed.

## 7. Alert inventory boundary

The connected GitHub tooling can verify CodeQL workflow execution and successful SARIF upload, but it does not expose the authenticated code-scanning alert inventory endpoint.

Therefore this update does **not** claim that the dashboard now shows zero open alerts.

Remaining verification:

1. open GitHub **Security → Code scanning**;
2. filter `is:open branch:main`;
3. confirm the current state of alerts #1 and #2 after CodeQL run #73;
4. record the result on issue #37.

If the alerts are absent/closed by the new analysis, record that exact result. If either remains open, inspect the new dataflow before any dismissal or further change.

## 8. Evidence boundaries unchanged

This work supports the statement:

> Repository security controls were hardened and the configured static-analysis findings were addressed in code.

It does not support:

- vulnerability-free software;
- penetration-test coverage;
- independent security audit;
- production security;
- security certification;
- standards certification;
- legal/regulatory compliance;
- commercial readiness;
- customer validation.

Frozen AR-P003 v0.2.3 evidence, AR-P003 v0.3 human-study status, business evidence, and ARC/Julia/DGAP lane boundaries are unchanged.


## 9. Repository-admin issue disposition

Issue #36 — `Repository admin: protect main with required validation and CodeQL checks` — was closed as completed on 2026-09-20 after the newer verified state above satisfied its acceptance conditions.

The closure does **not** collapse the remaining security evidence into that issue. Issue #37 stays open for the post-remediation CodeQL alert-dashboard check and owner security-alert notification verification if still outstanding.

No security control was weakened for the closure, and no zero-alert state was inferred from green CodeQL execution.


## 10. Authenticated CodeQL inventory superseding update — alert #1 remains open

Newer authenticated owner evidence from GitHub Security supersedes the earlier inventory-pending wording for the actual alert state.

Filter:

`is:open branch:main`

Verified result before the second remediation attempt:

- open: **1**;
- closed: **1**;
- remaining open original alert: **#1**;
- rule: **Clear-text logging of sensitive information**;
- severity: **High**;
- file: `research/security_smoke_test.py`;
- alert #2 is closed.

This creates an explicit source conflict with older implementation-status prose that described both findings as remediated in code. Preserve both facts:

- PR #72 and later green CodeQL runs are valid historical remediation/execution evidence;
- the authenticated alert inventory is the authority for whether an original alert is actually still open.

### Allowed action taken

A fresh narrow branch was created:

`codeql-alert-1-detection-state-separation`

First code commit:

`8b387a314500c1436dded92832cc8084229470e7`

The remaining tracked-secret path was refactored so repository text influences only a fixed detection-state bitmask. Scanned text, regex matches, and dynamic paths are not returned to the diagnostic layer. The generic stderr sink receives only fixed allowlisted secret-category messages for this scanner.

Synthetic regression coverage requires detection to remain active while preventing the synthetic secret, arbitrary source text, and dynamic source filename from appearing in diagnostics.

### Current protected boundary

Issue #37 remains open.

Do not infer closure from green CodeQL runs. After this branch is merged through protected `main`, the owner must re-check authenticated Code scanning with `is:open branch:main` and record the exact resulting inventory.

Owner Security-alert notification confirmation remains an independent acceptance item.


## 11. CodeQL source-model refinement after PR #75

PR #75 — `Separate secret detection state from diagnostics for CodeQL alert #1` — merged through protected `main` as:

`b8e10da52be098fe7bf2b68e065e7fae5dcb6263`

Post-merge execution evidence:

- validation run #162: success;
- CodeQL run #79:
  - Analyze python: success;
  - Analyze javascript-typescript: success.

Those green runs are execution evidence only. The authenticated post-PR-#75 alert inventory has not yet been supplied, so no zero-alert state is inferred.

### Upstream CodeQL source-model evidence

A follow-up inspection of the upstream Python CodeQL implementation identified a more precise source-model reason the generic stderr sink can remain reportable even after matched repository text and dynamic paths are removed from the diagnostic payload.

The Python sensitive-data model considers the right-hand-side expression of an assignment to a **sensitive-looking variable name** to be a sensitive source. It also considers sensitive-looking function names and string literals when building sensitive-data sources.

Relevant upstream model behavior is in:

- `python/ql/lib/semmle/python/dataflow/new/SensitiveDataSources.qll`;
- `shared/concepts/codeql/concepts/internal/SensitiveDataHeuristics.qll`;
- `python/ql/lib/semmle/python/security/dataflow/CleartextLoggingCustomizations.qll`.

On the PR #75 `main` state, diagnostic-side names/literals such as `SAFE_SECRET_DIAGNOSTICS` and `secret_diagnostic_regression_errors` still contain the heuristic term `secret`.

The direct source-model path is therefore:

```text
RHS assigned to SAFE_SECRET_DIAGNOSTICS
→ CodeQL SensitiveVariableAssignment source
→ .items()
→ fixed diagnostic message
→ errors.append(...)
→ generic print(..., file=sys.stderr) sink
```

A second potential modeled path exists through the sensitive-looking function name:

```text
secret_diagnostic_regression_errors()
→ CodeQL sensitive function-name source
→ returned error list
→ errors.extend(...)
→ generic stderr sink
```

This is distinct from the original runtime-data concern. The scanner can be runtime-value-safe and still match CodeQL's heuristic source model because the diagnostic identifiers themselves look sensitive to the query.

### Narrow follow-up

Fresh branch from post-PR-#75 `main`:

`codeql-alert-1-heuristic-source-hardening`

The follow-up preserves `HIGH_CONFIDENCE_SECRET_PATTERNS`, repository-wide tracked-text scanning, and failure semantics while:

- removing sensitive-looking names from the diagnostic-side state/rendering path;
- replacing printable category text with neutral fixed category identifiers;
- keeping scanned text and dynamic paths out of the rendered diagnostic;
- capturing the actual generic stderr renderer in the regression test and asserting that the synthetic probe value, arbitrary source text, and dynamic filename are absent.

The authenticated CodeQL inventory remains the authority for final alert state. Issue #37 must remain open until that inventory and the owner Security-alert notification setting are both independently verified.
