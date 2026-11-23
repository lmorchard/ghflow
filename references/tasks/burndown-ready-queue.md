# Burndown the ready queue

Coordinate the sequential delivery of issues in the project board's `Ready` column when the task starts, after any delivery that an earlier run parked for the time budget. Process each selected issue one at a time up to the agreed endpoint using [express-issue](express-issue.md). The selection stays fixed during this task. Add a later arrival only after the user explicitly expands the scope. In an interactive run, stop immediately if an issue hits an unexpected blocker, check failure, or review objection; for unattended delivery, use the deterministic runner with `scripts/run_queue.py`. The queue selection contains the Ready issues and the deliveries that an earlier run parked for the time budget; it does not draw from Backlog.

Read this reference first.
Open shared references when their conditions apply, as [Working context and tool output](../shared/context.md) states: [Agent identity](../shared/identity.md) for the identity check before the first issue; [express-issue](express-issue.md) and [Handoffs](../shared/coordination.md#handoffs) before the first dispatch; [Review](../shared/review.md) when you prepare the review plan; [Authorization](../shared/authorization.md) when the endpoint or a limit is in question; [Evidence](../shared/evidence.md) when you read a worker's report.
Open [Board status](../shared/board-status.md) and [GitHub writes](../shared/github-writes.md) before you change a GitHub record yourself; [Triage labels](../shared/triage-labels.md) only when you change a label by hand; [Task notes](../shared/task-notes.md) when you start your notes.
Confirm the paths of the worker task references, implement-issue, review-changes, and submit-pr, without reading their procedures; the workers read them. Reading every reference before the first dispatch delays it and changes no decision.

## Resume an interrupted queue

When interrupted or handing off, carry the selected issue IDs, endpoint, and authorization limits in the conversation. On resumption, use that selection and read the current state of the selected issues and board before acting. Check whether every selected issue has reached the agreed endpoint. Continue work on any selected issue that has not reached it, even if no issues are currently in `Ready`. Report completion only when every selected issue has reached the endpoint. Do not treat the current Ready queue as a new selection or add later arrivals unless the user explicitly expands the scope.

## Audit the Ready queue

Read the whole board with one command:

```bash
python3 "$GHFLOW_CLI" queue select --owner OWNER --project NUMBER
```

It reads every page, validates each one, and lists the `Ready` issues in burndown order under `selection`. A non-zero exit means incomplete discovery: it returns no selection, and any earlier output is void. Do not report a clear queue or dispatch work from a failed read, and do not rebuild the traversal by hand to get around the failure. Report the error and retry the command once; if it fails again, report discovery as incomplete.

For a new task, record the issue IDs in `parked` and then in `selection` as this task's selection, in that order. `parked` lists deliveries that an earlier unattended run parked for the time budget: issues In progress with an open PR that holds a "Parked (time budget)" section. Each holds published progress, so it goes first, and you resume it under [Resume from evidence](express-issue.md#resume-from-evidence) from its PR, worktree, and remaining steps.
The `selection` order is the delivery order: priority (`P0` before `P1`), then `Size` from smallest to largest (`XS`, `S`, `M`, `L`, `XL`, then unset), then ascending issue number.

Use the delivery endpoint the user already selected. If none is set, confirm it with the user:

- **Through review follow-up (default)**: Implements, verifies with independent review, submits PR, and addresses feedback, leaving the PR open for user review.
- **Through merge**: Merges the PR upon green CI and affirmative review, following the merge policy in [merge-pr](merge-pr.md).

## Check the project facts

After the traversal and before the first dispatch, run `git fetch origin` and then `python3 "$GHFLOW_CLI" facts` from the subject checkout. Workers branch from `origin`, so decide from `project_facts.origin`, which checks the facts file on the default branch against that branch's sources; the top-level `stale_sources` checks only your working copy, which can lag `origin`. If `project_facts.origin.present` is true and its `stale_sources` is empty, continue. If it is not empty, dispatch [prepare-project-facts](prepare-project-facts.md) to refresh the file before the first issue, with a handoff from `python3 "$GHFLOW_CLI" handoff prepare-project-facts --out FILE`, which takes no issue and states the ready PR without review.
Every worker in the queue reads the facts file, so a stale section can send each of them to the wrong gate or setup command.

The queue request authorizes the refresh and its PR. It is part of the delivery flow, not a change outside an issue under [Decisions](../shared/decisions.md#decide-in-an-unattended-flow). The refresh worker commits in its own worktree and publishes the file as a ready PR for the user's review; it does not merge. Workers branch from `origin/main`, where the refresh is not yet merged, so set the project facts path in every handoff to the refreshed file in the refresh worktree, as [Handoffs](../shared/coordination.md#handoffs) states. Record the refresh PR in the delivery summary.
The deterministic runner performs this dispatch before the first issue. It creates the refresh worktree and branch, runs `prepare-project-facts`, verifies that the committed branch changes only `.ghflow/project.md`, and points every later handoff at that copy. `--require-facts-refresh` stops the run before the first issue when the refresh fails; without it, the runner continues with the stale-source note.
If the refresh fails or returns no refreshed file, continue the queue: name the stale sources in each handoff, as [Handoffs](../shared/coordination.md#handoffs) states, and record the failure in the summary.

If `project_facts.present` is false, continue without a facts file and say so in the summary; writing the first facts file is a separate task the user requests.

The same output answers three other preparation questions without separate commands. `base_ci.summary` on the default branch head decides the red-base halt in the disruption step; if `base_ci.stale` is true, fetch and read `facts` again before you rely on it. `runtime.nested_dispatch` decides whether step 2 dispatches express-issue or coordinates each issue yourself. `skill_source` gives the revision for each handoff's source line; if `up_to_date` is false, report it in the summary and continue with the checked-out revision.

## Deliver issues sequentially

Process one issue at a time. For unattended delivery, do not run the coordinator procedure as an unattended model loop; run the deterministic runner with `python3 scripts/run_queue.py` from the target project checkout.

For an interactive delivery:

1. Select the top unblocked issue from the recorded selection that has not reached the agreed endpoint. Use current issue state to decide whether it remains actionable.
2. Before substantial dependent implementation, apply [Prepare required review](../shared/review.md#prepare-required-review). Dispatch a subagent to execute [express-issue](express-issue.md) on that issue, passing the confirmed repository, issue number, authorization, endpoint, and established review path.
3. On its ready-for-review submission handoff, apply [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership). Verify that `pr-state` reports `ci` as `green` on the current head, no requested or pending review, and the project board status updated to `In review` or `Done`.
4. **Disruption**: if an issue hits an unexpected blocker, persistent test failure, or review defect, **halt the burndown immediately.** Do not advance to the next issue. Preserve the worktree and branch. Return the blocker, error logs, and proposed remediation to the user.
5. If the issue successfully completes to the authorized endpoint, proceed to the next selected issue that has not reached that endpoint.

## Conclude and hand off

When all selected issues have reached the agreed endpoint:

1. Present a delivery summary table with `python3 "$GHFLOW_CLI" queue summary ISSUE_URL... --owner OWNER --project NUMBER`.
2. Report the result, sources, check evidence, and remaining decisions to the user.
3. Audit worker session logs for recurring operational toil with `python3 "$GHFLOW_CLI" audit toil`. Report any patterns that hit the Three Strikes threshold as candidates for deterministic automation.
4. File out-of-scope findings as follow-ups, following [Follow-ups](../shared/followups.md). Write them to `followups.md` in the run notes directory so the run summary includes them.
