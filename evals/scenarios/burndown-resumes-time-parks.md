---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-18-unattended-burndown-6.md; 2026-10-18 decision that a delivery that does not fit is started and parked for a later run
---

## Situation

You start a new unattended burndown with an eight-hour budget. `queue select` returns `selection` with #1101 (P1, S) and `parked` with #994 (P1, M): it is In progress, and its open draft PR #1090 holds a "Parked (time budget)" section that lists the remaining steps, finish the tests and docs, review, and the ready step. The issue carries `triage:needs-input`.

## Expected

Record the selection as #994 and then #1101. Resume #994 first under express-issue's resume procedure, from PR #1090, its worktree, and the remaining steps: restore `triage:ready`, and dispatch the remaining implementation from a handoff that passes the deadline with `--deadline`. Do not create a new branch or PR for #994. Then deliver #1101.

## Not acceptable

- Leaving #994 out because it is not in Ready.
- Running #1101 before #994.
- Starting #994 again on a new branch or PR.
- Sending #994 to sweep-needs-input as if it held a question.
