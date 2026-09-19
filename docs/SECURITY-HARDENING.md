# Repository Security Hardening

> **Status:** Repository-level defense-in-depth for an early-stage research project.  
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
- direct changes to sensitive files without an explicit reviewer/owner signal.

It cannot, by repository configuration alone, establish the truth of captured AI activity, protect production signing keys, authenticate external evidence, or secure a deployment that does not yet exist.

## Implemented repository controls

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

GitHub documents least-privilege `GITHUB_TOKEN` permissions and full-SHA Action pinning as workflow-hardening practices.

### Dependency maintenance

`.github/dependabot.yml` schedules weekly grouped update checks for:

- Python/pip dependency files;
- GitHub Actions references.

Dependabot-generated changes still require normal test/review discipline. An automated update PR is not evidence that the new dependency set is safe.

### Ownership metadata

`.github/CODEOWNERS` names the repository owner for all files and repeats ownership for security/evidence-sensitive paths.

CODEOWNERS is reviewer-routing metadata. It does **not** enforce approval unless repository branch/ruleset settings require code-owner review.

### Offline AR-P003 runner

The development runner now uses a stricter CSP and explicit local resource limits.

The reviewer bundle/response/analysis schemas also have bounded case, event, evidence, label, option, and content sizes.

These are defensive resource limits for a local development runner; they are not a browser sandbox guarantee.

### Secret/private-key smoke checks

The repository security smoke test rejects high-confidence private-key/token markers in tracked text files and checks the expected private-study `.gitignore` protections.

This is a narrow deterministic guard, not a substitute for GitHub secret scanning or a dedicated secrets scanner.

## Manual GitHub settings still required

Repository files cannot themselves enable every GitHub security feature.

Current API inspection found no repository rulesets on `main`. The GitHub connector used for this work also cannot change branch-protection/ruleset or Advanced Security settings.

Repository administration should therefore separately evaluate and enable:

1. a `main` ruleset/branch protection requiring pull requests and the validation status check, while blocking force-pushes and branch deletion;
2. CodeQL default setup for the public Python/JavaScript codebase;
3. private vulnerability reporting;
4. Dependabot security alerts/security updates if they are not already enabled;
5. security-alert notifications for the repository owner.

GitHub currently recommends default CodeQL setup for eligible repositories and supports private vulnerability reporting for public repositories.

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

When a vulnerability is sensitive, use GitHub private vulnerability reporting if the repository administrator has enabled it. Otherwise establish a private contact channel before sharing exploit details.

Non-sensitive reproducibility or correctness bugs may use normal GitHub issues.

## Evidence boundary

A green CI/security smoke test means only that the checked repository controls behaved as encoded at that commit. It is not:

- penetration testing;
- an independent security audit;
- CodeQL certification;
- supply-chain certification;
- production key-management validation;
- legal or regulatory compliance.
