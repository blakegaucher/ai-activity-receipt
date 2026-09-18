# Validation Record

This document summarizes the current validation state of the **AI Activity Receipt** project.

> **Important:** Current evidence is synthetic and technical. Nothing documented here establishes real-world productivity improvement, safety improvement, legal compliance, standards conformance, or commercial effectiveness.

---

## AR-P001 — Structural Validation

**Status:** Completed synthetic engineering pilot  
**Result:** 12 / 12 prespecified fixtures produced the expected accept/reject outcome.

### Purpose

Test whether the proposed AI Activity Receipt schema and invariant checker could enforce a small set of governance rules on synthetic AI-agent activity.

### Tested invariants

The pilot checked that:

1. required system, version, deployer, and task fields exist;
2. material sources cited by a result are registered;
3. a completed consequential action has prior approved authorization;
4. a prohibited action is not recorded as completed;
5. blocked unauthorized activity or tool failure produces an incident record;
6. completed consequential actions include an explicit verification state;
7. private chain-of-thought / hidden-reasoning fields are excluded.

### Public-repository reproduction note

AR-P001 and AR-P002 summarize earlier internal synthetic engineering suites and may use vocabulary from earlier schema iterations. The current public repository publishes a separate **19-fixture candidate-v0.2 reproducibility suite** using the present `system`, `authority.principal`, `authority.delegate`, provenance, action timing, authorization-decision timing, verification, incident, and integrity fields. The public workflow should not be described as a reproduction of all 12 AR-P001 or 24 AR-P002 historical cases unless those historical fixtures are separately published.

### Interpretation

AR-P001 supports the narrow conclusion that the schema and invariant checker behaved consistently on these synthetic fixtures.

It does **not** establish that the Receipt improves human auditing, incident reconstruction, productivity, or safety.

---

## AR-P002 — Expanded Engineering Validation

**Status:** Completed synthetic engineering checks  
**Result:** 24 / 24 historical internal v0.2 engineering fixtures behaved as expected.

The expanded fixture set covered areas including:

- authorization timing;
- event tampering;
- delegation;
- provenance;
- failed tool calls;
- incident linking;
- verification;
- private-reasoning exclusion.

### Interpretation

AR-P002 provides additional internal engineering evidence that the v0.2 design behaves as intended across a broader synthetic test set.

It remains an **internal engineering result**, not evidence of real-world effectiveness.

---

## Current public candidate-v0.2 reproducibility suite

**Status:** Public repository engineering smoke test  
**Manifest:** `examples/fixture-manifest.json`  
**Current cases:** 19 synthetic fixtures

The public suite tests both JSON Schema outcomes and semantic-invariant outcomes. Negative fixtures specify the invariant(s) expected to fire so the suite can detect a case that is rejected for the wrong reason.

The current public cases exercise:

- required structural identity fields;
- registered and unique material-source identifiers;
- approved, in-scope, prior authorization for consequential completion;
- explicit prohibited-action contradictions;
- linked incident preservation for materially blocked/failed activity;
- inverted authority windows and action timing before/after the authority window;
- confirmed-verification evidence requirements;
- unresolved verification references;
- unresolved incident references;
- direct-delegation consistency;
- duplicate material-action event identifiers;
- private-reasoning-field rejection;
- generation timestamps that precede represented activity.

The suite is intentionally a **repository reproducibility check**, not a measurement of human audit benefit, safety, compliance, or commercial performance.

---

## Canonical record derivation smoke test

**Status:** Public synthetic engineering check

The repository now publishes one candidate canonical Activity Record, an exact expected derived Receipt, and a deterministic derivation utility.

The self-test checks that:

- the canonical record satisfies `activity-record.schema.json`;
- actor/source/event references are internally resolvable under the candidate profile;
- non-material source/event records are excluded from the Receipt view;
- the derived Receipt exactly matches the published expected fixture;
- the derived Receipt passes the current Receipt schema and semantic invariant checker;
- repeated derivation is deterministic;
- the Receipt carries a SHA-256 binding to the exact parsed source record under the documented project-local serialization profile.

This establishes only deterministic behavior for the published synthetic example. It does not establish raw-log ingestion fidelity, cryptographic signing/non-repudiation, standards conformance, or real-world audit benefit.

---

## AR-P003 — Comparative Audit Reconstruction Benchmark

**Status:** Benchmark development and auxiliary reviewer testing  
**Primary human-benefit claim:** Not yet established.

### Research question

Given the same underlying AI-agent episode, can independent reviewers reconstruct:

- material actions;
- authorization state;
- material source provenance;
- incidents;
- verification state;

more accurately and/or faster when provided with a standardized AI Activity Receipt?

### Early auxiliary reviewer work

An early AR-P003 AI-reviewer pilot reviewed 80 synthetic episodes.

Its main value was methodological: it exposed problems in the benchmark design, including:

- action-ontology ambiguity;
- material-source ambiguity;
- invalid reviewer timing;
- verification-semantics confusion;
- scorer/instruction mismatches.

These results were retained as debugging evidence rather than converted into an effectiveness claim.

### Frozen v0.2.3 auxiliary result

A later auxiliary run reached ceiling-level performance on non-timing endpoints in both conditions.

That result did **not** establish a Receipt advantage because:

- control performance was also at ceiling;
- timing was unavailable;
- incident-label leakage was present;
- case ordering created learning/pattern risk;
- the human runner had timing-design problems;
- Receipt conditions contained substantially more displayed text.

The protocol therefore should not be silently altered and rescored as though it were confirmatory evidence.

---

## Current next benchmark — AR-P003 v0.3 direction

The preferred next step is a new human-centered benchmark using a fresh sealed corpus.

Planned improvements include:

- randomized case order;
- reduced answer leakage;
- realistic heterogeneous log formats;
- proper wall-clock timing;
- safer break handling;
- lower ceiling effects;
- explicit stale or incomplete Receipt cases;
- explicit Receipt/raw-evidence conflict cases;
- independent human reviewers;
- frozen endpoints before results are inspected;
- preservation of misses, abstentions, negative results, and defects.

The benchmark should compare:

1. **Control:** heterogeneous raw evidence only;
2. **Receipt:** the same underlying evidence plus a standardized Receipt.

For ordinary cases, the Receipt must not contain evidence that cannot be derived from the raw evidence.

---

## Candidate evaluation measures

Current measures of interest include:

- material-action reconstruction accuracy;
- authorization-violation detection;
- material-source attribution accuracy;
- incident classification accuracy;
- verification-state accuracy;
- time to final reconstruction;
- reviewer agreement;
- false incident flags;
- missing-evidence identification;
- reviewer confidence.

No single post-hoc composite score should replace the prespecified endpoints after results are inspected.

---

## Governance rules

The validation program follows these principles:

- Freeze the test corpus before evaluation.
- Freeze reviewer instructions and scoring rules before evaluation.
- Do not remove slow, confusing, failed, or negative cases after inspection.
- Do not tune a Receipt version on a test set and then present rescoring of that same set as independent confirmation.
- A schema change creates a new Receipt version.
- A confirmatory claim requires a fresh sealed evaluation set.
- Human reviewers are required for claims about human audit performance.
- AI reviewers may be used for debugging or auxiliary analysis.
- Private chain-of-thought is not required or collected.

---

## Current evidence boundary

At this stage, the project supports claims about:

- synthetic schema behavior;
- invariant-checking behavior;
- benchmark-development methodology;
- discovered evaluation defects;
- provenance and governance design.

It does **not yet support claims of**:

- proven human productivity improvement;
- proven human audit-time reduction;
- improved real-world safety;
- regulatory compliance;
- standards certification or conformance;
- commercial performance;
- superiority over existing standards or observability systems.

---

## Validation philosophy

Failures and null results are part of the project record.

The goal is not to make every experiment look successful. The goal is to develop an AI activity record that can survive increasingly difficult attempts to test, falsify, and audit it.
