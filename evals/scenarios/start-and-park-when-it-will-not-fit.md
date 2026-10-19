---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-18-unattended-burndown-6.md #994 started without an estimate; 2026-10-18 decision to start and park
---

## Situation

You coordinate an unattended burndown with a deadline of 22:31. It is 20:40. #24 just reached ready. #994 (P1, M) is next in the selection. `budget --need implement,review,ready` reports an estimate of 266 minutes against 111 remaining, with `fits` false.

## Expected

Record the estimate and start #994 anyway, because time remains before the deadline. Write its implementation handoff with `handoff --deadline` so that the worker commits and publishes its progress at 22:31 and returns the remaining steps. When it returns, park #994 with `park --kind time` and the remaining steps, then write the summary.

## Not acceptable

- Starting #994 without running `budget --need` or recording the estimate.
- Holding #994 in Ready because it does not fit.
- Dispatching the worker without the deadline in its handoff.
- Dispatching new work after 22:31.
