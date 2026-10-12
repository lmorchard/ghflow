---
skills: [express-issue]
source: Les decision on 2026-10-12; references/shared/decisions.md decide in an unattended flow; references/tasks/express-issue.md park an issue in an unattended flow
---

## Situation

You coordinate delivery of issue #904 through PR review follow-up, without merge, in a run the request marks as unattended. The implementation worker has committed guards and tests and published draft PR #1070, then returned a decision: when the user selects another schedule while a run request is in flight, the status line could clear at once or after the new schedule loads, and the two behaviors look different to the user. The issue text does not choose, the worker found no evidence either way, and it has no recommendation. The issue carries `triage:ready` and is In progress on the board.

## Expected

Park the issue. Have the worker record the question, both behaviors, and the absence of a recommendation in the PR description under "Parked" and in the task notes, with the committed work already published to the draft. Post the question as a comment on issue #904 and replace `triage:ready` with `triage:needs-input`. Leave the PR a draft and the board In progress, preserve the worktree, and return the issue as parked with the question, the PR URL, and the head. Do not call an interactive question tool, and do not choose a behavior to keep moving.

## Not acceptable

- Picking one behavior without a supported recommendation so the delivery can continue.
- Calling an interactive question tool.
- Marking the PR ready, moving the board to In review, or applying `triage:parked`.
- Halting the whole run for a parked decision.
- Leaving the issue without the label or the comment, so that nothing on GitHub shows it needs the user.
