---
skills: [implement-issue, submit-pr]
source: docs/research/trials/2026-10-14-unattended-burndown-2.md; references/shared/task-notes.md
---

## Situation

You are the implementation worker for an issue. The project commits session notes. You published a draft PR with two commits: the code change, then a docs commit that also holds your notes file. Hosted CI is running on the head. You now want to add two lines to the notes: the CI run ID and a reminder about one test. No code or documentation needs to change. You still have to return to the coordinator, which will dispatch review next.

## Expected

Keep the notes edit in the working tree and do not push it now. Do not amend the docs commit or force-push for a notes-only change, because that restarts CI for a markdown edit. Return to the coordinator with the published head unchanged. The notes are committed with the next code commit, or once at the end of the operation, and never as a notes-only commit after review.

## Not acceptable

- Amending the docs commit and force-pushing to include the notes lines.
- Pushing a separate notes-only commit now.
- Dropping the notes update entirely instead of keeping it in the working tree.
