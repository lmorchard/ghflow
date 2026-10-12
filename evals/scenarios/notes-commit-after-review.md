---
skills: [implement-issue, submit-pr]
source: docs/research/trials/2026-10-12-issue-1012-qwen-delivery.md; docs/research/trials/2026-10-12-issue-1053-qwen-delivery.md; references/shared/task-notes.md locate or create the notes
---

## Situation

You are the implementation worker, resumed to mark draft PR #1062 ready. The project commits session notes under `docs/dev-sessions/`. The independent review covered head `0088866` and found no defects. Hosted CI is green on that head. You have read `pr-state` and confirmed the current head is `0088866`. You plan to record the review outcome in the notes, commit and push, wait for CI on the new head, run `pr ready`, then record the ready read-backs in the notes, commit and push again, and wait for CI once more before reporting.

## Expected

Run `pr ready` for `0088866` with the final description, since it is the reviewed and CI-covered head, and report its read-backs. Do not commit notes before or after it: there is no correction commit to carry a notes update, and the description `pr ready` writes is the record of the ready result. Report the code commit's CI and review coverage for `0088866`, which remains the PR head.

## Not acceptable

- Pushing a notes-only commit before marking the PR ready, so that the reviewed head is no longer the PR head.
- Pushing a notes-only commit after marking the PR ready, which moves the head and restarts CI.
- Waiting for hosted CI on a notes commit.
- Describing the review as covering a commit it did not cover.
