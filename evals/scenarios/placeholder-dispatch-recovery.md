---
skills: [express-issue]
source: docs/research/trials/2026-10-12-issue-1054-qwen-delivery.md; docs/research/trials/2026-10-12-issue-1012-qwen-delivery.md; references/shared/coordination.md handoffs
---

## Situation

You coordinate delivery of issue #1054 through PR review follow-up, without merge. The reviewer returned with no actionable findings for head `42e9a74`. You dispatched a new worker for the ready submission, but the dispatch went out with the prompt `x` instead of the handoff. The new worker replied, after sixteen minutes, that it could not tell what to do and asked what you meant. Its session is still available.

## Expected

Resume that same new session with the full ready-submission handoff, or a one-line prompt that names the handoff file: the PR, the reviewed head, the review outcome text, the board target, and the authorization limits. Do not start yet another session for the ready submission. Name the extra call in your report.

## Not acceptable

- Dispatching a third session for the ready submission instead of resuming the one that received the placeholder.
- Treating the worker's reply as a blocker or as a request for a user decision.
- Repeating the review or re-reading the diff before resuming.
- Omitting the extra call from the report.
