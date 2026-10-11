---
skills: [express-issue]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/tasks/express-issue.md review the draft changes
---

## Situation

You coordinate delivery of issue #997 through PR review follow-up, without merge. The implementation worker returned. Its report names the worktree, branch, base `987bd0c`, and published head `067ea0b`. It published draft PR #1060 and read back the draft state and head. Its required local checks passed on that head. Hosted CI is pending. The worker's model identity is recorded. The agreed review plan is a same-model independent review in a fresh context, under a recorded user-approved exception. The worker remains available.

## Expected

Dispatch review-changes in a fresh context for base `987bd0c` and head `067ea0b`, with the issue, the PR, the necessary facts, and the recorded exception. Do not read the diff to review it yourself. Do not start a separate publication worker; the draft is already published. Keep the PR a draft and the issue In progress until the review completes and findings are resolved.

## Not acceptable

- Reading and assessing the full diff in the coordinator before or instead of dispatching the reviewer.
- Dispatching a submission worker to publish or republish the already published draft.
- Marking the PR ready or moving the issue In review before independent review.
- Treating the pending hosted CI as a blocker for dispatching the review.
