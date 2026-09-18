# Project Payload Type Identifiers

> **Status:** Project-local identifiers for research prototypes.  
> These are URIs controlled by this repository. They are not IANA-registered media types and do not imply in-toto predicate conformance.

## Activity Record candidate-record-v0.1

Identifier:

```text
https://github.com/blakegaucher/ai-activity-receipt/blob/main/docs/PAYLOAD-TYPES.md#activity-record-candidate-record-v01
```

Meaning:

- the DSSE payload contains the **exact bytes** of one JSON Activity Record artifact;
- after signature verification, the payload is parsed as JSON;
- the parsed object must declare `record_schema_version = "candidate-record-v0.1"`;
- the object must pass `activity-record.schema.json` and the canonical-record semantic checks;
- the existing project-local deterministic record hash may then be recomputed from the parsed object as a separate content-binding layer.

The DSSE signature is over exact payload bytes through DSSE pre-authentication encoding. The project-local SHA-256 record hash is over deterministic serialization of the parsed JSON object.

These are intentionally distinct semantics.

Changing pretty-printing or JSON member order can therefore change a DSSE signature over the artifact bytes while preserving the project-local record digest after parsing.

## Versioning rule

A schema/profile change that alters how a verifier interprets the signed payload requires a new payload-type identifier.

Do not reuse this identifier for a future `candidate-record-v0.2` or production profile.


## Research implementation

The payload type above is exercised by `research/dsse_prototype.py`.

The prototype signs the exact bytes of a candidate-record-v0.1 JSON artifact using DSSE v1 PAE and an ephemeral Ed25519 test key, then independently validates the parsed record and deterministic Receipt.

See [DSSE-PROTOTYPE.md](DSSE-PROTOTYPE.md).
