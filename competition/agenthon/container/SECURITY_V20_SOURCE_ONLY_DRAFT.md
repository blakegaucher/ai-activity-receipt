# Agenthon T4 security v20 — SOURCE-ONLY DRAFT / NOT EXECUTED

Purpose: address the critical advisory discovered in the separately preserved v19 audit. Do not back-edit its contents or historical Docker evidence.

Source parent: f907c578e97093221d282a92bc56c6b8daa694ae.
Official Track 4: 5d3b726a49b8ea218543e4d24319895874dcff6e (unchanged).
Toolkit v2.6.0: bd01548e34d21fd660d88fd06157078fb25ece4e (unchanged).
Historic base: python:3.13.15-slim@sha256:37134a49d21d2120e4c4d73bb76f8a4ab9aef31f096f7ec2ead48c2feead4332 (unchanged historically).
Proposed v20 base: python:3.13.16-slim@sha256:8fb4cfa1a2616d7b8e0c2175cc6ad68f5729c34ea8488c0b360d2934b7be9024 (Docker Hub, SHA-verified linux/amd64 child manifest, Python 3.13.16 config, no volumes).
Official Python 3.13.16 security release: https://www.python.org/downloads/release/python-31316/
v19 audit archive SHA-256: a04c3b3b773deb97f0ddb973e7d5e1261172ab6a2ed057e16bbb04d9b26c0944.
Frozen worked-example answer SHA: e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2.
Analysis schema SHA: 8a997f21a929f09596db805430839b281548ad0babab29bd1f3daa8456d38049.

Changes limited to base digest and Python version assertions, manual workflow branch guard and corresponding synthetic tests; no scoring or modeling changes.

NO NEW LIVE DOCKER RUN APPROVED. This is not merged, built, registry-published, team-claim packed, CodaBench uploaded or scored.
Historical five public-unit evidence failures/17 wrong-entity citations remain open. The v19 1 Critical and 70 High scanner matches and unresolved inherited license obligations do not become clean merely by updating Python.
Separate owner decisions are required for new Docker execution, full image audit, publication, private Team Key/proof and submission. Development last run START cutoff 2026-10-12T20:00Z.
