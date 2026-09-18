# Attestation Trust Policy — Candidate v0.1

> **Status:** Research/design policy plus machine-readable prototype.  
> **Snapshot:** 2026-09-18  
> This does not implement cryptographic signing or claim production trust.

The existing attestation design identified four prerequisites before implementing signing:

1. signer identity;
2. key management;
3. payload type;
4. trust/revocation policy.

This document defines a candidate answer for each prerequisite without yet adding signing code.

## 1. Envelope choice

The candidate envelope remains **DSSE v1**.

References:

- https://github.com/secure-systems-lab/dsse
- https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md

DSSE binds a payload type and exact payload bytes through its pre-authentication encoding before signature verification.

The DSSE specification deliberately leaves key management and PKI out of scope. That is why this project defines a separate trust policy rather than treating a valid DSSE signature as sufficient by itself.

The DSSE `keyid` field is only a key-selection hint. It must not be treated as authenticated signer identity.

## 2. Payload type

The candidate Activity Record payload type is the project-controlled URI:

```text
https://github.com/blakegaucher/ai-activity-receipt/blob/main/docs/PAYLOAD-TYPES.md#activity-record-candidate-record-v01
```

This is **not** an IANA-registered media type and is **not** an in-toto predicate identifier.

For this candidate profile:

- the DSSE payload is the exact byte sequence of one JSON Activity Record artifact;
- signature verification authenticates those exact bytes and the payload type;
- after signature verification, the bytes are parsed as JSON;
- the parsed record must declare `record_schema_version = "candidate-record-v0.1"`;
- schema and semantic validation then run;
- the existing project-local record digest may then be recomputed as a separate content-binding check.

This intentionally separates exact-byte signature semantics from parsed-object deterministic hashing.

## 3. Signer roles

### record_emitter

A `record_emitter` may attest:

> This signer emitted or is responsible for emitting this exact canonical Activity Record artifact.

That statement does **not** by itself mean:

- every underlying event is true;
- the human principal approved every event;
- the signer is the principal;
- the signer is authorized to make unrelated claims.

The record's authority and action evidence still have to pass their own checks.

### independent_verifier

An `independent_verifier` is an optional future role for a separate verifier or additional signature.

A verifier signature should remain distinguishable from the emitter signature.

The candidate policy requires only the `record_emitter` role for the research envelope profile.

## 4. Identity model

The trust-policy schema can represent signer identities using:

- SPIFFE ID;
- X.509 subject identity;
- OIDC subject identity;
- public-key fingerprint;
- explicit test identity.

### Preferred production direction: workload identity

SPIFFE is a strong candidate for production workload identity because it defines a portable workload identity namespace and verifiable identity documents.

References:

- https://spiffe.io/docs/latest/spiffe-specs/
- https://spiffe.io/docs/latest/spiffe-specs/x509-svid/

An X.509 SVID carries a SPIFFE ID in a URI Subject Alternative Name, and SPIFFE trust is rooted in a trust domain and its trust bundle.

This project does **not** require SPIFFE. It is one suitable identity substrate.

Deployments may instead use another certificate/workload identity system if the verifier can map the cryptographic key to a trusted signer identity and role.

## 5. Key-management rules

For production policy:

- private signing keys must not be stored in this public repository;
- key rotation is required;
- compromise-response procedures are required;
- each trusted signer must have a defined verification-material source;
- active production signers require a revocation/status reference;
- signer validity windows must be coherent;
- test identities may not satisfy production trust requirements.

The repository may contain public verification material or synthetic test-only material if clearly marked.

## 6. Trust policy

Signature verification is a layered decision.

A record attestation is acceptable only when all required checks pass:

1. envelope structure is valid;
2. payload type is recognized;
3. cryptographic signature is valid;
4. signer identity maps to a trusted signer entry;
5. signer role is allowed for the payload type;
6. signer is not revoked/expired/invalid under the applicable policy;
7. the required signer roles and signature threshold are satisfied;
8. Activity Record payload parses and declares the expected schema version;
9. Activity Record structure and semantics pass;
10. downstream Receipt binding and invariants pass.

Do not collapse these into one generic `signature_valid = true` field.

## 7. Revocation and historical verification

A cryptographically valid signature can still be unacceptable because the signer has been revoked or the trust policy has changed.

Candidate production behavior:

- unknown current revocation status fails closed;
- verification evaluates signer status at verification time;
- historical validation should require an appropriate trusted timestamp or deployment-specific historical-status mechanism before claiming that a now-revoked key was valid at signing time.

DSSE itself does not provide a trusted signing timestamp.

The canonical record's `generated_at` is record metadata, not a trusted signature timestamp.

## 8. Test-only identities

The machine-readable example uses:

```text
identity_type = test_identity
status        = test_only
```

This is allowed only in a research policy.

The semantic validator requires production policies to reject test-only signers.

No test key identifier or fixture should be interpreted as a production trust root.

## 9. Machine-readable policy

Files:

- `research/attestation-trust-policy.schema.json`
- `research/attestation-trust-policy.example.json`
- `research/validate_attestation_policy.py`

Run:

```bash
python research/validate_attestation_policy.py --self-test
```

The validator checks:

- unique payload types, roles, signer IDs, and key IDs;
- role-to-payload references;
- signer role resolution;
- coherent validity windows;
- research-only handling of test identities;
- production revocation requirements;
- required-role signer availability;
- signature-threshold feasibility;
- project-controlled HTTP(S) payload-type URI;
- rejection of private-key fields in the policy.

The self-test includes one valid research policy and adversarial mutations.

## 10. Why key ID is not identity

DSSE allows a signature entry to carry `keyid`, but the DSSE specification treats it as an unauthenticated hint used to select candidate verification keys.

Therefore:

```text
keyid -> lookup hint
verified public key/certificate -> cryptographic identity material
trust policy mapping -> signer identity + allowed role
```

The project must not use:

```text
keyid == trusted identity
```

as its trust rule.

## 11. Multiple signatures

DSSE supports multiple signatures.

The machine-readable policy includes:

- `required_roles`;
- `minimum_signatures`.

A later implementation can therefore evaluate:

- one required record-emitter signature;
- optional verifier signatures;
- future threshold policies.

The current research example uses one required emitter signature.

## 12. Authorization remains separate

A trusted `record_emitter` signature authenticates the record artifact under the trust policy.

It does not automatically prove that a consequential event was authorized.

Those checks still depend on:

- principal/delegate identity;
- authority scope and prohibited actions;
- authority time window;
- per-action authorization state and decision time;
- multi-hop delegation evidence where applicable.

This separation is mandatory for the Activity Receipt model.

## 13. Implementation gate

With this candidate policy, the four prerequisites are now defined at research level:

- signer identity model: explicit trusted signer identities, workload identity preferred;
- key management: external private keys, rotation, compromise response, verification-material references;
- payload type: project-controlled Activity Record URI with exact-byte semantics;
- trust/revocation: role-based trusted signer registry, fail-closed production revocation behavior, threshold rules.

A **research-only DSSE signing/verification prototype** now exercises this policy with ephemeral in-memory Ed25519 keys and adversarial verification cases. See [DSSE-PROTOTYPE.md](DSSE-PROTOTYPE.md).

Production signing remains blocked until a deployment provides actual identity issuance, protected private-key storage, revocation/status infrastructure, operational trust roots, and an appropriate timestamp/history strategy.

## Evidence boundary

A well-defined trust policy improves testability. It does not establish that any real signer, certificate authority, workload identity provider, or revocation service has been deployed.
