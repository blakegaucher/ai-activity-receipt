# AR-P003 v0.3 Benchmark Workspace

This directory contains **development infrastructure** for the next human-centered AR-P003 evaluation.

> Nothing here is a completed human experiment. The repository does not yet contain a frozen confirmatory corpus, human reviewer data, or evidence of a Receipt benefit.

## Files

- `protocol.json` — machine-readable candidate protocol scaffold.
- `score_responses.py` — deterministic component-level scorer with a built-in synthetic self-test.
- `response-record.schema.json` — JSON Schema for one analysis-side reviewer/case scoring record.
- `generate_assignment.py` — seeded reviewer/case assignment generator for the selected raw / neutral-structured / Receipt design; it avoids repeat exposure to the same case and keeps each reviewer/case condition count within one observation across the three conditions.
- `freeze_manifest.py` — content-bound SHA-256 manifest utility that reads the exact protocol version/hash, rejects duplicate paths, computes an aggregate artifact-set digest and deterministic freeze content ID, and can require `protocol.frozen=true`.
- `freeze-manifest.schema.json` — machine-readable v0.2 freeze-manifest contract.
- `case-package.schema.json` — development manifest schema for reviewer-facing evidence, Receipt, and analysis-only files.
- `lint_case_packages.py` — file-separation, path-safety, stratum/state, leakage-marker, and hash-report linter for development case packages.
- `audit_leakage.py` — analysis-side heuristic audit for literal gold-label exposure, degenerate answer-option sets, cross-presentation evidence drift, and Receipt presentation expansion.
- `leakage-audit.schema.json` — machine-readable report schema for the pre-freeze leakage/presentation audit.
- `case-methodology-review.schema.json` — analysis-side schema for manual pre-freeze case review bound to one exact audit/build.
- `case-methodology-review.example.json` — deliberately not-run review template; not evidence.
- `validate_case_methodology_review.py` — requires full case coverage, exact audit/build binding, no unresolved high-risk leakage flags, and acceptable manual review dimensions before a review may be marked complete.
- `plan_sample_size.py` — development-only sample-size/precision screening approximations.
- `planning-scenarios.example.json` — illustrative independent-observation sensitivity grid; not frozen study assumptions.
- `plan_crossed_design.py` — development-only reviewer × case Monte Carlo sensitivity planner using the balanced assignment and two-way clustered uncertainty.
- `crossed-planning-scenarios.example.json` — illustrative crossed-design scenarios; not frozen performance or variance assumptions.
- `offline_runner.html` — self-contained development-only reviewer interface with structured answers, pause/visibility timing, safe intermissions, and local response export.
- `runner-bundle.schema.json` — reviewer-facing bundle schema; hidden gold/stratum data are excluded.
- `runner-response.schema.json` — reviewer-side response/timing export schema.
- `runner-analysis.schema.json` — hidden analysis-side gold/stratum schema.
- `runner-bundle.example.json` — synthetic development-only runner bundle.
- `validate_runner_data.py` — bundle/response validation plus static offline/no-network runner checks.
- `merge_runner_responses.py` — analysis-side join from reviewer export + hidden gold bundle + exact frozen assignment into scorer-compatible JSONL; rejects assignment-hash/version, case/order, condition, stratum, and incomplete-session mismatches.
- `runner-build-config.schema.json` — analysis-side configuration for turning case packages + assignment rows into reviewer bundles.
- `build_runner_bundles.py` — validates case packages, enforces assignment/manifest stratum agreement, checks that every set-valued gold answer is representable by the reviewer UI options, emits condition-specific reviewer bundles plus a separate hidden analysis bundle and SHA-256 build manifest.
- `pipeline_smoke_test.py` — synthetic end-to-end assignment → bundle build → reviewer response → hidden-label merge → scoring integration test.
- `freeze-readiness.schema.json` — machine-readable preregistration/freeze gate schema.
- `freeze-readiness.current.json` — current gate state; intentionally development-not-ready.
- `check_freeze_readiness.py` — fails closed on premature ready/frozen claims and cross-checks `protocol.json`.
- `browser-smoke-record.schema.json` — structured record for real manual browser/device smoke tests.
- `browser-smoke-record.example.json` — deliberately incomplete/not-run template; not smoke-test evidence.
- `validate_browser_smoke.py` — prevents incomplete templates or major defects from masquerading as a passing manual smoke record.

The human-readable preregistration draft and first explicit methodology decision are in:

- `../../docs/AR-P003-V0.3-PROTOCOL.md`
- `../../docs/AR-P003-V0.3-COMPARISON-CONDITIONS-DECISION-2026-09-20.md`
- `../../docs/AR-P003-V0.3-CHALLENGE-DESIGN-DECISION-2026-09-21.md`

## Data boundary

Do **not** commit identifiable human-participant data, access tokens, private chain-of-thought, passwords, or other secrets to this public repository.

Future confirmatory materials should distinguish:

- **development data** — may be inspected and changed while tooling is developed;
- **sealed confirmatory data** — fixed before scored human outcomes are inspected;
- **release data** — de-identified material that can responsibly be published after evaluation.

The synthetic records embedded in the scorer self-test are developer checks only. They are not AR-P003 evidence.

### Assignment balance guarantee

Condition labels are assigned only after reviewer/case incidence is selected. The current version uses deterministic equitable bipartite b-matching to allocate raw, structured, and Receipt conditions.

For every generated assignment:

- each reviewer sees each selected case only once;
- case exposure differs by at most one across cases;
- each reviewer's largest-minus-smallest raw/structured/Receipt count is at most one;
- each case's largest-minus-smallest raw/structured/Receipt count is at most one;
- when a relevant degree is divisible by three, its split is exactly one-third per condition.

The generator also emits reviewer-, case-, and stratum-level condition diagnostics. Stratum-level totals are diagnostic rather than a mathematical guarantee; they should be inspected before the final assignment is frozen.

This replaces an earlier development-only greedy condition allocator that could keep individual cases balanced while leaving a reviewer with a 4/2 split when six cases were assigned. No human confirmatory data had been collected or frozen under that development allocator.

## Response record format

The current scorer expects one JSON object per line.

Example shape:

```json
{
  "reviewer_id": "pseudonymous-reviewer-id",
  "case_id": "case-id",
  "condition": "raw",
  "stratum": "ordinary",
  "elapsed_seconds": 83.4,
  "gold": {
    "material_actions": ["action-1"],
    "authorization_violation": false,
    "material_sources": ["source-1"],
    "incidents": [],
    "verification_state": "confirmed",
    "missing_evidence": false
  },
  "answer": {
    "material_actions": ["action-1"],
    "authorization_violation": false,
    "material_sources": ["source-1"],
    "incidents": [],
    "verification_state": "confirmed",
    "missing_evidence": false,
    "confidence": 4
  }
}
```

In an actual study, gold labels must remain hidden from reviewers. The combined record above is an analysis/scoring representation, not a reviewer-facing file.

## Scoring

Run the development self-tests:

```bash
python benchmark/arp003_v0_3/score_responses.py --self-test
python benchmark/arp003_v0_3/generate_assignment.py --self-test
python benchmark/arp003_v0_3/lint_case_packages.py --self-test
python benchmark/arp003_v0_3/audit_leakage.py --self-test
python benchmark/arp003_v0_3/validate_case_methodology_review.py --self-test
python benchmark/arp003_v0_3/validate_case_methodology_review.py
python benchmark/arp003_v0_3/plan_sample_size.py --self-test
python benchmark/arp003_v0_3/validate_runner_data.py --self-test
python benchmark/arp003_v0_3/merge_runner_responses.py --self-test
python benchmark/arp003_v0_3/build_runner_bundles.py --self-test
python benchmark/arp003_v0_3/pipeline_smoke_test.py
python benchmark/arp003_v0_3/check_freeze_readiness.py --self-test
python benchmark/arp003_v0_3/check_freeze_readiness.py
python benchmark/arp003_v0_3/validate_browser_smoke.py --self-test
python benchmark/arp003_v0_3/freeze_manifest.py --self-test
```

Score JSONL records:

```bash
python benchmark/arp003_v0_3/score_responses.py responses.jsonl --output scored.json
```

The scorer intentionally reports endpoint components separately:

- set precision/recall/F1 for material actions, sources, and incidents;
- exact accuracy for authorization violation, verification state, and missing-evidence state;
- elapsed time;
- confidence as a descriptive measure.

It does **not** generate a post-hoc weighted primary composite.

## Sample-size / precision development planning

The workspace includes a screening planner for binary accuracy endpoints, standardized continuous endpoints, and confidence-interval precision targets.

Run the bundled sensitivity grid:

```bash
python benchmark/arp003_v0_3/plan_sample_size.py \
  benchmark/arp003_v0_3/planning-scenarios.example.json
```

The calculations are independent-observation approximations with optional design-effect and unusable-observation inflation. They do **not** freeze the confirmatory sample size because AR-P003 observations are crossed by reviewer and case.

See `../../docs/AR-P003-V0.3-PLANNING.md`.

## Development case-package linting

The case-package linter is designed to catch mechanical corpus mistakes **before** a future sealed set is frozen.

A case manifest uses one shared `reviewer_evidence_files` list plus separate `structured_control_file` and `receipt_file` artifacts. This encodes the selected ordinary comparison contract as:

```text
raw        = shared underlying evidence
structured = same shared underlying evidence + neutral structured event table
receipt    = same shared underlying evidence + Receipt
```

The linter also requires analysis-only files (including gold labels) to remain disjoint from reviewer-facing files, rejects unsafe or missing paths, checks that stale/incomplete/conflicting strata use the matching Receipt state, scans exact prespecified leakage markers, and reports SHA-256 hashes for linked files.

This tool cannot prove that a case is realistic, unbiased, or free of all semantic leakage. Human review of the underlying evidence and Receipt is still required before freeze.

Create a development freeze manifest when the artifact set is ready:

```bash
python benchmark/arp003_v0_3/freeze_manifest.py \
  docs/AR-P003-V0.3-PROTOCOL.md \
  benchmark/arp003_v0_3/protocol.json \
  benchmark/arp003_v0_3/score_responses.py \
  --output benchmark/arp003_v0_3/FREEZE-MANIFEST.json
```

Do not treat a development manifest as the final confirmatory freeze unless it also includes the final corpus, instructions, assignments, exclusions, and analysis artifacts required by the protocol.

### Assignment-bound response integrity

Generated reviewer bundles now carry the exact assignment version and SHA-256 digest. The offline runner propagates those fields into response exports.

The analysis-side merge requires the exact assignment JSON and treats it—not the reviewer export—as authoritative for reviewer membership, case order, and raw/structured/Receipt condition. Final scorer input is rejected if the response was edited or mixed with a different assignment.

This is an integrity control for the development study pipeline. It is not cryptographic signer authentication and does not prevent a malicious party who can replace every analysis artifact consistently.

### Answer-option representability guard

The bundle builder fails closed if a gold material-action, material-source, or incident label is absent from the reviewer-facing answer options. It also records analysis-side counts for option-set size, gold-set size, and non-gold options.

This prevents an impossible-to-answer case from reaching the runner. It does **not** prove that the options are free of answer leakage. Before freeze, review the option diagnostics and ensure the visible choice set is justified independently of the hidden gold labels.

### Local/private output protection

The repository `.gitignore` excludes common local reviewer-bundle, hidden-analysis, response-export, scorer-input, and private study-data paths. This is a backup against accidental commits, not an access-control mechanism.

---

## Development offline runner

The development runner removes several avoidable v0.2.3 interface/timing confounds without declaring the v0.3 instrument frozen.

Reviewer-facing bundles contain only evidence, optional Receipt, pseudonymous IDs, and selectable response vocabularies. Gold labels and hidden challenge strata remain in a separate analysis bundle and are joined only after reviewer export.

The browser runner is self-contained and offline, records wall and active time, supports manual and visibility pauses, inserts a safe intermission between cases, and uses structured controls rather than raw JSON editing.

Before the first timed case, the runner now requires a three-question **pre-case comprehension gate** covering: Receipt-vs-source-evidence conflict handling, the prohibition on private chain-of-thought submission, and pause/visibility timing behavior. The response export records only the gate version, attempt count, and pass timestamp; it does not score the comprehension check as a study outcome.

After that gate, reviewers complete one **untimed structured practice reconstruction** using a fixed synthetic training example. They must correctly use the same action/source/incident/authorization/verification/missing-evidence controls before the first study case begins. The export records only practice version, attempt count, and pass time; the practice answer is not included in scorer input.

The analysis-side bundle builder now closes the development packaging loop: it reads the seeded assignment and linted case manifests, verifies the assignment's hidden stratum against each case manifest, gives raw reviewers shared evidence only, structured reviewers that same evidence plus the neutral table, Receipt reviewers that same evidence plus the Receipt, and emits gold/stratum data to a separate hidden analysis bundle.

See `../../docs/AR-P003-V0.3-OFFLINE-RUNNER.md`.

---

## Methodology decision control

The current executable draft and the earlier project research review contain material methodological differences that must be resolved deliberately before confirmatory freeze.

Files:

- `methodology-decisions.schema.json`
- `methodology-decisions.current.json`
- `validate_methodology_decisions.py`
- `../../docs/AR-P003-V0.3-METHODOLOGY-DECISIONS.md`

The ledger records `comparison_conditions` as selected (`three_condition_structured_control`), `challenge_design` as selected (`integrated_challenge_strata`), and `reviewer_population` as selected (`relevant_professional_reviewers`). Primary endpoint, primary timing clock, and meaningful effect/precision target remain unresolved. The selected population requires at least 1 year of relevant professional/practical experience, records 1–2/3–5/6+ year bands, and freezes language, familiarity, exclusion, assistance, and inference-scope rules without authorizing recruitment. CI rejects a frozen protocol while required methodology decisions remain unresolved.

Run:

```bash
python benchmark/arp003_v0_3/validate_methodology_decisions.py --self-test
python benchmark/arp003_v0_3/validate_methodology_decisions.py
```

---

## Before human execution

Do not describe AR-P003 v0.3 as frozen or confirmatory until the checklist in the preregistration draft is complete, including population definition, endpoint selection, sample-size/precision analysis, corpus freeze, reviewer instructions, assignment procedure, scorer/analysis freeze, applicable ethics determination, and SHA-256 freeze manifest.
