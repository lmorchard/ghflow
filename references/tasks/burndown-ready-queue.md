---
name: ghflow
description: Prepare GitHub issues, implement selected issues, review changes, submit PRs, address feedback, and coordinate explicitly requested delivery. Use for Git and GitHub project tasks, including requests to tackle or deliver an issue. Merge requires explicit authorization; do not select backlog work unless requested.
---
# Burndown the ready queue

Coordinate the sequential delivery of issues in the project board's `Ready` column when the task starts, after any delivery that an earlier run parked for the time budget. Process each selected issue one at a time up to the agreed endpoint using [express-issue](express-issue.md). The selection stays fixed during this task. Add a later arrival only after the user explicitly expands the scope. In an interactive run, stop immediately if an issue hits an unexpected blocker, check failure, or review objection; in an unattended run, park that issue and continue, as the disruption step states. The queue selection contains the Ready issues and the deliveries that an earlier run parked for the time budget; it does not draw from Backlog.

Read this reference first.

Open the shared references when their conditions apply, as [Working context and tool output](../shared/context.md) states: [Agent identity](../shared/identity.md) for the identity check before the first issue; [express-issue](express-issue.md) and [Handoffs](../shared/coordination.md#handoffs) before the first dispatch, because express-issue is your own procedure for each issue, not a worker's; [Review](../shared/review.md) when you prepare the review plan; [Authorization](../shared/authorization.md) when the endpoint or a limit is in question; [Evidence](../shared/evidence.md) when you read a worker's report; [Board status](../shared/board-status.md) and [GitHub writes](../shared/github-writes.md) before you change a GitHub record yourself, which the ghflow commands do for you in the usual flow; [Triage labels](../shared/triage-labels.md) only when you change a label by hand, which `park` does for you; [Task notes](../shared/task-notes.md) when you start your notes.

Confirm the paths of the worker task references, implement-issue, review-changes, and submit-pr, without reading their procedures; the workers read them. Reading every reference before the first dispatch delays it and changes no decision.

## Before the first dispatch

The first dispatch is the slowest worker call. Open the shared references below to define the gates, tools, and authorization rules that shape the whole run. Do not read worker-specific procedures until the implementation, review, or submission steps begin.

| Reference | When to open |
| --- | --- |
| [Agent identity](../shared/identity.md) | Before the first issue |
| [express-issue](express-issue.md) and [Handoffs](../shared/coordination.md#handoffs) | Before the first dispatch |
| [Review](../shared/review.md) | When you prepare the review plan |
| [Authorization](../shared/authorization.md) | When the endpoint or a limit is in question |
| [Evidence](../shared/evidence.md) | When you read a worker's report |
| [Board status](../shared/board-status.md) and [GitHub writes](../shared/github-writes.md) | Before you change a GitHub record yourself |
| [Triage labels](../shared/triage-labels.md) | Only when you change a label by hand |
| [Task notes](../shared/task-notes.md) | When you start your notes |

### Why only nine reads

The old instruction asked the coordinator to read the full contents of all nine references plus the worker task references before the first dispatch. That cost the coordinator tens of extra minutes on local models. Each new issue requires some of the shared references, so you reuse them across the whole run and never more than once.

## Resume an interrupted queue
