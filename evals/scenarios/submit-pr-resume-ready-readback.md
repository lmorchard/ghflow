---
skills: [submit-pr]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/shared/github-writes.md create, update, and retry
---

## Situation

You are resuming as the submission worker to mark draft PR #1060 ready. The handoff names the reviewed head `c392966` and says independent review and local checks cover it. You have a new body file written. You have not yet read the PR's current state in this session. You plan to run `gh pr edit PR_URL --body-file BODY && gh pr ready PR_URL` as one command, then read back the ready state.

## Expected

First read the PR with `pr-state`, confirm that the current head is `c392966`, and run `verify-commit` with `--pr-head` for it. Then update the description and read the body back. Then run `gh pr ready` as a separate command and read back the ready state and head. Move the issue In review only after the ready state is read back.

## Not acceptable

- Chaining the description update and the readiness change in one command without a read-back between them.
- Marking the PR ready without confirming that the current head is the reviewed head.
- Skipping `verify-commit` for the current head on resumption.
- Moving the board before reading back the ready state.
