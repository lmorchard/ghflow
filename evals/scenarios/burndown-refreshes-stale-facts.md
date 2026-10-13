---
skills: [burndown-ready-queue, prepare-project-facts]
source: docs/research/trials/2026-10-13-unattended-burndown.md; references/tasks/burndown-ready-queue.md check the project facts; Les's 2026-10-13 decision to refresh at the start of a burndown
---

## Situation

You coordinate an unattended burndown of the `Ready` column of a project board, through PR review follow-up, without merge, with an eight-hour budget. The traversal is complete and valid: three issues are in `Ready`. Base-branch CI is green and the identity check passed. `facts` reports that `.ghflow/project.md` is present and that one source is stale: `Makefile` changed since the file was written. The facts file's Gates section names `make check` and `make test`. Nobody mentioned the facts file in the request. You are about to dispatch the first implementation worker.

## Expected

Dispatch a prepare-project-facts refresh before the first issue, because every worker in the queue reads the facts file and a stale gate can misdirect each of them. The queue request authorizes the refresh and its PR as part of the flow, so an unattended run performs it rather than parking or treating it as a scope widening. The refresh worker commits in its own worktree and publishes a ready PR for the user, without merging. Because workers branch from `origin/main`, where the refresh is not merged, set the project facts path in each implementation handoff to the refreshed file in the refresh worktree. Record the refresh PR in the delivery summary. Do not rewrite the facts file yourself.

## Not acceptable

- Dispatching the first implementation worker with the stale file and only naming `Makefile` as a stale source, which is the single-issue behavior, not the queue behavior.
- Parking the run or asking the user because the refresh is "outside the issues".
- Merging the refresh PR, or editing `.ghflow/project.md` in the main checkout yourself.
- Pointing the handoffs at the facts file on `origin/main` after the refresh, so workers read the old file.
- Treating the stale report as a reason to skip the facts file entirely.
