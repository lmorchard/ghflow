---
skills: [implement-issue, express-issue]
source: Les decision on 2026-10-10; references/shared/task-notes.md
---

## Situation

The selected repository instructions store session notes under .work-notes/ instead of docs/dev-sessions/. A delivery handoff identifies .work-notes/2026-10-10-0930-issue-947/notes.md in the active worktree. The main checkout has a newer notes directory for an unrelated issue. The task is moving to another worker with access to the active worktree.

## Expected

Respect the project override and reuse the notes file for the selected task inside its active worktree. Read it before resuming and carry its absolute path and relevant facts to the next worker. Do not select unrelated work by directory recency or create a default directory merely because the worker changed.

## Not acceptable

- Creating docs/dev-sessions/ despite the project override.
- Writing the task notes into the main checkout instead of the active worktree.
- Using the newest unrelated session as the current task.
- Returning a handoff that omits the notes path.
