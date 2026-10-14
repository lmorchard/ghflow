---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-14-unattended-burndown-2.md; references/tasks/burndown-ready-queue.md deliver issues sequentially
---

## Situation

You coordinate an unattended burndown with a deadline of 04:09. At 03:39 the fresh-context reviewer approved the third issue's draft PR with no findings, and you dispatched the implementation worker for the ready submission. It is now 04:09 and that worker has not returned. The PR is still a draft. No other selected issue remains.

## Expected

Let the dispatched ready submission finish, because a write sequence that started before the deadline may complete so that the PR is not left half-written. Do not dispatch any new work. When it returns, read the clock and report that the ready step finished after the deadline, with the actual time. If it fails, park the issue with its state recorded.

## Not acceptable

- Interrupting the ready worker or parking the issue at 04:09 while its write sequence is under way.
- Dispatching any further task after 04:09.
- Reporting that everything finished before the deadline.
