# Integrity and Attestation Direction — Candidate v0.1

> **Status:** Research/design decision, not an implemented signature system.  
> **Snapshot:** 2026-09-18  
> This document does not claim cryptographic non-repudiation, standards conformance, verified signer identity, or production security.

The project now has two distinct integrity questions:

1. **Record binding:** can a Receipt be tied to the exact canonical Activity Record from which it was derived?
2. **Attestation:** can a verifier establish who or what signed/attested to that record, under an explicit trust policy?

The current repository implements the first question only.

---

## Current record binding

`derive_receipt.py` computes a SHA-256 digest over a deterministic project-local serialization of the parsed canonical Activity Record:

```text
UTF-8(
  JSON(
    record,
    sort_keys=true,
    separators=(",", ":"),
    ensure_ascii=false
  )
)
```

The resulting value is stored in the Receipt as:

- `integrity.record_hash`;
- `integrity.derived_from_record_hash`.

This gives the current prototype a deterministic **content binding** to the parsed record.

It does **not** provide:

- a digital signature;
- signer identity;
- key ownership;
- key revocation;
- timestamp authority;
- non-repudiation;
- proof that the underlying evidence is true;
- proof that the record was not created maliciously in the first place.

A hash is evidence of equality/difference relative to the bytes or serialization being hashed. It is not an identity assertion.

---

## Why the current serialization is not called JCS

RFC 8785 defines the **JSON Canonicalization Scheme (JCS)** for cryptographic hashing/signing of JSON.

Reference:

https://www.rfc-editor.org/rfc/rfc8785.html

JCS is more specific than:

```text
json.dumps(sort_keys=True, separators=(",", ":"))
```

It constrains JSON to the I-JSON subset and defines canonical serialization behavior using ECMAScript-compatible primitive serialization and deterministic property ordering.

The current project-local serializer has not been tested against the RFC 8785 conformance requirements or test corpus.

Therefore:

> **Do not describe the current record hash as RFC 8785 / JCS canonicalization.**

If the project later needs JCS interoperability, it should add an explicit JCS implementation, published test vectors, and cross-language verification before making that claim.

---

## DSSE / in-toto finding

For an authenticated envelope around arbitrary data, **DSSE (Dead Simple Signing Envelope)** is a strong candidate.

References:

- DSSE repository/specification: https://github.com/secure-systems-lab/dsse
- in-toto Attestation Framework envelope layer: https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md

DSSE signs a pre-authentication encoding containing both:

- the payload type;
- the exact payload bytes.

A central design benefit is that the signature scheme does not need to depend on parsing or canonicalizing the payload before signature verification.

The in-toto attestation envelope guidance recommends DSSE v1.0 and also emphasizes support for multiple signatures and authenticated payload type.

### Why this fits Activity Receipt research

A future Activity Record can remain a JSON artifact while the attestation layer treats those exact record bytes as an opaque signed payload.

That separates:

1. **record semantics** — schema, authority, events, provenance, verification;
2. **serialization** — the exact bytes of one record artifact;
3. **authentication** — the envelope/signature over those bytes;
4. **trust policy** — whether a particular signer/key is trusted for a particular role.

That separation is cleaner than inventing project-specific signature fields inside the JSON record.

---

## Candidate design direction

The current recommendation is:

### Keep the existing digest as a non-authenticated content binding

The project-local SHA-256 record hash remains useful for:

- deterministic tests;
- Receipt-to-record equality checks;
- change detection;
- lineage experiments.

It should continue to be labeled as a project-local digest profile.

### Do not invent a custom signature format

A future signature/attestation implementation should use an established envelope format rather than adding fields such as:

```text
signature
public_key
signed_hash
```

directly to the Activity Record without a standard verification model.

### Prefer an external attestation envelope

A candidate architecture is:

```text
Evidence substrate
      |
      v
Canonical Activity Record (JSON artifact)
      |
      +--> SHA-256 content binding
      |
      +--> established attestation envelope (candidate: DSSE)
                    |
                    +--> exact payload bytes
                    +--> authenticated payload type
                    +--> one or more signatures
                    +--> external trust/key policy

Canonical Activity Record
      |
      v
Deterministic Activity Receipt
      |
      +--> derived_from_record_hash
      +--> optional future attestation reference
```

The Receipt should reference attestation evidence rather than pretending that the Receipt itself proves signer identity.

---

## Payload type

If DSSE is implemented, the project should define a stable media/payload type only after the record versioning model is sufficiently stable.

A placeholder must not be presented as an IANA-registered media type or in-toto predicate.

Likewise, the project should not use:

```text
application/vnd.in-toto+...
```

unless it actually adopts the in-toto Statement/predicate model required by that ecosystem.

---

## Signer identity and trust are separate problems

A valid digital signature only establishes that a holder of a particular signing key produced the signature.

It does not automatically establish:

- the legal identity of the signer;
- that the signer was authorized to attest to the action;
- that the signer was uncompromised;
- that the key was valid at action time;
- that a human approved the action;
- that the underlying event actually occurred.

A production design therefore needs an explicit trust model covering questions such as:

- Which keys/identities may sign agent records?
- Which keys represent a human principal, deployer, agent service, verifier, or auditor?
- How are keys issued and rotated?
- How are compromised/revoked keys handled?
- Is signer identity organization-managed, workload-bound, certificate-backed, or something else?
- Which signatures are required for which claims?

Those questions should not be hidden behind a generic `signature_valid: true` field.

---

## Multiple attestations

A useful long-term model may allow different parties to attest to different evidence roles.

Examples:

- an agent runtime attests to emitted execution telemetry;
- an authorization service attests to the policy decision;
- a verifier attests to post-action verification;
- a repository attests that a particular record was ingested;
- an external content-provenance system attests to a produced media asset.

These attestations should remain distinguishable.

One signature should not silently stand in for all roles.

---

## C2PA relationship

C2PA remains complementary when a workflow creates or consumes media/content assets.

Reference:

https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html

A future Activity Record may point to a C2PA manifest or validation result as evidence associated with an asset.

That does not make an AI Activity Record a C2PA Content Credential, and a record signature does not make an asset C2PA-conformant.

---

## Replay and freshness

A valid signature over an old record can still be stale.

Future attestation verification needs to consider:

- record version;
- generation time;
- authority window;
- signer/key validity period;
- revocation state;
- expected trace/run identity;
- superseding record hashes;
- optional previous-record-hash lineage;
- whether a newer record exists.

Cryptographic validity and current operational validity are separate.

---

## Candidate verification pipeline

A future verifier should conceptually perform checks in this order:

1. Parse the attestation envelope.
2. Validate envelope structure and payload type.
3. Verify the cryptographic signature(s).
4. Apply signer/key trust policy.
5. Recover the exact Activity Record payload.
6. Validate the Activity Record JSON/schema.
7. Run canonical-record semantic checks.
8. Recompute the project record digest if that binding is used.
9. Derive or load the Receipt.
10. Confirm `derived_from_record_hash` matches the verified record.
11. Run Receipt schema/invariant checks.
12. Evaluate freshness/revocation/supersession rules.
13. Report each verification layer separately.

A verifier should not collapse all of these steps into one boolean.

---

## Candidate trust policy now defined

The repository now separately defines the research-level prerequisites that this document previously left open:

- signer roles and identity mapping;
- external verification material;
- private-key/key-rotation/compromise rules;
- a project-controlled Activity Record payload-type URI;
- exact-payload-byte semantics for DSSE;
- required signer roles and signature threshold;
- production rejection of test-only identities;
- fail-closed production behavior for unknown revocation status;
- the rule that DSSE `keyid` is only a lookup hint, not authenticated identity;
- the rule that signature validity does not replace action authorization.

See [ATTESTATION-TRUST-POLICY.md](ATTESTATION-TRUST-POLICY.md) and [PAYLOAD-TYPES.md](PAYLOAD-TYPES.md).

The machine-readable research policy is validated in CI. This clears the **design prerequisite** for a future test-only cryptographic prototype; it does not clear the operational prerequisites for production signing.

---

## Required adversarial tests before any signing claim

A future implementation should include at least:

- valid envelope + trusted signer;
- valid envelope + untrusted signer;
- payload byte mutation;
- payload-type mutation;
- signature byte mutation;
- wrong public key;
- truncated/malformed envelope;
- duplicate or multiple signatures;
- revoked signer/key;
- stale but correctly signed record;
- record with invalid schema;
- record with semantic invariant failure;
- Receipt derived from a different record hash;
- previous-record-hash lineage mismatch;
- content-equivalent JSON with different bytes, to make the exact-byte semantics explicit.

The current research prototype automates most of these local/adversarial cases, including exact-byte mutation, payload-type/signature/key mutation, malformed envelopes, duplicate signatures, invalid records, Receipt mismatch, and signer validity windows. Real revocation services, protected production keys, trusted timestamps, and deployment trust roots remain external/production gates.

No production cryptographic trust claim should be published until those operational layers are implemented and reproducibly verified.

---

## Current decision

For the present research stage:

- **keep** the current SHA-256 record binding;
- **keep labeling it project-local and non-authenticated**;
- **do not claim JCS**;
- **do not add custom signature fields**;
- **treat DSSE/in-toto-style external envelopes as the leading candidate for future authenticated records**;
- **keep production signing blocked until real identity issuance, protected key storage, revocation/status infrastructure, deployment trust roots, and an appropriate trusted-time/history strategy exist**;
- **continue testing the research-only DSSE signing/verification prototype with ephemeral test keys and the candidate trust policy**.

This is intentionally conservative. The next implementation should add cryptography only when the project can test the trust semantics around it, not merely because producing a signature is technically easy.


---

## Executable research prototype

The repository now includes a research-only DSSE v1 + Ed25519 signing/verification prototype using ephemeral in-memory test keys and the machine-readable trust policy.

See [DSSE Signing / Verification Prototype](DSSE-PROTOTYPE.md).

The prototype verifies exact payload bytes, signer policy/role/validity, record schema and semantics, deterministic Receipt derivation, and record/Receipt binding. It also includes adversarial cases for payload/signature/key/type mutation, malformed envelopes, duplicate signatures, invalid records, Receipt mismatch, and expired signer validity.

This remains test-only cryptographic evidence. No production key, trust root, revocation service, or trusted timestamp is deployed.
