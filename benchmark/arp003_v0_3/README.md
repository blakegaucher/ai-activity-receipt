# AR-P003 v0.3 Benchmark Workspace

This directory contains **development infrastructure** for the next human-centered AR-P003 evaluation.

> Nothing here is a completed human experiment. The repository does not yet contain a frozen confirmatory corpus, human reviewer data, or evidence of a Receipt benefit.

## Files

- `protocol.json` — machine-readable candidate protocol scaffold.
- `score_responses.py` — deterministic component-level scorer with a built-in synthetic self-test.
- `response-record.schema.json` — JSON Schema for one analysis-side reviewer/case scoring record.
- `generate_assignment.py` — seeded reviewer/case assignment generator that avoids showing the same case twice to one reviewer, balances case exposure, and guarantees per-reviewer/per-case control-vs-Receipt imbalance of at most one observation.
- `freeze_manifest.py` — SHA-256 manifest utility for protocol/corpus/scorer freeze artifacts.
- `case-package.schema.json` — development manifest schema for reviewer-facing evidence, Receipt, and analysis-only files.
- `lint_case_packages.py` — file-separation, path-safety, stratum/state, leakage-marker, and hash-report linter for development case packages.
- `plan_sample_size.py` — development-only sample-size/precision screening approximations.
- `planning-scenarios.example.json` — illustrative sensitivity grid; not frozen study assumptions.
- `offline_runner.html` — self-contained development-only reviewer interface with structured answers, pause/visibility timing, safe intermissions, and local response export.
- `runner-bundle.schema.json` — reviewer-facing bundle schema; hidden gold/stratum data are excluded.
- `runner-response.schema.json` — reviewer-side response/timing export schema.
- `runner-analysis.schema.json` — hidden analysis-side gold/stratum schema.
- `runner-bundle.example.json` — synthetic development-only runner bundle.
- `validate_runner_data.py` — bundle/response validation plus static offline/no-network runner checks.
- `merge_runner_responses.py` — analysis-side join from reviewer export + hidden gold bundle into scorer-compatible JSONL.
- `runner-build-config.schema.json` — analysis-side configuration for turning case packages + assignment rows into reviewer bundles.
- `build_runner_bundles.py` — validates case packages, enforces assignment/manifest stratum agreement, checks that every set-valued gold answer is representable by the reviewer UI options, emits condition-specific reviewer bundles plus a separate hidden analysis bundle and SHA-256 build manifest.
- `pipeline_smoke_test.py` — synthetic end-to-end assignment → bundle build → reviewer response → hidden-label merge → scoring integration test.

The human-readable preregistration draft is in:

- `../../docs/AR-P003-V0.3-PROTOCOL.md`

## Data boundary

Do **not** commit identifiable human-participant data, access tokens, private chain-of-thought, passwords, or other secrets to this public repository.

Future confirmatory materials should distinguish:

- **development data** — may be inspected and changed while tooling is developed;
- **sealed confirmatory data** — fixed before scored human outcomes are inspected;
- **release data** — de-identified material that can responsibly be published after evaluation.

The synthetic records embedded in the scorer self-test are developer checks only. They are not AR-P003 evidence.

### Assignment balance guarantee

Condition labels are assigned only after reviewer/case incidence is selected. The current generator treats that incidence structure as a bipartite graph and uses deterministic balanced edge coloring based on Euler circuits.

For every generated assignment:

- each reviewer sees each selected case only once;
- case exposure differs by at most one across cases;
- each reviewer has control-vs-Receipt count imbalance of at most one;
- each case has control-vs-Receipt count imbalance of at most one;
- even-degree reviewers/cases receive an exact 50/50 condition split.

The generator also emits reviewer-, case-, and stratum-level condition diagnostics. Stratum-level totals are diagnostic rather than a mathematical guarantee; they should be inspected before the final assignment is frozen.

This replaces an earlier development-only greedy condition allocator that could keep individual cases balanced while leaving a reviewer with a 4/2 split when six cases were assigned. No human confirmatory data had been collected or frozen under that development allocator.

## Response record format

The current scorer expects one JSON object per line.

Example shape:

```json
{
  "reviewer_id": "pseudonymous-reviewer-id",
  "case_id": "case-id",
  "condition": "control",
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
python benchmark/arp003_v0_3/plan_sample_size.py --self-test
python benchmark/arp003_v0_3/validate_runner_data.py --self-test
python benchmark/arp003_v0_3/merge_runner_responses.py --self-test
python benchmark/arp003_v0_3/build_runner_bundles.py --self-test
python benchmark/arp003_v0_3/pipeline_smoke_test.py
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

A case manifest uses one shared `reviewer_evidence_files` list for both conditions and a separate `receipt_file`. This encodes the ordinary comparison contract as:

```text
control = shared underlying evidence
receipt = same shared underlying evidence + Receipt
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

The analysis-side bundle builder now closes the development packaging loop: it reads the seeded assignment and linted case manifests, verifies the assignment's hidden stratum against each case manifest, gives control reviewers only shared evidence, gives Receipt reviewers the same evidence plus the Receipt, and emits gold/stratum data to a separate hidden analysis bundle.

See `../../docs/AR-P003-V0.3-OFFLINE-RUNNER.md`.

---

## Before human execution

Do not describe AR-P003 v0.3 as frozen or confirmatory until the checklist in the preregistration draft is complete, including population definition, endpoint selection, sample-size/precision analysis, corpus freeze, reviewer instructions, assignment procedure, scorer/analysis freeze, applicable ethics determination, and SHA-256 freeze manifest.
