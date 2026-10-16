# Take one issue through delivery

Coordinate implementation, independent review, and submission for one selected issue. One implementation worker carries implementation, draft publication, corrections, and ready submission through their task references. A separate fresh context reviews. The coordinator dispatches, reads the returned evidence, and settles decisions. It does not do subject-repository work. A delegated coordinator stops after ready submission and hands the remaining agreed endpoint to the parent. Each operation remains usable without this coordinator.

Read this reference and [Handoffs](../shared/coordination.md#handoffs) before the first dispatch. Open the other shared references when their conditions apply, as [Working context and tool output](../shared/context.md) states: [Authorization](../shared/authorization.md) when the endpoint or a limit is in question; [Evidence](../shared/evidence.md) when you read a worker's report; [Review](../shared/review.md) before you select or dispatch a reviewer; [GitHub writes](../shared/github-writes.md) before you change a GitHub record yourself, which this coordinator rarely does. Reading all of them first delays the first dispatch and changes no decision.

## Establish the task and endpoint

Read the selected issue, repository instructions, existing work, and user decisions. Identify the repository, the issue, and the **endpoint**: where this invocation stops.

Use the endpoint agreed in the conversation. If none was given, state the default: through PR review follow-up, without merge. A narrower request takes precedence. A request through merge authorizes that step, subject to the merge rules in [merge-pr](merge-pr.md). When the request says the run is unattended, apply [Decide in an unattended flow](../shared/decisions.md#decide-in-an-unattended-flow): take a supported recommendation and record it, park the issue when no answer is supported, and do not call an interactive question tool. A merge endpoint does not run unattended.

Confirm the paths of the linked task references before dispatch. Do not read a worker's procedure: the handoff names it, and the worker reads it. A handoff names the task reference and supplies the facts, decisions, and authorization that the worker cannot read itself, as [Handoffs](../shared/coordination.md#handoffs) lists. It does not restate the procedure.

## Resume from evidence

Read existing [Task notes](../shared/task-notes.md), then inspect existing branches, worktrees, PRs, review records, and check results for the issue. If the issue was parked by an unattended delivery and no question remains open, restore its label under [Parked deliveries](../shared/triage-labels.md#parked-deliveries) before the next dispatch. Reuse completed work when it still applies to the current revision. Do not create another branch or PR because this invocation is new. Keep evidence of implementation, tests, independent review, publication, and merge distinct.

If the issue is stale or contradicts current code, use [reconsider-issue](reconsider-issue.md). If its scope is unclear, use [define-issue](define-issue.md). Settle material decisions in the parent with [interview-issue](interview-issue.md). A clear issue needs none of these.

Changes to the selected issue can stay within the agreed flow. Creating a new child or choosing a replacement task is a scope decision for the user. This skill does not select work from a backlog or decompose issues.

## Implement and publish draft progress

Before substantial dependent implementation, apply [Prepare required review](../shared/review.md#prepare-required-review) for this delivery endpoint. Dispatch [implement-issue](implement-issue.md) when implementation remains. Give it the contents in [Handoffs](../shared/coordination.md#handoffs), including the source revision, the confirmed scope and decisions, existing work, the established review path or explicit exception, and the flow authorization and its limits. Authorize the same worker to continue into [submit-pr](submit-pr.md) for draft publication in the same session, and state that it must not mark the PR ready or request review. Request its actual results and evidence limits.

Apply [Draft PRs and readiness](../shared/pr-lifecycle.md) during implementation. The worker publishes its first significant committed checkpoint as a draft, then resumes implementation on the same branch. When the implementation is complete and its required checks pass, the worker publishes the final commits to the same draft before it returns. The worker returns the PR URL, published head, check results, and remaining work. Reuse an existing draft on resumption. A draft checkpoint does not trigger the ready-submission handoff or complete the endpoint.

If the worker returns a checkpoint without publishing it, resume that worker with publication authorization instead of starting another worker.

## Review the draft changes

Before marking the PR ready, dispatch [review-changes](review-changes.md) in a fresh context for the exact base and published head when required by the review plan. Carry any [user-approved exception](../shared/review.md#user-approved-exceptions) into that plan and subsequent handoffs. Give the reviewer the issue and necessary facts, not the author's conversation or desired conclusion. Apply [Review](../shared/review.md) to model evidence and unmet review requirements. Do not skip the review silently.

Read the worker's report and the reviewer's report. Do not read the diff to review it yourself. Inspect the subject repository only to settle a fact that the next dispatch depends on, such as a disputed finding.

If dispatching the reviewer fails because of a capacity limit, that is a dispatch problem, not a review choice. Finish your handoff with the commits, checks, and recorded implementation model, and let the parent dispatch the reviewer under [Coordination](../shared/coordination.md#handoffs).

Resume the implementation worker with the text of each actionable finding. It corrects them on the same branch, runs the affected checks, commits, and publishes the commits to the same draft under [submit-pr](submit-pr.md). Settle the reviewer's notes yourself as routine choices under [Decisions](../shared/decisions.md): accept or decline each in the correction handoff, with the reason. Return to the parent interview only a disputed finding that current evidence cannot settle, a scope change, or a choice about intended behavior; do not ask the user about style, naming, wording, or documentation conventions. After corrections, resume the reviewer for the changed code and the unresolved findings. Do not repeat completed checks without a new reason. If the same blocker persists without progress, report it instead of cycling.

When resuming with an existing PR, use current independent review evidence if it satisfies the review plan. Do not repeat completed review just to replay the sequence. Report any unmet review requirement and resolve it explicitly.

## Park an issue in an unattended flow

When [Decisions](../shared/decisions.md#decide-in-an-unattended-flow) parks the task, or a blocker persists without progress in an unattended run, leave the issue in a state the user can pick up from GitHub. Write the question or blocker, its evidence, and the recommended answer, or for a time park the remaining steps, to a file, and run `python3 "$GHFLOW_CLI" park ISSUE_URL --pr PR_URL --kind question|blocker|time --text FILE`. It does steps 1 and 2 below in one command for committed work that is already published, with a read-back of each write:

1. Have the implementation worker publish the committed work to the draft PR, if any is committed, and record the open question or blocker, its evidence, and the recommended answer when one exists, in the PR description under "Parked" and in the task notes.
2. Post the same question or blocker as a comment on the issue, and replace `triage:ready` with `triage:needs-input`, following [Triage labels](../shared/triage-labels.md#parked-deliveries), so that the user's needs-input view shows it.
3. Leave the PR a draft and the board In progress. Preserve the worktree and branch.
4. Return the issue as parked, with the question, the PR URL, and the head, to the queue coordinator or the user. Do not mark the PR ready, request review, or select the next issue yourself.

[sweep-needs-input](sweep-needs-input.md) resolves the question with the user later, and the delivery resumes from the PR under [Resume from evidence](#resume-from-evidence). A park for the time budget records the remaining steps instead of a question, and a later request resumes it directly.

## Submit and hand off

When review is complete and actionable findings are resolved, resume the implementation worker to mark the same PR ready under [submit-pr](submit-pr.md). Pass the review outcome, the reviewed head, and authorization. The worker publishes any remaining reviewed commits, then runs `pr ready` with the final description, the reviewed head, and the board target; that command's read-backs of the description, the ready state and head, the board, and the current-head checks and reviews are its ready submission evidence. If publication was explicitly deferred, submit the reviewed work within that limit instead.

If you are a delegated coordinator, return the submission result and remaining endpoint to the parent under [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership). Include the exact source revisions and existing checks and reviews, with original request times, deadlines, and identifiers. Stop at this handoff instead of dispatching or waiting for a nested [address-pr-review](address-pr-review.md) worker. If resuming an existing PR, hand off its current evidence by the same route. For a direct session, continue as the conversation owner under the shared rule.

## Continue to the endpoint in the parent

Apply [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership) to the ready submission report. If that report shows every hosted check passed for the current head, no requested or pending review, and no unresolved findings, it is the final follow-up evidence. Report the result from that read-back and stop. Do not read the worker's notes, the PR, or the diff to confirm it, and do not edit the worker's notes to record the endpoint; the endpoint belongs in your report.

Otherwise, the parent directly dispatches [address-pr-review](address-pr-review.md) and receives its final report. Preserve that task's one-cycle review limit and CI repair. A review requested after corrections can still be pending when it ends. Report a missing or timed-out review separately from passed CI and completed repairs.

For a review endpoint, use the final report of current-head CI, review coverage, resolved findings, and outstanding work. Apply [Evidence](../shared/evidence.md#reports) to distinguish a final result from an incomplete handoff. Do not merge.

For an authorized merge endpoint, the parent dispatches [merge-pr](merge-pr.md) after follow-up, without asking for the same permission again. Authorization for the full flow does not waive its checks.

Report the issue and PR URLs, the current or merged commit, test and review evidence, and remaining limits, including required post-merge checks not yet done. Take these from the responsible worker's read-back, not from your own subject-repository reads.

Stop at the endpoint or at a concrete blocker. Preserve the worktree and enough information to resume. Do not deploy, remove branches, or select the next issue unless the request includes it.
