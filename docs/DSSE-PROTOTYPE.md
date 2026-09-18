# DSSE Signing / Verification Prototype — Research v0.1

> **Status:** Test-only cryptographic research prototype.  
> **Snapshot:** 2026-09-18  
> This is not production key management, a production trust root, non-repudiation, or proof that underlying activity occurred.

The repository now contains a narrow executable prototype for signing and verifying exact canonical Activity Record bytes with a DSSE v1 envelope and an Ed25519 test key generated only in process memory.

Files:

- `research/dsse-envelope.schema.json`
- `research/dsse_prototype.py`
- `research/attestation-trust-policy.schema.json`
- `research/attestation-trust-policy.example.json`
- `docs/PAYLOAD-TYPES.md`

## What is implemented

The prototype performs these layers in order:

1. validate the machine-readable trust policy;
2. validate the constrained DSSE envelope structure;
3. require a payload type recognized by the trust policy;
4. reconstruct DSSE v1 pre-authentication encoding (PAE);
5. verify one or more Ed25519 signatures;
6. map a verified key to a trusted signer through the policy's verification-material reference;
7. enforce signer role, validity window, environment, signature threshold, and required-role rules;
8. decode the authenticated payload bytes as UTF-8 JSON;
9. require the Activity Record schema version associated with the payload type;
10. validate canonical-record JSON Schema;
11. run canonical-record semantic checks;
12. deterministically derive the Activity Receipt;
13. validate Receipt schema/invariants;
14. recompute and verify the project-local canonical-record hash binding;
15. optionally require a separately supplied Receipt to equal the deterministic derivation from the signed record.

## Exact-byte DSSE semantics

The implementation uses DSSE v1 PAE:

```text
"DSSEv1" SP len(payloadType) SP payloadType SP len(payload) SP payload
```

The lengths are byte lengths, encoded as base-10 ASCII.

The DSSE signature therefore authenticates:

- the payload type;
- the **exact payload bytes**.

This is intentionally different from the project-local record digest.

The record digest is computed after JSON parsing over the project's deterministic JSON serialization profile.

As a result, two JSON files with identical parsed content but different whitespace/member formatting can have:

- the same project-local record digest;
- different DSSE signatures.

The self-test requires this distinction.

## Key identity and `keyid`

The DSSE envelope includes `keyid`, but this project treats it only as a lookup hint.

Verification works conceptually as:

```text
keyid
  -> candidate signer entry in trusted policy
  -> signer verification-material URI
  -> trusted public key supplied to verifier
  -> cryptographic signature check
  -> signer role / trust-policy evaluation
```

A matching `keyid` with the wrong private key fails.

An unknown `keyid` fails.

The prototype does not equate `keyid` with authenticated identity.

## Private-key handling

The repository contains no static private key for this prototype.

The self-test creates an ephemeral Ed25519 private key in process memory:

```python
Ed25519PrivateKey.generate()
```

The public half is supplied to the verifier through the policy's verification-material lookup path.

This is suitable for a research self-test only.

A production signer would require protected key storage, identity issuance, rotation, compromise response, revocation/status infrastructure, and deployment trust roots.

## Adversarial coverage

The self-test requires one valid signed record and negative cases for:

1. unknown/untrusted `keyid`;
2. correct `keyid` but signature from the wrong private key;
3. exact payload-byte mutation with JSON-semantic equivalence;
4. payload-type mutation;
5. signature-byte mutation;
6. wrong trusted verification key;
7. malformed/truncated envelope;
8. duplicate signatures from the same key;
9. correctly signed but schema-invalid Activity Record;
10. correctly signed but semantically invalid Activity Record;
11. Receipt bound to a different Activity Record;
12. signer outside its configured validity window.

The PAE helper is also checked directly, including a non-ASCII payload-type byte-length case.

Run:

```bash
python research/dsse_prototype.py
```

## What a valid result means

A passing result means:

- an exact byte sequence was signed with a test-only key;
- the signature matched a public key supplied through the research trust-policy path;
- the signer was permitted by the research policy at the supplied verification time;
- the signed bytes decoded to a valid candidate Activity Record;
- the record passed current semantic checks;
- the derived Receipt was internally valid and bound to that record.

It does **not** mean:

- the signer has a real-world identity;
- the signer was legally or operationally authorized;
- the underlying events are true;
- the evidence substrate is complete;
- the record was not maliciously fabricated before signing;
- the key was hardware-protected;
- revocation was checked against a real service;
- a trusted timestamp exists;
- production non-repudiation has been established.

## Current implementation boundary

This prototype clears the roadmap item for a **research-only DSSE signing/verification prototype with test-only keys and adversarial verification cases**.

Production signing remains open and separately gated.

The next useful cryptographic work should not be "more signatures" in isolation. It should connect the prototype to a real identity/key lifecycle in a controlled pilot, or add external verification interoperability against an independent DSSE implementation.
