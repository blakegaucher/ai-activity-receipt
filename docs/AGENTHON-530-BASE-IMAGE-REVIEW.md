# Agenthon 5.3.0 base-image availability correction — source-only draft

## Executive summary (read this first)

Run [38124068960](https://github.com/blakegaucher/ai-activity-receipt/actions/runs/38124068960) built the public baseline image successfully, then failed to inspect the frozen base reference with `No such image`. This draft explicitly pulls the same immutable Linux/amd64 base by its canonical name-and-digest reference, inspects it, and applies the base VOLUME guard before building the candidate. The candidate VOLUME guard remains before every container execution, and the public baseline's MIT notice is included in the build context and image. Mocked tests cover the correction and preserved boundaries, but cannot prove Docker execution or competition compatibility. This is a draft-only source correction, not permission to merge, dispatch, publish, package, submit, or retry a historical run.

## Evidence and scope

The observed failure is at the former helper line 160. The successful build exported local candidate ID `sha256:b282782aa6f1acac639bd80a71a120a610450a3e4d5de03b9dc9d82600711144`; that identity is from the BuildKit export log, not successful image inspection or a participant registry manifest. Neither image's `Config.Volumes`, container Python, answer bytes, schema validation, claim findings, nor post-run input integrity were observed. The exact printed failure report SHA-256 is `ad1c12d4ca33bcfd888ac5e4f5fdc872f12801361a601818a4954400fa09edfc`.

The helper assumed successful build-time resolution made the exact base reference available for daemon inspection. This draft removes that assumption; it does not assert an independently observed cause inside BuildKit's storage. [Docker's pull documentation](https://docs.docker.com/reference/cli/docker/image/pull/) documents immutable `NAME@DIGEST` pulls and platform selection. The canonical `python@sha256:...` pull/inspect reference names the **same frozen digest** as the unchanged `python:3.13.15-slim@sha256:...` build argument. No moving tag, alternate image, skipped inspection, fallback, or retry is added.

## Unchanged controlling pins

| Control | Exact value |
|---|---|
| Owner main / parent | `f5fcbcb54afe9104be1a4a38f5886b9a23b3253a` |
| Historical 5.3.0 execution branch head | `6067dd4478debc93c1aff62b2c98572abe5c0487` |
| Official Track 4 / scorer 5.3.0 | `5d3b726a49b8ea218543e4d24319895874dcff6e` |
| Toolkit v2.5.1 peeled commit | `50fb2dc2b39c70f4cf81fcd269943782eddfaed0` |
| Python base | `python:3.13.15-slim@sha256:37134a49d21d2120e4c4d73bb76f8a4ab9aef31f096f7ec2ead48c2feead4332` |
| Frozen answer SHA-256 | `e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2` |
| Frozen schema SHA-256 | `8a997f21a929f09596db805430839b281548ad0babab29bd1f3daa8456d38049` |

Stop if a controlling revision advances. Do not install the moving toolkit main or relabel older local checks as scorer 5.3.0 production parity.

## Narrow changes

1. `container_gate.py`: validate the original exact base pin, pull its canonical immutable reference once with a 60-second bound, inspect and record it, reject declared volumes and a wrong platform before build. Copy the license from the same pinned public Track 4 checkout. Preserve failure events, the final evidence report and cleanup behavior.
2. `Dockerfile`: copy only the public baseline's `LICENSE` notice in addition to the existing baseline files. No corpus, task, model, customer, or private research data is added.
3. `test_container_gate.py`: 21 standard-library mocked regression tests; every subprocess is patched, including a fail-closed default. Synthetic image IDs are not execution evidence.
4. `validate-receipts.yml`: retain compilation of the full Agenthon container directory and add only those mocked tests. Other validation and CodeQL behavior are unchanged.
5. `agenthon-container-smoke.yml`: retain the sole manual trigger and all repository, public-repository, confirmation and exact-approved-commit guards; bind execution only to the new isolated branch `competition/agenthon-container-530-base-load-draft`.
6. This new review record. Earlier review documents and failure records are not edited.

Base inspection and rejection now occur earlier than in the historical helper. Candidate checks, offline runtime (`--network none`), read-only/non-root input handling, capabilities, CPU/memory/PID limits, answer-byte equality, schema and claim gates remain intact. The baseline implementation and the sole public exemplar `t4-EXAMPLE-eps-beat` are unchanged. The original Dockerfile's no-default build-argument warning was nonfatal and is not the diagnosed defect.

## Verification boundary

The mocked suite checks a cold local store requiring a pull before inspection, exact reference/platform/timeout, pull and inspection failure preservation without retries, malformed inspection data, both roles' VOLUME rejection, frozen pins and hashes, exact historical token-boundary wording, execution ordering, workflow guards, resource/network settings, license inclusion, cleanup failure preservation and symlink rejection. Run it without Docker:

```bash
python -m compileall -q competition/agenthon/container
python -m unittest discover -s competition/agenthon/container -p 'test_container_gate.py' -v
python -O -m unittest discover -s competition/agenthon/container -p 'test_container_gate.py' -v
```

Local verification on Python 3.12 is syntax/mocked verification only. The separately approved runtime continues to require host and container Python 3.13.15. A future exact-head smoke remains necessary to establish actual daemon inspection, volumes, runtime, output, claim checks, integrity and cleanup. Neither that smoke nor these tests measure an official competition score.

## Authority and stop conditions

| Lane | Status | Authority | Allowed next action | Protected boundary |
|---|---|---|---|---|
| Source correction | Draft only | October 11 source-only continuation | Review exact diff and ordinary required CI | No merge without separate explicit approval |
| Historical runs | Preserved, attempt 1 | Evidence preservation | Read run 38124068960, skipped 38119659983 and failed 37746247914 | No rerun, overwrite or retry |
| New container smoke | Closed | Previous one-additional-run grant consumed | Prepare a new exact-head approval after review/merge | No dispatch or Docker execution now |
| October 9 grant | Unused, stale pins | Historical record only | Preserve its original scope | Not transferable to this branch/source |
| Competition submission | Not ready | Read-only readiness review | Resolve publication/package/account gates separately | No registry publication, Team Key, packaging, upload, attempt or spending |
| Other protected lanes | Closed | No new authority | None | No Stage 2 or ARC work |

Only the new isolated branch may change in this draft. The original `competition/agenthon-container-530-pin-draft` must remain at its recorded head. All historical evidence, protocols, frozen answer/schema controls and existing unrelated repository work remain intact.
