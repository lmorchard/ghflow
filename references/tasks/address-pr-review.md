# Address pull request review

Take an existing PR through one review cycle and CI repair, and return the final report directly to the parent. This skill can follow [submit-pr](submit-pr.md) or start from a PR created elsewhere. It acts on review findings; it does not provide independent review. It stops before merge.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Review](../shared/review.md) throughout. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

Apply [Working context and tool output](../shared/context.md) to selective source reads and complete evidence with concise output.

## Establish the task

Apply any [user-approved exception](../shared/review.md#user-approved-exceptions) before arranging review or a fallback below. Preserve the agreed review plan while still reading feedback and checking CI.

Read the issue, PR, project instructions, current branch, and any supplied review report. Apply [Task notes](../shared/task-notes.md) to preserve findings, repair attempts, and the next action across interruptions. Confirm the current head.

If the parent reports an external branch update, read the actual PR head and compare the changes before continuing. Reassess checks, review coverage, and unresolved findings under [Evidence](../shared/evidence.md#results-belong-to-a-commit). Preserve the original review deadline and one-cycle limit.

For a local review report, identify the commit it reviewed and its evidence limits. Do not wait for Copilot when local findings are the input. If the report covers an earlier commit, compare it with the current code before you make corrections.

If no review exists or was requested, report that and do not wait. The parent can request Copilot or run [review-changes](review-changes.md). If Copilot is unavailable, report the reason. A different-model local review of the current head is the review evidence. If none covers the current head, hand off a review of the uncovered changes with [review-changes](review-changes.md) to the parent. Do not return the choice of fallback to the parent or user.

## Watch and repair CI

Watch CI while you wait for review and after each push. Use the installed watch command when available:

```sh
gh pr checks PR_URL --watch --interval 30 --fail-fast
```

Run it in a way that returns control, so you can handle review feedback and user input. Report when a check finishes, a review arrives, or a decision is needed. Do not send updates that only repeat an unchanged pending state.

If a check fails, read its job log before you change anything. Distinguish a code defect from setup problems, permissions, service outages, and cancellation. Fix failures within the issue and its required build setup, without weakening checks. Run the affected local checks, commit, push to the same PR, and watch the new head.

Continue until CI passes or a concrete blocker prevents useful work. Do not retry an unchanged failure without new evidence or a specific reason that a retry can help. Rerunning a failed job for such a reason is part of CI repair. Report missing credentials, persistent service failures, and decisions that need the user. Keep completed fixes.

## Wait for the review

Inspect existing feedback first, using `pr-state` from [CLI results](../cli.md#reading-pr-state) for review requests, reviews, and checks on the current head. If the requested review is already complete, go straight to its findings.

Otherwise, use the request time, requested head, and prior review identifiers from the handoff or GitHub. Set the deadline 20 minutes after the request. If the request time is unknown, record that and wait once, for 20 minutes from now. On resumption, keep the recorded deadline. A push does not reset it.

A completed review from the requested reviewer for the requested commit ends the wait. If the head changes during the wait, identify which commit each review covers; the deadline does not restart.

Poll GitHub about once a minute, or use a supported watch mechanism. Keep each wait short enough to accept user input. Do not send another review request on each poll. Handle temporary read errors within the deadline, and report persistent access failures rather than treating missing data as an empty review.

Stop waiting at the deadline or when the user interrupts. At a timeout, report the last observed state and address the available findings. A timeout is an incomplete review. It is not approval and does not show that Copilot is unavailable. After a timeout, use a different-model local review of the current head as the review evidence, as when Copilot is unavailable. If none covers the current head, hand off a review of the uncovered changes with [review-changes](review-changes.md) to the parent, without asking the user. If a Copilot review arrives later, read it before merge. The deadline applies only to the review; CI repair continues after it.

## Address the findings

Read the review body, inline discussions, and relevant top-level comments, including all result pages. Assess each finding against the issue and current code before you change anything.

Address human findings while a Copilot request is still pending. They do not complete the Copilot wait. Before you report completion, read human feedback again and address new requests within scope.

Respond to each finding in one of these ways:

- Fix a demonstrated problem within the agreed scope.
- Explain a disputed suggestion with evidence.
- Identify an unrelated problem for separate work. Propose a follow-up issue, but file it only if filing is authorized.

A request to address review covers corrections and factual replies within the agreed scope. Return a new product decision or broader scope to the parent or user. Do not weaken a success condition to satisfy a suggestion.

Make all accepted corrections, run the checks, and push them together. Each push restarts CI and can trigger another automatic review.

Before you edit, confirm that the worktree and branch match the PR head. Work in that worktree or a new isolated one, and preserve unrelated work. Add or update useful tests, and run the affected checks plus the required project checks. Commit and push to the same PR branch. Inspect unexpected remote changes before you push, and do not force-push over another contributor's work.

Reply with the correction and its commit, or explain why you made no change. Resolve a discussion only when its concern is fixed and the project permits it. Leave disputed and undecided discussions open.

After a push, read CI and review state for the new head. Update the PR description if the changes make its claims wrong.

## Request another review if needed

If the corrections need another Copilot review, follow the request rules in [Review](../shared/review.md). Reuse an automatic request instead of duplicating it.

This skill waits for one review cycle. Do not start another 20-minute wait without a further request. Continue CI repair for the latest head.

## Report the result

Before reporting, read the current head, checks, and feedback again under [Evidence](../shared/evidence.md#reports). Return directly to the parent:

- The PR URL, current head, corrections, and test results.
- Each finding as fixed, disputed, deferred, or unanswered, including unresolved human requests even when CI is green.
- CI state, naming the commit whose hosted checks passed or the concrete blocker.
- Review state, covered commits, coverage limits, and whether the wait completed or timed out.
- Original and new review request times, requested commits, deadlines, and review identifiers needed for resumption.
- Remaining actions and concrete blockers, including any failed read of the current head or its evidence.

An earlier clean review does not cover later changes.

If required checks remain pending or current evidence is unread, identify the report as partial and follow-up as incomplete. Continue useful authorized work unless a concrete blocker or interruption prevents it.

Do not merge or enable automatic merge. Do not create a replacement PR because review handling failed.
