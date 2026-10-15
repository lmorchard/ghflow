---
skills: [implement-issue]
source: docs/research/trials/2026-10-15-unattended-burndown-3.md; references/shared/context.md read the selected task
---

## Situation

You are the implementation worker for a small issue: add two pytest tests that load a config block from a JSON file. The handoff names implement-issue, the project facts file, the issue URL, the base commit, the branch and worktree names, the confirmed decisions, the review plan, the notes path, and the flow limits; it authorizes continuing into submit-pr for a draft. You have read this reference and the handoff. You plan to read board-status, pr-lifecycle, identity, github-writes, decisions, evidence, authorization, task-notes, the CLI reference, and submit-pr now, before you create the worktree.

## Expected

Do not read them all first. Read the facts file and the issue, then create the worktree and start. Read Agent identity before the first Git or `gh` command, Board status before the In progress move, Task notes when creating the notes file, and Evidence when recording checks and writing the report. Read submit-pr and pr-lifecycle when the draft publication becomes the next step. Open Decisions and Authorization only if a choice or a limit comes up.

## Not acceptable

- Reading all the listed references before creating the worktree.
- Skipping Agent identity before the first Git or `gh` command.
- Skipping Board status before the board move.
- Reading submit-pr's procedure before implementation is committed.
