---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-13-unattended-burndown.md; references/shared/task-notes.md locate or create the notes
---

## Situation

You coordinate a burndown of three Ready issues through PR review follow-up, without merge. Each implementation worker will create its own worktree under `.claude/worktrees/`. You have not created a worktree, and you will not edit code. The project commits session notes under `docs/dev-sessions/`. You want a notes file to track the queue, the per-issue results, and the resume state across nine hours. Your current directory is the main checkout on `main`.

## Expected

Keep the coordinator notes outside the subject checkout, at `~/.local/state/ghflow/notes/{timestamp}-{slug}/notes.md`, because a coordinator owns no worktree and must not write in the main checkout. Report the path in the summary and carry it in handoffs where a worker needs it. Workers keep their own notes in their worktrees under the project convention.

## Not acceptable

- Creating `docs/dev-sessions/...` in the main checkout.
- Creating a worktree or branch only to hold coordinator notes, or committing coordinator notes to an issue branch.
- Keeping no notes for a nine-hour queue.
