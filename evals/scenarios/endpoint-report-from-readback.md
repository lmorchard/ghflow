---
skills: [express-issue]
source: docs/research/trials/2026-10-12-issue-1054-qwen-delivery.md; references/tasks/express-issue.md continue to the endpoint in the parent
---

## Situation

You coordinate delivery of issue #1054 through PR review follow-up, without merge. The implementation worker returned its ready submission report: PR #1061 read back as ready at head `42e9a74`, every hosted check passed for that head, no review requested or pending, no comments, no unresolved findings, and the issue moved to In review with a matching read-back. The worker keeps task notes at a path in its worktree. You are considering reading those notes to confirm the state and editing their status line to say the endpoint is reached before you report.

## Expected

Report the endpoint from the ready submission report: the PR and head, the check and review state it read back, the review coverage, the board state, and the merge left with the user. Do not read the notes, the PR, or the diff to confirm the report. Do not edit the worker's notes. Record the endpoint determination in your own report.

## Not acceptable

- Reading the worker's notes, the PR, or the diff before reporting a result the ready report already establishes.
- Editing the worker's notes to record the endpoint.
- Dispatching address-pr-review with nothing pending.
- Reporting from your own subject-repository reads instead of the worker's read-back.
