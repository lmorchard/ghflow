# Burndown the ready queue

Coordinate the sequential delivery of issues in the project board's `Ready` column when the task starts. Process each selected issue one at a time up to the agreed endpoint using [express-issue](express-issue.md). The selection stays fixed during this task. Add a later arrival only after the user explicitly expands the scope. In an interactive run, stop immediately if an issue hits an unexpected blocker, check failure, or review objection; in an unattended run, park that issue and continue, as the disruption step states. The queue selection contains Ready issues only; it does not draw from Backlog.

Read this reference first. Open the shared references when their conditions apply, as [Working context and tool output](../shared/context.md) states: [Agent identity](../shared/identity.md) for the identity check before the first issue; [express-issue](express-issue.md) and [Handoffs](../shared/coordination.md#handoffs) before the first dispatch, because express-issue is your own procedure for each issue, not a worker's; [Review](../shared/review.md) when you prepare the review plan; [Authorization](../shared/authorization.md) when the endpoint or a limit is in question; [Evidence](../shared/evidence.md) when you read a worker's report; [Board status](../shared/board-status.md) and [GitHub writes](../shared/github-writes.md) before you change a GitHub record yourself, which the ghflow commands do for you in the usual flow; [Triage labels](../shared/triage-labels.md) only when you change a label by hand, which `park` does for you; [Task notes](../shared/task-notes.md) when you start your notes. Confirm the paths of the worker task references, implement-issue, review-changes, and submit-pr, without reading their procedures; the workers read them. Reading every reference before the first dispatch delays it and changes no decision.

## Resume an interrupted queue

When interrupted or handing off, carry the selected issue IDs, endpoint, and authorization limits in the conversation. On resumption, use that selection and read the current state of the selected issues and board before acting. Check whether every selected issue has reached the agreed endpoint. Continue work on any selected issue that has not reached it, even if no issues are currently in `Ready`. Report completion only when every selected issue has reached the endpoint. Do not treat the current Ready queue as a new selection or add later arrivals unless the user explicitly expands the scope.

## Audit the Ready queue

Read the whole board with one command:

```bash
python3 "$GHFLOW_CLI" queue select --owner OWNER --project NUMBER
```

It reads every page, validates each one, and lists the `Ready` issues in burndown order under `selection`. A non-zero exit means incomplete discovery: it returns no selection, and any earlier output is void. Do not report a clear queue or dispatch work from a failed read, and do not rebuild the traversal by hand to get around the failure. Report the error and retry the command once; if it fails again, report discovery as incomplete.

For a new task, record the issue IDs in `selection` as this task's selection, in that order. A later board read can refresh issue state, but it does not replace the selection. Add a later arrival only after the user explicitly expands the scope. On resumption, use the recorded selection and the procedure in [Resume an interrupted queue](#resume-an-interrupted-queue); do not create a new selection.
If `unresolved` lists a Ready item with no actionable issue URL and repository identity, report it as unresolved and do not report the queue as empty.
The `selection` order is the delivery order: priority (`P0` before `P1`), then `Size` from smallest to largest (`XS`, `S`, `M`, `L`, `XL`, then unset), then ascending issue number. Smaller issues run first, so the deadline is most likely to fall on the largest one. The board's card order is not read. An issue in `below_tier` is below `P1` and breaks [Priority tiers](../shared/board-status.md#priority-tiers): deliver it with the selection, and name it in the summary so the user can reprioritize it through sweep-prioritize or remove it.
For a new task only, if `selection` and `unresolved` are both empty, report that the initial selection is empty and the selected delivery is complete.
This traversal is not an atomic snapshot. Report that limit if the board could change during retrieval.

Use the delivery endpoint the user already selected. If none is set, confirm it with the user:

- **Through review follow-up (default)**: Implements, verifies with independent review, submits PR, and addresses feedback, leaving the PR open for user review.
- **Through merge**: Merges the PR upon green CI and affirmative review, following the merge policy in [merge-pr](merge-pr.md).

## Check the project facts

After the traversal and before the first dispatch, run `git fetch origin` and then `python3 "$GHFLOW_CLI" facts` from the subject checkout. Workers branch from `origin`, so decide from `project_facts.origin`, which checks the facts file on the default branch against that branch's sources; the top-level `stale_sources` checks only your working copy, which can lag `origin`. If `project_facts.origin.present` is true and its `stale_sources` is empty, continue. If it is not empty, dispatch [prepare-project-facts](prepare-project-facts.md) to refresh the file before the first issue, with a handoff from `python3 "$GHFLOW_CLI" handoff prepare-project-facts --out FILE`, which takes no issue and states the ready PR without review. Every worker in the queue reads the facts file, so a stale section can send each of them to the wrong gate or setup command.

The queue request authorizes the refresh and its PR. It is part of the delivery flow, not a change outside an issue under [Decisions](../shared/decisions.md#decide-in-an-unattended-flow), so an unattended run performs it. The refresh worker commits in its own worktree and publishes the file as a ready PR for the user's review; it does not merge. Workers branch from `origin/main`, where the refresh is not yet merged, so set the project facts path in every handoff to the refreshed file in the refresh worktree, as [Handoffs](../shared/coordination.md#handoffs) states. Record the refresh PR in the delivery summary. If the refresh fails or returns no refreshed file, continue the queue: name the stale sources in each handoff, as [Handoffs](../shared/coordination.md#handoffs) states, and record the failure in the summary.

If `project_facts.present` is false, continue without a facts file and say so in the summary; writing the first facts file is a separate task the user requests.

The same output answers three other preparation questions without separate commands. `base_ci.summary` on the default branch head decides the red-base halt in the disruption step; if `base_ci.stale` is true, fetch and read `facts` again before you rely on it. `runtime.nested_dispatch` decides whether step 2 dispatches express-issue or coordinates each issue yourself. `skill_source` gives the revision for each handoff's source line; if `up_to_date` is false, report it in the summary and continue with the checked-out revision.

## Deliver issues sequentially

Process one issue at a time:

1. Select the top unblocked issue from the recorded selection that has not reached the agreed endpoint. Use the current issue state to decide whether it remains actionable. When delivering to a review follow-up endpoint (without merge), ensure the selected task is independent of other in-flight PRs so it can branch cleanly from `origin/main`. If a task depends on code in an unmerged PR, either authorize merging the prerequisite PR first or defer the dependent task.
2. Before substantial dependent implementation, apply [Prepare required review](../shared/review.md#prepare-required-review). Dispatch a subagent to execute [express-issue](express-issue.md) on that issue, passing the confirmed repository, issue number, authorization, endpoint, and established review path, model evidence, or explicit exception. If a subagent in your runtime cannot dispatch subagents of its own, as `facts` reports with `runtime.nested_dispatch` false for OpenCode, coordinate the issue yourself under express-issue instead: dispatch its implementation, review, and ready workers directly, and keep express-issue's limits on the coordinator. In particular, do not read the subject code to scope a handoff. The handoff names the issue, the confirmed decisions and where they are recorded, and the project facts file, and the implementation worker does the research.
3. On its ready-for-review submission handoff, apply [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership). The conversation parent directly dispatches follow-up and receives the final report. If you are a delegated queue coordinator, relay the handoff, remaining selected issue IDs, endpoint, and authorization limits to that parent, then stop. Resume from the parent's endpoint result before selecting another issue. After the chosen endpoint finishes, verify the result:
   - Did the task reach the expected endpoint?
   - Is the project board status updated to `In review` or `Done`?
4. **Disruption**: a persistent test failure, a review defect that the correction cycle does not resolve, an unexpected merge conflict, or a decision that [Decisions](../shared/decisions.md#decide-in-an-unattended-flow) parks.
   - In an interactive run, **halt the burndown immediately.** Do not advance to the next issue. Preserve the worktree and branch. Return the blocker, error logs, and proposed remediation to the user.
   - In an unattended run, which the user's request states, park the issue under [Park an issue in an unattended flow](express-issue.md#park-an-issue-in-an-unattended-flow), record it for the summary, and continue with the next selected issue. Halt even when unattended if the failure would affect every later issue: the identity check or token fails, the base branch's CI is red, or the same environment failure parks two issues in a row. A merge endpoint never runs unattended.
   - When the request gives a time budget, do not start an issue after the budget's deadline. Park an issue that is in progress at the deadline with its state recorded. A ready submission or another write sequence that you dispatched before the deadline may finish after it, so that no PR is left half-written; do not dispatch new work after the deadline.
   - Under a time budget, keep measured durations with `budget` in your notes directory. Record the deadline once before the first dispatch with `python3 "$GHFLOW_CLI" budget --log NOTES_DIR/budget.jsonl --deadline "DEADLINE"`. Run it with `--start KIND:ISSUE` just before each dispatch and `--end KIND:ISSUE` when the worker returns. Use the kinds `refresh`, `implement`, `review`, `correction`, `ready`, and `park`. Before you dispatch work, run it with `--need` for the kinds that must still fit, such as `--need review,ready`, and add a few minutes for your own turns between dispatches. `remaining_minutes` and `need.fits` are the estimate. When `fits` is null because a kind is not measured yet, estimate from the closest measured kind and say so. Do not take durations from PR or issue timestamps such as `updatedAt`, which change on any edit. CI time alone is not an estimate. Dispatch a correction for an optional reviewer note only when the correction, its re-review, and the ready step fit before the deadline. Otherwise decline the note and record it in the PR description with the reason, so that an approved head reaches the endpoint.
5. For a merge endpoint, obtain CI on the base branch's merge commit through the responsible worker before you start the next issue. If it fails, treat it as a disruption and halt. After each merge, run `facts` again; if a source became stale, apply [Check the project facts](#check-the-project-facts) before the next issue.
6. If the issue successfully completes to the authorized endpoint, proceed to the next selected issue that has not reached that endpoint.

## Conclude and hand off

When all selected issues have reached the agreed endpoint:

1. Read the time with a clock command or `budget`, and state the actual end time and any step that finished after the deadline. Then present a delivery summary table. `python3 "$GHFLOW_CLI" queue summary ISSUE_URL... --owner OWNER --project NUMBER` reads the PR, head, draft state, board status, and parked label for each selected issue and prints them as a table; add the review evidence and decisions from the workers' reports. The table holds:
   - Issue number and title.
   - Pull request URL and head commit SHA.
   - Review evidence (local reviewer model or Copilot).
   - Final status on the project board (`In review` or `Done`), or `parked` with the question or blocker and the label applied.
   - For an unattended run, each decision taken under [Decisions](../shared/decisions.md#decide-in-an-unattended-flow), with the PR that records it.
   - The project facts refresh PR, when the queue dispatched one, or the stale sources it found when no facts file exists.
2. If current authorization includes curation, continue under [curate-ready-queue](curate-ready-queue.md) within those limits without asking for the same authorization again. Otherwise, suggest curation as a possible next task and stop. Do not select or move backlog issues, or dispatch curation, without authorization.
