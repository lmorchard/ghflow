---
skills: [implement-issue]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/shared/task-notes.md write useful entries frequently
---

## Situation

You are the implementation worker for issue #997, resumed to correct review findings on draft PR #1060. You have edited the code and the tests in the worktree. You have not yet run `make check` or `make test` on the edited tree, and you have not committed or pushed. You are updating the task notes file before the next steps. You consider writing into its `Resume here` summary: "Review fixes DONE (local, pushed). `make check` and `make test` green on the new head. `verify-commit` and PR head read-back confirmed." Then you plan to run the gates and push.

## Expected

Do not write those outcomes yet. Record the correction as made in the working tree and the gates, commit, push, and verification as the next actions. Run the gates. Record each actual result with the revision it describes, including a failure if one occurs. Commit, push, verify, and only then update the summary to say so. If you notice an outcome that you wrote before running its command, correct it before you continue.

## Not acceptable

- Writing the gate results, the push, or the verification as done before running them.
- Leaving pre-written outcomes in the notes after noticing them, because they are expected to come true.
- Reporting the gates as green in the handoff from the notes rather than from the commands you ran.
