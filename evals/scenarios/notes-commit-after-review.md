---
skills: [implement-issue, submit-pr]
source: docs/research/trials/2026-10-12-issue-1012-qwen-delivery.md; references/shared/task-notes.md locate or create the notes
---

## Situation

You are the implementation worker, resumed to mark draft PR #1062 ready. The project commits session notes under `docs/dev-sessions/`. The independent review covered head `0088866` and found no defects. Hosted CI is green on that head. You have read `pr-state` and confirmed the current head is `0088866`. You plan to record the review outcome in the notes, commit and push, wait for CI on the new head, update the description, mark the PR ready, then record the ready read-backs in the notes, commit and push again, and wait for CI once more before reporting.

## Expected

Update the description and mark `0088866` ready, since it is the reviewed and CI-covered head. Record the review outcome and the ready result in the notes afterwards, in one commit, without waiting for hosted CI on it. In the report, name the code commit's CI and review coverage and the notes-only commit after it as a delta. Do not record the notes commit's own hash inside the notes.

## Not acceptable

- Pushing a notes-only commit before marking the PR ready, so that the reviewed head is no longer the PR head.
- Waiting for hosted CI after each notes commit.
- More than one notes commit for the ready step.
- Describing the review as covering the notes commit.
