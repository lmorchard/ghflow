---
skills: [express-issue]
source: docs/research/trials/2026-10-13-unattended-burndown.md; references/shared/triage-labels.md parked deliveries
---

## Situation

The user asks you to deliver issue #1006 through PR review follow-up, without merge. An unattended run parked it last night when its time budget ended: draft PR #1067 at a green head, the first review clean, accepted corrections committed, and an issue comment listing the remaining steps, a fresh re-review and the ready submission. The issue carries `triage:needs-input` and the board shows In progress. The comment asks no question, and nothing on the issue or PR is unresolved.

## Expected

Resume from the PR evidence instead of starting new work. Because the park was for time and no question is open, replace `triage:needs-input` with `triage:ready` before the next dispatch. Then dispatch the fresh re-review of the current head and continue to the ready submission with the implementation worker. Do not route the issue through sweep-needs-input.

## Not acceptable

- Leaving `triage:needs-input` on the issue while delivering it, or removing it only at the end.
- Sending the issue to sweep-needs-input or asking the user a question when none is open.
- Starting a new branch, worktree, or PR.
- Marking the PR ready without the fresh re-review of the corrected head.
