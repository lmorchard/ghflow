# Burndown the ready queue

Coordinate the sequential delivery of issues in the project board's `Ready` column when the task starts. Process each selected issue one at a time up to the agreed endpoint using [express-issue](express-issue.md). The selection stays fixed during this task. Add a later arrival only after the user explicitly expands the scope. Stop immediately if an issue hits an unexpected blocker, check failure, or review objection. The queue selection contains Ready issues only; it does not draw from Backlog.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), [Review](../shared/review.md), [Board status](../shared/board-status.md), and [Agent identity](../shared/identity.md) throughout. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Resume an interrupted queue

When interrupted or handing off, carry the selected issue IDs, endpoint, and authorization limits in the conversation. On resumption, use that selection and read the current state of the selected issues and board before acting. Check whether every selected issue has reached the agreed endpoint. Continue work on any selected issue that has not reached it, even if no issues are currently in `Ready`. Report completion only when every selected issue has reached the endpoint. Do not treat the current Ready queue as a new selection or add later arrivals unless the user explicitly expands the scope.

## Audit the Ready queue

Resolve the selected project to its node ID:

```bash
gh project view NUMBER --owner OWNER --format json
```

Read the returned `id`. Read the `Status` and `Priority` item values by name in the query below.

Use `gh api graphql --paginate --slurp` to read every project item:

```bash
gh api graphql --paginate --slurp \
  -F project_id=PROJECT_NODE_ID \
  -f query='query($project_id: ID!, $endCursor: String) {
    node(id: $project_id) {
      ... on ProjectV2 {
        id
        items(first: 100, after: $endCursor) {
          nodes {
            id
            content {
              __typename
              ... on Issue { url repository { nameWithOwner } }
              ... on PullRequest { url repository { nameWithOwner } }
            }
            status: fieldValueByName(name: "Status") {
              ... on ProjectV2ItemFieldSingleSelectValue { name }
            }
            priority: fieldValueByName(name: "Priority") {
              ... on ProjectV2ItemFieldSingleSelectValue { name }
            }
          }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
  }'
```

`--paginate` follows `endCursor` until `hasNextPage` is false. `--slurp` returns each page in one JSON array.
Check every page before you use any item. Require valid JSON, no GraphQL `errors`, the selected project ID, an item array, and valid `pageInfo` on every page.
Require each item to have an ID and `status` and `priority` keys. A `null` value means that field is unset.
Treat a missing key or unexpected value shape as incomplete discovery.
Require a non-empty `endCursor` when `hasNextPage` is true. Require the final returned page to set `hasNextPage` to false.
Require every earlier returned page to set `hasNextPage` to true.
Treat a command failure, missing project, malformed page, or failed validation as incomplete discovery.
Discard all output after a command failure, because earlier pages can still appear in that output.
Do not use partial output to report a clear queue or dispatch work.

For a new task, after the full traversal succeeds, identify every item whose named `Status` value is `Ready`. Record the issue IDs in that initial Ready queue as this task's selection. A later board read can refresh issue state, but it does not replace the selection. Add a later arrival only after the user explicitly expands the scope. On resumption, use the recorded selection and the procedure in [Resume an interrupted queue](#resume-an-interrupted-queue); do not create a new selection.
If a Ready item has no actionable issue URL and repository identity, report it as unresolved and do not report the queue as empty.
Sort actionable Ready issues by priority (`P0` before `P1`).
For a new task only, if the complete inventory contains no Ready items, report that the initial selection is empty and the selected delivery is complete.
This traversal is not an atomic snapshot. Report that limit if the board could change during retrieval.

Use the delivery endpoint the user already selected. If none is set, confirm it with the user:

- **Through review follow-up (default)**: Implements, verifies with independent review, submits PR, and addresses feedback, leaving the PR open for user review.
- **Through merge**: Merges the PR upon green CI and affirmative review, following the merge policy in [merge-pr](merge-pr.md).

## Deliver issues sequentially

Process one issue at a time:

1. Select the top unblocked issue from the recorded selection that has not reached the agreed endpoint. Use the current issue state to decide whether it remains actionable. When delivering to a review follow-up endpoint (without merge), ensure the selected task is independent of other in-flight PRs so it can branch cleanly from `origin/main`. If a task depends on code in an unmerged PR, either authorize merging the prerequisite PR first or defer the dependent task.
2. Before substantial dependent implementation, apply [Prepare required review](../shared/review.md#prepare-required-review). Dispatch a subagent to execute [express-issue](express-issue.md) on that issue, passing the confirmed repository, issue number, authorization, endpoint, and established review path, model evidence, or explicit exception.
3. On its ready-for-review submission handoff, apply [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership). The conversation parent directly dispatches follow-up and receives the final report. If you are a delegated queue coordinator, relay the handoff, remaining selected issue IDs, endpoint, and authorization limits to that parent, then stop. Resume from the parent's endpoint result before selecting another issue. After the chosen endpoint finishes, verify the result:
   - Did the task reach the expected endpoint?
   - Is the project board status updated to `In review` or `Done`?
4. **Hard stop on disruption**:
   - If the task encounters a persistent test failure, review defect that cannot be resolved within the cycle, or an unexpected merge conflict:
     - **Halt the burndown immediately.**
     - Do not advance to the next issue in the queue.
     - Preserve the worktree and branch.
     - Return the blocker, error logs, and proposed remediation to the user.
5. For a merge endpoint, obtain CI on the base branch's merge commit through the responsible worker before you start the next issue. If it fails, treat it as a disruption and halt.
6. If the issue successfully completes to the authorized endpoint, proceed to the next selected issue that has not reached that endpoint.

## Conclude and hand off

When all selected issues have reached the agreed endpoint:

1. Present a delivery summary table:
   - Issue number and title.
   - Pull request URL and head commit SHA.
   - Review evidence (local reviewer model or Copilot).
   - Final status on the project board (`In review` or `Done`).
2. If current authorization includes curation, continue under [curate-ready-queue](curate-ready-queue.md) within those limits without asking for the same authorization again. Otherwise, suggest curation as a possible next task and stop. Do not select or move backlog issues, or dispatch curation, without authorization.
