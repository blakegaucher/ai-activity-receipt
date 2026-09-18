# C2PA Evidence-Reference Evaluation — Candidate v0.1

> **Status:** Research/evaluation only.  
> **Snapshot:** 2026-09-18  
> This document does not claim C2PA conformance, successful Content Credential validation, or authenticated provenance for any project fixture.

## Question

Should the AI Activity Record/Receipt copy C2PA assertions directly into its core schema, or should C2PA evidence remain externally referenced?

## Current C2PA 2.4 signals relevant to this project

Official specification:

https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html

C2PA 2.4 (April 2026) adds several features that are directly relevant to AI Activity Receipt interoperability:

- `c2pa.repository-receipt`, which can record proof that a C2PA Manifest was ingested by a Manifest Repository;
- `c2pa.ai-disclosure`, which provides machine-readable AI transparency information;
- crJSON, a JSON-LD derived view for profile evaluation, interoperability testing, and validation reporting.

The C2PA specification explicitly describes crJSON as a **derived view** rather than an independently verifiable input format.

The repository-receipt assertion includes a repository identity, repository-canonical manifest identifier, and an anchor URI/proof for the ingestion event. The proof structure is repository-specific.

C2PA also uses hashed references such as `hashed_uri` / `hashed_ext_uri` in a number of assertions and specifies validation behavior for referenced data.

## Design conclusion

**Do not copy complete C2PA assertions or repository proof bodies into candidate-record-v0.1 or the compact Receipt.**

Prefer an external evidence-reference layer that records enough information to:

- identify what canonical object the evidence supports;
- identify the external standard/profile;
- locate or bind to the external evidence;
- record whether validation has actually been performed;
- keep third-party proof payloads and credentials outside the Receipt.

This keeps operational provenance and content provenance related but distinct.

## Why an external reference is preferable

### 1. Different evidence domain

The Activity Receipt focuses on delegated authority, actions, material sources, verification, incidents, and audit reconstruction.

C2PA focuses on content provenance and tamper-evident Content Credentials for digital assets.

Those domains overlap for produced or consumed content, but they are not interchangeable.

### 2. Avoid false validation claims

A URI pointing to a Content Credential is not the same as a successfully validated C2PA Manifest.

The candidate evidence-reference profile therefore separates:

- **where the evidence is**;
- **what profile/standard it claims to use**;
- **whether validation was performed**.

The default example state is `not_checked`.

### 3. Repository receipt proof is repository-specific

C2PA 2.4 defines the repository-receipt assertion around a repository, a canonical manifest identifier, and an anchor containing a repository-specific proof.

The Activity Record should not invent semantics for that proof body or normalize it into a generic authorization decision.

Instead, it can reference the verification/retrieval URI and manifest identifier.

### 4. AI disclosure should stay content-specific

The `c2pa.ai-disclosure` assertion can carry model provenance, scientific-domain metadata, and human-oversight information for a content-creation pipeline.

Those fields can complement an Activity Record but should not automatically override:

- authenticated system identity;
- delegated authority;
- event authorization;
- verification state.

A validated disclosure could be referenced as content-provenance evidence associated with a source or produced artifact.

### 5. Avoid duplicated signatures and trust logic

If C2PA already defines signature, trust, validation, and content-binding behavior, the Activity Receipt should not reproduce the assertion body and pretend to re-validate it with a different ad hoc model.

The better boundary is:

```text
Activity Record / Receipt
        |
        +--> external evidence reference
                  |
                  +--> validated C2PA Manifest / assertion / repository receipt
```

## Standalone research prototype

The repository includes:

- `research/external-evidence-reference.schema.json`
- `research/external-evidence-reference.example.json`
- `research/validate_external_evidence.py`

The example links one synthetic canonical record to:

1. a C2PA content-provenance manifest reference;
2. a C2PA 2.4 repository-receipt anchor;
3. a separate authorization-decision reference.

That third reference is deliberate: it demonstrates that a C2PA evidence reference does not replace operational authorization evidence.

## Candidate evidence-reference fields

Each external reference records:

- `evidence_id`;
- evidence `kind`;
- the canonical-record `subject` it supports;
- optional external standard/profile;
- optional external identifier;
- URI and/or SHA-256 digest locator;
- explicit validation state;
- optional validator/time/trust-profile metadata.

The prototype does not contain raw bearer tokens, private reasoning, or repository-specific proof objects.

## Semantic checks

The validator requires:

- the index `record_id` to match the target canonical record;
- unique evidence IDs;
- event/source subjects to resolve;
- `state = valid` to include both validator identity and validation timestamp;
- repository-receipt references to identify C2PA, `c2pa.repository-receipt`, the repository-canonical manifest ID, and a verification/retrieval URI;
- unknown or arbitrary proof payload fields to be rejected by the profile.

Run:

```bash
python research/validate_external_evidence.py --self-test
```

## Current mapping decision

For candidate-record-v0.1:

- a validated C2PA asset/content reference may still support `sources[].uri`;
- a validated digest may support `sources[].hash`;
- `c2pa.ai-disclosure` remains without a dedicated canonical-record field;
- `c2pa.repository-receipt` remains without a dedicated canonical-record field.

The evaluation therefore does **not** add C2PA-specific fields to candidate-record-v0.1.

Instead, the standalone external-reference prototype is the preferred direction for future evidence-substrate integration.

## Future integration gate

Before external references are added to the canonical schema, the project should define:

1. whether references live directly in the Activity Record or in a separately bound evidence index;
2. how the evidence index is itself content-bound to the record;
3. which evidence kinds require validation metadata;
4. how revocation/staleness is represented;
5. how trust profiles are named and versioned;
6. whether the compact Receipt exposes only an evidence count/summary or selected references;
7. privacy and retention requirements for external evidence locations.

## Evidence boundary

A reference does not prove the referenced evidence is:

- reachable;
- authentic;
- valid;
- complete;
- trustworthy;
- sufficient to support the claimed real-world event.

Those questions remain the job of the referenced standard's validator, the evidence source, and the applicable trust policy.
