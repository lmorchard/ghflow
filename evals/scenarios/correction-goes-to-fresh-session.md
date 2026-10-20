---
skills: [express-issue]
source: 2026-10-19 #994 resume, where resuming a 222,000-token implementation session overflowed the shared 262,144-token cache; decision to dispatch later steps fresh
---

## Situation

You coordinate the delivery of issue #994 in OpenCode on the local model. The implementation worker published draft PR #1085 at head `1a6b47b` and returned; its session is long. A fresh reviewer returned one actionable finding, F1, which you settled with the user and recorded in `decisions.md` in your notes directory. The worktree is `.claude/worktrees/issue-994-subagent-memory-cap`. You are about to dispatch the correction.

## Expected

Write the correction handoff with `ghflow handoff address-pr-review` for #994, passing F1 and the decision in the decisions or extra file, and dispatch it as a new session with the printed prompt. Do not resume the implementation worker's session. After the correction returns, dispatch a new reviewer from `handoff review-changes` with F1 and the reviewed head, and later the ready step from `handoff submit-pr`, each in a new session.

## Not acceptable

- Resuming the implementation worker's session for the correction or the ready step.
- Resuming the first reviewer's session for the re-review.
- Writing the correction yourself as the coordinator.
