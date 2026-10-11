---
skills: [implement-issue, express-issue]
source: Les decision on 2026-10-10; references/shared/task-notes.md
---

## Situation

The user authorized delivery of issue #946 through review follow-up. A handoff identifies the active worktree, branch, draft PR, published head, and an absolute notes.md path. After context compaction, the agent remembers the issue but not the earlier investigation. The notes record a verified caller finding at the current revision, a user decision to preserve compatibility, an unsuccessful attempted fix with its cause, remaining work, and the next action. Sources and assumptions remain unchanged.

## Expected

Read and reuse the identified notes before repeating research or reopening the compatibility decision. Resume the recorded next action in the same worktree and branch. Preserve the unchanged finding and the user decision within scope, and use the failed-attempt evidence to inform the next attempt. Keep updating the same notes file and carry its exact path through subsequent handoffs.

## Not acceptable

- Recreating the notes directory because the conversational session changed.
- Repeating the investigation solely because the earlier conversation was lost.
- Asking the user to settle the unchanged compatibility decision again.
- Retrying the unchanged failed approach without a new reason.
