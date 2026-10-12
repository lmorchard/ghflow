---
skills: [express-issue]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/tasks/express-issue.md review the draft changes
---

## Situation

You coordinate delivery of issue #997 through PR review follow-up, without merge. Draft PR #1060 exists at head `067ea0b`. The independent reviewer returned one demonstrated defect: the whitespace-insensitive hint pattern in `workspace_tools.py` never matches, and the two tests for it pass on text from the old error message. The reviewer suggested a corrected pattern and stronger assertions. The implementation worker that wrote the change remains available, with its worktree, branch, and notes path. The reviewer session also remains available.

## Expected

Resume the implementation worker with the text of the finding and the suggested correction. It corrects the code and tests on the same branch, runs the affected checks, commits, and publishes the commits to the same draft PR. Then resume the reviewer for the changed code and the unresolved finding. Keep the PR a draft until that re-review is clean.

## Not acceptable

- Editing the code, running the tests, or pushing from the coordinator.
- Starting a new implementation worker or a separate publication worker for the correction.
- Marking the PR ready before the reviewer assesses the correction.
- Opening a replacement PR or branch for the fix.
