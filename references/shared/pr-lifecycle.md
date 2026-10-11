# Draft PRs and readiness

Apply these rules when implementation and publication belong to the authorized flow. [Authorization](authorization.md) preserves local-only and preparation-only limits.

## Publish useful progress

Prefer opening a draft PR as soon as significant committed work exists, before independent review. Significant work is a coherent change that shows progress on the issue, even when implementation or verification remains incomplete. Do not wait for all implementation or review to finish merely to create the PR.

Use [submit-pr](../tasks/submit-pr.md) for publication. Keep the issue In progress while the PR is a draft, and defer review requests and review follow-up. In an ongoing delivery flow, an early draft is a progress checkpoint. It does not complete a ready-submission or review-follow-up endpoint. An explicit draft-only submission can stop with the requested draft.

Keep the same PR and branch as work continues. Publish further logical commits at useful checkpoints. Update the description with completed work, remaining work, actual check results, and the next useful action. Preserve the PR URL, worktree, branch, base, and published head in handoffs so another session can resume. Carry any [Task notes](task-notes.md) path in the handoff alongside this evidence. Uncommitted changes still need a separate report.

## Mark the PR ready

When implementation, required checks, and the selected pre-submission review are complete, use [submit-pr](../tasks/submit-pr.md) to mark the existing draft ready for review. An explicit draft-only limit keeps it a draft. Resolve actionable findings and report any remaining evidence limits before claiming readiness.

Refresh the description to explain the final change and its current evidence. Read back the ready state and current head before moving the issue to In review or requesting review. Readiness does not establish affirmative review, passed hosted CI, or merge permission.
