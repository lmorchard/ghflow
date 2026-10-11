# Take one issue through delivery

Coordinate implementation, independent review, and submission for one selected issue. A delegated coordinator stops after ready submission and hands the remaining agreed endpoint to the parent. Dispatch tasks rather than repeating their procedures here. Each operation remains usable without this coordinator.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Review](../shared/review.md) throughout. Apply [Coordination](../shared/coordination.md) to dispatch and handoffs. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

Apply [Working context and tool output](../shared/context.md) to selective source reads and complete evidence with concise output.

## Establish the task and endpoint

Read the selected issue, repository instructions, existing work, and user decisions. Identify the repository, the issue, and the **endpoint**: where this invocation stops.

Use the endpoint agreed in the conversation. If none was given, state the default: through PR review follow-up, without merge. A narrower request takes precedence. A request through merge authorizes that step, subject to the merge rules in [merge-pr](merge-pr.md).

Locate the linked task references before dispatch, and read each one when its task becomes relevant.

## Resume from evidence

Read existing [Task notes](../shared/task-notes.md), then inspect existing branches, worktrees, PRs, review records, and check results for the issue. Reuse completed work when it still applies to the current revision. Do not create another branch or PR because this invocation is new. Keep evidence of implementation, tests, independent review, publication, and merge distinct.

If the issue is stale or contradicts current code, use [reconsider-issue](reconsider-issue.md). If its scope is unclear, use [define-issue](define-issue.md). Settle material decisions in the parent with [interview-issue](interview-issue.md). A clear issue needs none of these.

Changes to the selected issue can stay within the agreed flow. Creating a new child or choosing a replacement task is a scope decision for the user. This skill does not select work from a backlog or decompose issues.

## Implement and publish draft progress

Before substantial dependent implementation, apply [Prepare required review](../shared/review.md#prepare-required-review) for this delivery endpoint. Dispatch [implement-issue](implement-issue.md) when implementation remains. Give it the contents in [Handoffs](../shared/coordination.md#handoffs), including the source revision, the confirmed scope and decisions, existing work, the established review path or explicit exception, the flow authorization and its limits, and the local-only limit for this operation.

Apply [Draft PRs and readiness](../shared/pr-lifecycle.md) during implementation. Tell the implementation agent to return the first significant committed checkpoint without waiting for the full task. Dispatch [submit-pr](submit-pr.md) with draft status, current check evidence, remaining work, and publication authorization. Then resume [implement-issue](implement-issue.md) in the same worktree and branch, carrying the PR URL. Use later useful checkpoints to update the same draft.

If the implementation returns complete before a checkpoint, publish it as a draft before independent review. Reuse an existing draft on resumption. A draft checkpoint does not trigger the ready-submission handoff or complete the endpoint.

## Review the draft changes

Before marking the PR ready, dispatch [review-changes](review-changes.md) in a fresh context for the exact base and head when required by the review plan. Carry any [user-approved exception](../shared/review.md#user-approved-exceptions) into that plan and subsequent handoffs. Give the reviewer the issue and necessary facts, not the author's conversation or desired conclusion. Apply [Review](../shared/review.md) to model evidence and unmet review requirements. Do not skip the review silently.

If dispatching the reviewer fails because of a capacity limit, that is a dispatch problem, not a review choice. Finish your handoff with the commits, checks, and recorded implementation model, and let the parent dispatch the reviewer under [Coordination](../shared/coordination.md#handoffs). Do not review the changes yourself.

Return actionable local findings to the implementation agent, on the same task branch, with affected checks run again. Return disputed findings and scope changes to the parent interview. After corrections, have the reviewer assess the changed code and the unresolved findings. Do not repeat completed checks without a new reason. If the same blocker persists without progress, report it instead of cycling.

When resuming with an existing PR, use current independent review evidence if it satisfies the review plan. Do not repeat completed review just to replay the sequence. Report any unmet review requirement and resolve it explicitly.

## Submit and hand off

Dispatch [submit-pr](submit-pr.md) to publish any remaining reviewed commits, update the draft description, and mark the same PR ready. Pass the PR URL, verified worktree, branch, base, head, checks, review outcome, and authorization. If publication was explicitly deferred, submit the reviewed work within that limit instead.

If you are a delegated coordinator, return the submission result and remaining endpoint to the parent under [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership). Include the exact source revisions and existing checks and reviews, with original request times, deadlines, and identifiers. Stop at this handoff instead of dispatching or waiting for a nested [address-pr-review](address-pr-review.md) worker. If resuming an existing PR, hand off its current evidence by the same route. For a direct session, continue as the conversation owner under the shared rule.

## Continue to the endpoint in the parent

The parent directly dispatches [address-pr-review](address-pr-review.md) and receives its final report. Preserve that task's one-cycle review limit and CI repair. A review requested after corrections can still be pending when it ends. Report a missing or timed-out review separately from passed CI and completed repairs.

For a review endpoint, use the responsible worker's final report of current-head CI, review coverage, resolved findings, and outstanding work. Apply [Evidence](../shared/evidence.md#reports) to distinguish a final result from an incomplete handoff. Do not merge.

For an authorized merge endpoint, the parent dispatches [merge-pr](merge-pr.md) after follow-up, without asking for the same permission again. Authorization for the full flow does not waive its checks.

Read back the final state through the responsible subagent. Report the issue and PR URLs, the current or merged commit, test and review evidence, and remaining limits, including required post-merge checks not yet done.

Stop at the endpoint or at a concrete blocker. Preserve the worktree and enough information to resume. Do not deploy, remove branches, or select the next issue unless the request includes it.
