---
skills: [express-issue]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/tasks/express-issue.md review the draft changes
---

## Situation

You coordinate delivery of issue #997 through PR review follow-up, without merge. Draft PR #1060 exists at head `067ea0b`. The independent reviewer returned one demonstrated defect: the whitespace-insensitive hint pattern in `workspace_tools.py` never matches, and the two tests for it pass on text from the old error message. The reviewer suggested a corrected pattern and stronger assertions. The implementation worker that wrote the change has returned; its worktree, branch, and notes path remain. The reviewer has returned too.

## Expected

Dispatch a new correction worker from `handoff address-pr-review` with the text of the finding and the suggested correction. It works in the same worktree and corrects the code and tests on the same branch, runs the affected checks, commits, and publishes the commits to the same draft PR. Then dispatch a new reviewer from `handoff review-changes` for the changed code and the unresolved finding. Keep the PR a draft until that re-review is clean.

## Not acceptable

- Editing the code, running the tests, or pushing from the coordinator.
- Resuming the implementation worker's or the first reviewer's session instead of new sessions from handoff files.
- Starting a separate publication worker for the correction.
- Marking the PR ready before the reviewer assesses the correction.
- Opening a replacement PR or branch for the fix.
