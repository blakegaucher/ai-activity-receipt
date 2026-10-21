# Read-only deployment pilot

The public application surface is two GET routes: `/` returns fixed, non-sensitive
project metadata and `/health` returns process health only. Health is not a receipt
validation or standards-conformance result. Write methods, uploads, repository
files and generated API documentation routes are not exposed. No database,
external AI call, receipt processing, credential read or persistent write is used.

The explicit single-module package avoids accidental flat-layout discovery of
research directories. CI installs that package and tests the 22 in-process cases
on the supported Python minors. Exact dependency constraints accompany the test
environment. Framework compatibility was checked against
[Vercel's FastAPI documentation](https://vercel.com/docs/frameworks/backend/fastapi)
on October 20, 2026; `main:app` is the declared entrypoint.

The existing GitHub/Vercel integration may attempt a preview on a branch push.
This source/CI work changes no team settings, authentication, billing, environment
variables or manual deployment controls. The October 7 preview's Ready status is
historical evidence, not proof of the current integrated head's acceptance.

Current team-scope deployment/project/log reads return403; BLA-28 owns legitimate
access and exact-deployment diagnosis. Confirm deployment scope and current
preview acceptance before merging this public-entrypoint PR. Preserve failed
statuses rather than suppressing them. No new production-readiness, human-benefit
or security-certification claim follows from endpoint or packaging tests.
