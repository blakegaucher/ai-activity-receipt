# Contributing

AI Activity Receipt is an early-stage research repository. Contributions are welcome when they preserve the project's evidence boundaries and reproducibility rules.

## Before opening a pull request

Run the public deterministic/synthetic suite:

```bash
python -m pip install -r requirements-lock.txt
python research/reproduce.py --output reproducibility-report.json
```

The command must exit successfully before a change is described as passing the repository suite.

For a supported-range environment rather than the exact tested snapshot, install `requirements.txt`.

## Evidence rules

Please keep these classes separate:

- engineering / synthetic test evidence;
- human-participant evidence;
- external independent reproduction;
- standards or institutional correspondence;
- customer / market evidence;
- financing or commercial evidence.

A passing project-authored test is not independent validation, standards conformance, legal compliance, production security validation, or proof of real-world benefit.

Preserve null and negative findings.

Do not rewrite frozen benchmark results to match a newer schema or interpretation. Material methodology changes should use a new version, branch, or append-only correction.

## Human-study and privacy boundary

Do not commit:

- identifiable participant data;
- reviewer response exports;
- hidden analysis/gold bundles;
- passwords, API keys, access tokens, credentials, or secrets;
- private chain-of-thought.

The repository `.gitignore` blocks common AR-P003 local/private output paths, but that is a backup control, not a substitute for access control and review.

Reviewer-facing AR-P003 bundles must remain separated from hidden gold labels, strata, and analysis-only material.

## Pull-request expectations

A useful pull request should include:

- a narrow description of the change;
- the evidence or failure mode motivating it;
- deterministic tests where practical;
- documentation updates when behavior or evidence boundaries change;
- no unsupported claim upgrade.

When changing AR-P003 tooling, include or extend an end-to-end smoke test if the change crosses assignment, bundle construction, response export, hidden-label merge, or scoring boundaries.

## Security-sensitive reports

Do not publish secrets or participant data in a public issue. Use a private repository-owner channel or GitHub's private vulnerability-reporting path if one is available for the repository.

## Licensing

Project-authored public repository material is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE), [NOTICE](NOTICE), and [docs/LICENSING.md](docs/LICENSING.md).

Do not submit third-party code, text, fixtures, or assets unless their provenance and required notices are clear and compatible with inclusion. Future human-study, participant, reviewer, hidden-analysis, personal, or privacy-sensitive material remains outside the public-release scope unless a separate release/privacy/ethics/licensing decision is made.

The Apache-2.0 repository license does not grant trademark or endorsement rights in Ancient Immortal Art or AI Activity Receipt.
