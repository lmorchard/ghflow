---
name: ghflow
description: Prepare GitHub issues, implement selected issues, review changes, submit PRs, address feedback, and coordinate explicitly requested delivery. Use for Git and GitHub project tasks, including requests to tackle or deliver an issue. Merge requires explicit authorization; do not select backlog work unless requested.
---
# Burndown the ready queue

Coordinate the sequential delivery of issues in the project board's `Ready` column when the task starts, after any delivery that an earlier run parked for the time budget. Process each selected issue one at a time up to the agreed endpoint using [express-issue](express-issue.md). The selection stays fixed during this task. Add a later arrival only after the user explicitly expands the scope. In an interactive run, stop immediately if an issue hits an unexpected blocker, check failure, or review objection; in an unattended run, park that issue and continue, as the disruption step states. The queue selection contains the Ready issues and the deliveries that an earlier run parked for the time budget; it does not draw from Backlog.

Read this reference first.

## The facts file is required

Before the first dispatch, the coordinator MUST read `.ghflow/project.md`. This file is the source of truth for gates, tests, and note locations. Workers need explicit facts about what tests to run, which branch to use, and where to write notes.

If `.ghflow/project.md` is absent from the default branch, the coordinator must park the delivery with a note that the facts file is missing. The facts file must be provided before the first issue is dispatched. A later delivery can request and include the facts file in its PR before resuming.

Open shared references when their conditions apply, as [Working context and tool output](../shared/context.md) states: [Agent identity](../shared/identity.md) for the identity check before the first issue; [express-issue](express-issue.md) and [Handoffs](../shared/coordination.md#handoffs) before the first dispatch, because express-issue is your own procedure for each issue, not a worker's; [Review](../shared/review.md) when you prepare the review plan; [Authorization](../shared/authorization.md) when the endpoint or a limit is in question; [Evidence](../shared/evidence.md) when you read a worker's report; [Board status](../shared/board-status.md) and [GitHub writes](../shared/github-writes.md) before you change a GitHub record yourself, which the ghflow commands do for you in the usual flow; [Triage labels](../shared/triage-labels.md) only when you change a label by hand, which `park` does for you; [Task notes](../shared/task-notes.md) when you start your notes.

Confirm the paths of the worker task references, implement-issue, review-changes, and submit-pr, without reading their procedures; the workers read them. Reading every reference before the first dispatch delays it and changes no decision.

## Before the first dispatch

The first dispatch is the slowest worker call. Before that dispatch, the coordinator must complete the following:

1. **Read the facts file**: `.ghflow/project.md` must exist and have no stale sources. Run `facts --issue` to verify. If stale, flag or skip.
2. **Open the nine shared references**: These nine references name the gates, tools, and authorization rules that shape the whole run.
3. **Dispatch the first issue**: Only after the two above is complete.

Do not read worker-specific procedures (`implement-issue`, `submit-pr`, `review-changes`) until their handoffs.

### The nine shared references

Open exactly these nine references before the first dispatch:

| Reference | Purpose |
| --- | --- |
| [Agent identity](../shared/identity.md) | Identity check pass/fail, write gate definition |
| [express-issue](express-issue.md) and [Handoffs](../shared/coordination.md#handoffs) | Callouts, `ghflow exec --`, and `handoff --` contracts |
| [Review](../shared/review.md) | Independent review selection, review limits, and resolution paths |
| [Authorization](../shared/authorization.md) | Merge and endorsement policies |
| [Evidence](../shared/evidence.md) | Final result vs incomplete handoff, what counts as closure |
| [Board status](../shared/board-status.md) and [GitHub writes](../shared/github-writes.md) | Status columns, automatic gain rules, tools the commands use |
| [Triage labels](../shared/triage-labels.md) | Time park, scope park, `triage:needs-input` meanings |
| [Task notes](../shared/task-notes.md) | Notes directory layout and handoff structure |

These nine define the gates, tools, and authorization rules that shape the whole run. Once the first dispatch is under way, read the worker-specific procedures for responsible gates and checks.

## Resume an interrupted queue
