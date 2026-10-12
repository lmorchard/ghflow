---
skills: [express-issue]
source: docs/research/trials/2026-10-12-issue-1054-qwen-delivery.md; references/shared/coordination.md handoffs
---

## Situation

You coordinate delivery of issue #1054 and are composing the implementation handoff. `facts --issue` reported that `.ghflow/project.md` is present with 38 lines, written last week, and no stale sources. You read it: it gives the worktree setup commands, the format, check, and test gates, the generated websocket message docs and their source manifest, the session notes convention, the commands never to run, and the commit subject style. You are about to copy those into the handoff as a fifteen-line "Project conventions" block, as the previous coordinator did.

## Expected

Point the worker to the project facts file and to `facts --issue` for live state instead of copying the conventions. Keep in the handoff only the facts that differ for this task: the confirmed decision, the base, the branch and worktree names, the review plan, the authorization and its limits, and the return list.

## Not acceptable

- Copying the setup, gates, generated files, or conventions from the facts file into the handoff.
- Omitting the pointer to the facts file.
- Reading the project instructions in full to extract conventions the facts file already holds.
- Dropping task-specific facts because the file exists.
