## Executive summary (read this first)

This draft advances the participant interface candidate to the reviewed Track 4 source at scorer 5.3.0. It preserves the minimal public baseline, exemplar, Dockerfile, toolkit v2.5.1 selection and frozen answer/schema hashes. The upstream scoring and image-access rules changed materially, so this source review does not establish a Development score or production parity. The October 9 one-run approval remains unused and attached to the old exact head and upstream pin; it does not authorize this candidate. Review stops before merge, Docker execution, manual workflow dispatch or any publication or competition submission.

### Exact source selection

| Item | Previous selection | Draft selection |
| --- | --- | --- |
| Track 4 commit | `458bc07efc05983de342ccb371e2b3cd793d621f` | `5d3b726a49b8ea218543e4d24319895874dcff6e` |
| Scorer declaration | 5.2.2 | 5.3.0 |
| Participant branch guard | `competition/agenthon-container-522-syntax-fix` | `competition/agenthon-container-530-pin-draft` |
| Toolkit v2.5.1 commit | `50fb2dc2b39c70f4cf81fcd269943782eddfaed0` | unchanged |

The [exact official comparison](https://github.com/Agenthon-2026/track4-analysis-public/compare/458bc07efc05983de342ccb371e2b3cd793d621f...5d3b726a49b8ea218543e4d24319895874dcff6e) contains three commits and 27 changed paths. The candidate's Python helper changes only its Track constant and report scope string. Its manual workflow changes only the Track checkout pin and the exact branch name in its input description and job guard. The Dockerfile and all other workflow guards remain unchanged. The original corrected branch and historical failure remain untouched.

### Compatibility findings

| Official change | Consequence for this draft |
| --- | --- |
| First 20 claims per entity, in answer file order, contribute to claim checks and F/T counts | No baseline edit is indicated: its unchanged source creates at most one claim per entity. This is a source inference, not a newly generated answer or score. |
| Later claims are ignored for per-claim judging; schema and structural citation/date checks still cover every claim | Do not drop structural checks or treat ignored claims as exempt from admission requirements. The helper's deterministic-finding allowlist remains unchanged. |
| Development uses the pinned production NLI judge, including contradiction checking | Existing local preview evidence cannot attest current Development results. With a judge spec configured, the Development factory uses production judging but stamps results non-rankable. A signed plan without a judge spec faults; participant-local lexical preview remains a separate path. No NLI/tokenizer/model execution is performed here. |
| Judge may select CPU/GPU, stays loaded once per process, and bounds long premises before tokenizing | These are organizer-side source changes. Upstream numerical-equivalence claims were not reproduced here; the candidate adds no judge assets, device selection or scoring call. |
| No private-image submission route | Development and Final images must be anonymously pullable. Old toolkit image-access fields or mirror guidance do not confer a route. Public image contents need a separate licensing/IP/privacy review before any publication. |
| Final uploads close October 25 at 23:59 AoE; runs and verification may finish later | Keep a submitted image pullable until results publication. This does not extend Development deadlines or authorize an upload. |

The complete minimal-baseline subtree (six files), wrapper and exemplar subtree (five files) have identical Git blobs across the two official revisions. The Track dependency declaration remains `qfbench2-common>=2.5.0,<3`; the selected 2.5.1 toolkit satisfies that declared range. This metadata check does not prove runtime compatibility. Moving toolkit main is deliberately not substituted for the selected tag.

Frozen expected answer SHA-256: `e305c47d7dfca92e73b3304d24f937b26f0bf861082649e06629c92eae91b3d2`.

Frozen Analysis schema SHA-256: `8a997f21a929f09596db805430839b281548ad0babab29bd1f3daa8456d38049`.

Both remain byte controls for a future separately authorized check. No fresh answer, schema verdict on a generated answer, claim verdict, container image identity, Config.Volumes observation or competition score is produced by this review.

### Verification and controls

Source-only verification covers fetched Git blob identities, the official diff, Python syntax/compilation, YAML structure, the permitted helper/workflow edits, unchanged token-boundary wording, unchanged frozen pins and Dockerfile, and intact execution/resource/network/cleanup guards. Compilation uses Python 3.12.14; the future container's Python 3.13.15 has not been run. The Track package declares Python >=3.13, so compilation is not an import/runtime or NLI compatibility result. The existing receipt CI compiles `competition/agenthon/container`; ordinary PR validation and CodeQL provide separate evidence for this draft when completed.

The workflow still requires a manual event, the exact repository and branch, `github.sha == inputs.approved_commit`, `CONTAINER_ONLY`, and a public owner repository. The helper still stops before Docker if official Track main differs from its exact pin. Both base and candidate nonempty Docker Config.Volumes are rejected before container execution. The public-only sparse checkout/build context, offline flags, non-root/read-only container, resource limits, unchanged hashes, and cleanup/failure preservation remain intact.

| Lane | Status | Authority | Allowed next action | Protected boundary |
| --- | --- | --- | --- | --- |
| Agenthon 5.3.0 source candidate | Draft only | Source-drift review and isolated pin advance | Review diff and static/ordinary PR CI evidence | Stop before merge or execution; stop on further official revision change |
| Historical October 9 smoke grant | Unused; old source pin is stale | Existing exact-head grant with stop-on-drift clause | Preserve as historical authority | Do not consume, transfer or renew it through this draft |
| Competition submission | Closed | No publication/submission authority in this review | Read published requirements | No registry publication, Team Key, CodaBench submission, Development attempt or Stage 2 |

No private AIAR research/customer material enters this candidate. ARC work remains outside its scope. A future merge and any new exact-head smoke decision require separate owner authority under the current source selection.

Sources: [5.3.0 scorer commit](https://github.com/Agenthon-2026/track4-analysis-public/commit/11852111d268766fef7772ce5edfaccc1718c763), [public-image policy commit](https://github.com/Agenthon-2026/track4-analysis-public/commit/277cb8601360ca1faa3db4fb882520a37e2e6f7e), [Final timing commit](https://github.com/Agenthon-2026/track4-analysis-public/commit/5d3b726a49b8ea218543e4d24319895874dcff6e), [current alignment](https://github.com/Agenthon-2026/track4-analysis-public/blob/5d3b726a49b8ea218543e4d24319895874dcff6e/qfbench2_track_analysis/alignment.py), [current scorer](https://github.com/Agenthon-2026/track4-analysis-public/blob/5d3b726a49b8ea218543e4d24319895874dcff6e/qfbench2_track_analysis/scoring.py), [current submission contract](https://github.com/Agenthon-2026/track4-analysis-public/blob/5d3b726a49b8ea218543e4d24319895874dcff6e/SUBMISSION_CLI.md), and [preserved historical failure](https://github.com/blakegaucher/ai-activity-receipt/actions/runs/37746247914).
