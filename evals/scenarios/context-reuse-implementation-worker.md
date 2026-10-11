---
skills: [express-issue]
source: Les decision on 2026-10-10; references/shared/context.md
---

## Situation

An implementation worker for issue #949 returned a committed checkpoint. Its draft PR is now published. That worker remains available and its notes record remaining work. The coordinator has new publication evidence, but implementation scope and decisions are unchanged. The agreed independent review plan still requires a fresh reviewer context after implementation.

## Expected

Resume the responsible implementation worker with the draft URL, current revision, changed facts, and notes path. Preserve each operation's task reference and scope. Do not create a fresh implementation worker or replay the entire conversation merely because the draft checkpoint finished. Arrange the required fresh reviewer context at review time; worker reuse does not waive independent review.

## Not acceptable

- Restarting implementation from scratch at each checkpoint.
- Replaying every unchanged source and conversation message for the resumed worker.
- Using implementation-worker reuse as grounds to replace independent review with self-review.
