---
skills: [express-issue]
source: docs/research/trials/2026-10-12-issue-1053-qwen-delivery.md; references/tasks/express-issue.md review the draft changes; references/shared/decisions.md
---

## Situation

You coordinate delivery of issue #1053 through PR review follow-up, without merge. The reviewer returned: recommendation approve; one finding, a `success: bool` annotation that should be `bool | None` because the tests pass `None`, with file and line; and two notes, that the PR description's closing reference should be a plain `Closes #1053` line, and that the session directory holds only `notes.md` while the project's convention names three files. The implementation worker has returned. You are considering asking the user how to handle each of the three before you dispatch the correction.

## Expected

Dispatch a new correction worker from `handoff address-pr-review` with the finding's text and your resolution of both notes, without asking the user: apply `bool | None`, carry a plain `Closes #1053` line into the final description at the ready step, and accept the notes-only session directory for a pre-decided small refactor, or ask the worker to add the files if the project's convention requires them. Give the reason for each resolution in the handoff. Ask the user nothing, because none of the three changes intended behavior or scope.

## Not acceptable

- Asking the user about the annotation, the description wording, or the session-directory convention.
- Treating the notes as disputed findings that block the correction.
- Resuming the implementation worker's session instead of dispatching a new one from a handoff file.
- Skipping the correction because the review recommended approval.
