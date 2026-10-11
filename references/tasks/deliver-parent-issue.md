# Deliver a parent issue

Work through the children needed to satisfy one selected parent issue, reusing the existing skills and carrying decisions between them. Continue from child to child without the user restarting the flow. Stop at the parent's boundary.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Review](../shared/review.md) throughout. Apply [Coordination](../shared/coordination.md) to dispatch and handoffs. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Establish the boundary

Read the parent, project instructions, confirmed decisions, existing children, and related PRs. Identify the intended result, exclusions, priority policy, and the endpoint for each child.

State the authorized scope at the start without requesting it again: which of definition, filing, implementation, publication, and merge the flow includes. If the child endpoint is unspecified, use the [express-issue](express-issue.md) default of review follow-up without merge. At an explicit limit, such as a subset or a budget, stop with a truthful handoff.

A request to complete the parent includes maintaining its progress and closing it when its full success conditions are met. A request to process selected children does not authorize closing a broader parent. Distinguish the two before claiming completion.

## Reconcile the remaining work

Compare the parent goal with current target-branch code, related changes, tests, and child results. Use [reconsider-issue](reconsider-issue.md) when evidence challenges the parent's content or status. Use [decompose-parent-issue](decompose-parent-issue.md) when task boundaries or coverage are missing.

Reuse an existing decomposition while it still fits, but a previously proposed list is not a current inventory. Maintain a compact map from each parent requirement to completed work, an existing child, remaining work, or an explicit exclusion.

Record progress and decisions in the parent issue and native child relationships, through a subagent, preserving intervening edits. Small corrections to completed work or the next task do not need a full reconsideration cycle.

## Choose and prepare the next child

Choose from the agreed parent scope using real dependencies, current priority, useful results, and review size, and explain the choice briefly. Inspect current code and actual consumers before accepting an old candidate's technical claims.

Follow project rules for entering active work. Do not raise a priority to make an issue eligible. Use priorities already approved for the work, or return a material priority decision to the user.

Process one child at a time by default. Base each implementation on the target branch after its prerequisites merge, not on an unmerged branch. Parallel work needs independent scope and enough review capacity.

If a child lacks an implementable definition, use [define-issue](define-issue.md), with material decisions settled in the parent through [interview-issue](interview-issue.md). If a candidate holds independently useful changes too large to review together, split it, keep parent coverage intact, and explain the split. Routine boundary refinement within agreed scope needs no new authorization. A change to intended behavior, exclusions, or material cost goes back to the user.

When the draft is ready and the flow includes publication, use [file-issue](file-issue.md). Reuse matching existing work instead of filing duplicates.

## Deliver each child

Before substantial dependent implementation of a child, apply [Prepare required review](../shared/review.md#prepare-required-review). Carry the established review path, model evidence, or explicit exception into the child handoff.

Run [express-issue](express-issue.md) for the selected child with its endpoint, scope, decisions, and authorization. Its delegated coordinator owns implementation, early draft publication, independent review, and ready submission under [Draft PRs and readiness](../shared/pr-lifecycle.md). The conversation parent owns direct follow-up dispatch under [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership).

If running as a delegated coordinator, relay the ready-submission handoff and remaining child and parent scope to the conversation parent, then stop. Resume from the parent's endpoint result. A submission handoff does not complete a child whose endpoint includes follow-up or merge.

In this flow, a child merges only with both affirmative independent review of its final changes and green hosted CI for its final head, unless a [user-approved exception](../shared/review.md#user-approved-exceptions) explicitly changes this flow's review condition. Merge permission alone does not substitute for the favorable review here, and a pending or timed-out review is not favorable. Keep the exact-head checks and other rules in [merge-pr](merge-pr.md).

A subject agent can define, file, and implement in one dispatch; a nested agent per phase is not required. Apply the agreed review plan under [Review](../shared/review.md#user-approved-exceptions). A capacity limit alone does not permit replacing independent review with self-review.

After the parent receives the responsible worker's final result for the chosen child endpoint, verify that result through the responsible subagent and credit only delivered behavior. Update the parent issue's progress and the coverage map, then continue to the next eligible child without another prompt.

If a child is blocked, record its state and dependency, and continue an independent child when useful and authorized. Do not hide the blocker or skip work the parent needs. When no useful authorized progress remains, stop and return a focused question.

Treat new user feedback, smoke-test results, and regressions as active evidence. Fix defects that this effort caused before dependent tasks. Report unrelated pre-existing defects without adding them to the parent's scope.

## Verify the parent result

After the planned children finish, reassess the parent's success conditions against current code and consumers. Refresh the coverage map and inspect integration across the children. A set of closed issues does not prove the parent complete.

Run the project checks and focused integration checks needed for the remaining evidence gaps. Reuse valid results that cover the current revision and behavior, rather than repeating full suites to produce another report.

Keep automated tests, hosted CI, deployment, and user-reported smoke checks distinct. Name required live checks that were not performed. Do not claim parent completion while a required success condition is unresolved.

If the authorized endpoint and all completion conditions are met, have a subagent close the parent and apply its board transition, then read back the result. Otherwise leave it open and report exactly what remains.

Return the child and PR links, parent state, current coverage, decisions made, blockers, and verification limits. Do not move on to unrelated backlog work.
