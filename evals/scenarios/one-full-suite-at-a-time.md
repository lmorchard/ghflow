---
skills: [implement-issue]
source: docs/research/trials/2026-10-12-issue-1012-qwen-delivery.md; references/tasks/implement-issue.md prepare an isolated workspace
---

## Situation

You are the implementation worker in a worktree. The project's full suite runs with `-n auto`, which starts eighteen pytest workers on this machine, and takes several minutes. A baseline run of the full suite is in progress in the background. You have just finished editing the code and tests and want to see whether the full suite passes with your change. You consider starting a second full-suite run now, in the foreground, while the baseline continues.

## Expected

Do not start a second full suite while one is running. Run the targeted tests for the changed files now, and start the full suite on the edited tree after the baseline finishes. If a full suite dies while another is running, treat the death as a result of the overlap, not of the code, and rerun it alone.

## Not acceptable

- Running two full suites at the same time to save time.
- Attributing a death or failure during overlapping runs to the change.
- Skipping the baseline to free the machine.
