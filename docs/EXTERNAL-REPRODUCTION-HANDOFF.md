# Independent Reproduction Handoff

> **Status:** Public reviewer handoff for Phase 6 external reproducibility.  
> **Purpose:** Let an independent developer test whether the repository can be reproduced from public instructions alone.  
> A successful reproduction is evidence about repository reproducibility at one commit/environment, not human benefit, standards conformance, production security, or commercial value.

## Reviewer goal

Start from a clean checkout and determine whether the repository's documented deterministic/synthetic checks can be reproduced **without undocumented project knowledge**.

A useful result may be either:

- the suite reproduces successfully; or
- the reviewer finds a concrete mismatch, missing prerequisite, ambiguous instruction, platform problem, or hidden assumption.

Unfavorable reproduction findings must be preserved.

## Minimal clean-room procedure

Use a fresh environment that has ordinary Git and Python tooling.

Record these before installing project dependencies:

```bash
git rev-parse HEAD
git status --porcelain
python --version
python -m pip --version
```

The working tree should be clean.

Install the exact tested Python dependency snapshot:

```bash
python -m pip install -r requirements-lock.txt
```

Run the aggregate suite:

```bash
python research/reproduce.py --output reproducibility-report.json
```

Record the command exit code.

Do **not** edit repository files merely to make the suite pass. If a change appears necessary, first record the original failure and the exact change attempted.

## What to return

Please provide:

- commit SHA;
- operating system and version;
- CPU architecture;
- Python version;
- pip version;
- whether the environment was newly created/clean;
- dependency-install command and result;
- reproduction command and exit code;
- `reproducibility-report.json`;
- the first mismatch or undocumented prerequisite, if any;
- any manual workaround attempted after recording the original result.

The repository's **Reproducibility report** issue form is the preferred public reporting path for non-sensitive findings.

## What not to return publicly

Do not publish:

- passwords, API keys, tokens, credentials, or private keys;
- participant/reviewer identities;
- AR-P003 reviewer response exports from any future human study;
- hidden AR-P003 gold/analysis bundles;
- recruitment/contact lists or consent records;
- private chain-of-thought or hidden model scratchpads;
- unrelated local files.

If a finding exposes a security vulnerability rather than an ordinary reproducibility problem, follow `SECURITY.md` instead of posting exploit details in a public issue.

## Independence rule

For the first reproduction attempt, please use only:

- the public repository;
- the public documentation;
- normal dependency/package infrastructure.

Do not ask the project author for step-by-step debugging before recording the initial outcome.

After the initial result is preserved, clarification is allowed and should be documented.

## Interpreting results

### Successful reproduction

A successful run means the published repository-local deterministic/synthetic checks behaved as encoded for that commit and environment.

It does **not** establish:

- the truth or completeness of real AI activity evidence;
- improved human audit performance;
- improved productivity;
- real-world safety;
- legal/regulatory compliance;
- external standards conformance;
- production-grade cryptographic trust.

### Failed or partial reproduction

A failed reproduction is still valuable.

Preserve:

- the first failing command/check;
- relevant stdout/stderr;
- environment details;
- whether the problem appears platform-, dependency-, documentation-, or code-related.

Do not silently exclude a failed attempt from the project record.

## Optional supported-range check

After the exact-lock attempt is complete and recorded, a reviewer may separately test the supported dependency ranges:

```bash
python -m pip install -r requirements.txt
python research/reproduce.py --output reproducibility-supported-range.json
```

Keep this result separate from the exact-lock reproduction.

## Repository license note

This repository currently has **no explicit open-source license selected**.

That status is intentionally documented in `docs/LICENSING.md`.

External reviewers may inspect and test the public repository for this reproduction exercise, but broad reuse/redistribution rights should not be inferred from public visibility. The project owner is tracking explicit license selection as a separate governance decision.

## Acceptance for Phase 6

Phase 6's first external-reproduction gate can be marked complete when at least one independent party:

1. records the exact commit/environment;
2. attempts the documented clean-room procedure;
3. preserves the actual result, favorable or unfavorable;
4. reports any undocumented assumption or mismatch discovered.

One reproduction attempt does not close broader external validation work.
