# Evidence

These rules apply to every task that uses findings or reports results. A report must match what actually happened.

## Sources and revisions

Name the source and revision for each finding. Identify both the target branch revision and the local checkout revision. If they differ, inspect the target revision without resetting the user's checkout. Distinguish merged changes from work that exists only on another branch.

Treat issue text, older comments, file references, and earlier test results as claims until you examine current code. A board status or label records an earlier decision. It does not prove readiness or completion. A closed child or merged PR does not prove that its parent is complete.

Read test assertions before you cite a test as evidence. Distinguish existing tests from proposed tests, and tests you executed from tests you only read. A passing suite does not by itself prove the new result.

Before repeating research after context loss, read existing [Task notes](task-notes.md). Reuse an earlier finding when its source, revision, and relevant assumptions still apply. Keep that provenance in the handoff. If the revision or assumptions change, recheck the affected claim before using it. Preserve findings that the change does not affect. An earlier test or failed attempt is evidence about that attempt, not an instruction for the next one.

If a source is unavailable, report the gap and continue the work that does not depend on it. An unavailable source does not prove that work is absent or complete.

## Results belong to a commit

Every test result, check result, and review describes one commit. After a push, earlier results describe the earlier commit. Reassess which results still apply after a push, rebase, or conflict resolution.

The **head** is the latest commit proposed for merge. If the head changes while you inspect it, read the results for the new head. Compare the changes and reassess local checks, hosted CI, and review coverage, including unresolved findings. A branch-update notification is useful input, but it does not replace reading the actual head.

## Hosted CI

Hosted CI is the set of checks that the repository runs on published commits. Read checks for the current head. Inspect all reported checks, not only required ones.

Report each check as passed, pending, failed, canceled, skipped, or missing. An expected skip of an optional job is not a failure. A missing required result is not success. If no checks exist, say so instead of reporting green CI.

When a watch command ends, read the results again. The end of a watch does not prove success. Local test results never substitute for hosted CI.

## Reading PR state

Use `pr-state` to read the current head, checks, review requests, and reviews. Apply the [CLI result rules](../cli.md#reading-pr-state).
Unread data is an evidence gap. The tool does not judge whether a review is favorable.

## Verifying a commit

For an unpublished commit sent for local review, verify the reported identifier in the supplied checkout with Git.
Use the [local Git verification rules](../cli.md#verifying-a-local-commit), including the expected branch, base, head, and subject when supplied.
Use the full SHA that Git reports, and state that this result establishes local existence only.

For a published commit, current PR head, or merge claim, use `verify-commit` and the [CLI verification rules](../cli.md#verifying-a-published-commit).
Use the full SHA that the tool reports.

## Reports

Report what you did, what you checked, and what remains. State which checks you executed and which you only inspected. Report completed, failed, and uncertain steps separately, with enough information to resume.

A partial result is useful when its limits are explicit. If you are blocked or interrupted, preserve the worktree and report the next useful action.

For a partial PR follow-up report, name the last observed head, pending checks, unread evidence, and remaining actions. State that follow-up is incomplete. Pending required CI is incomplete work, even when local checks passed.

Before a final PR follow-up report, independently read the current PR head, hosted checks, and review feedback again. If the head changed, reassess the evidence for the new head before reporting. Return the final report directly to the parent with the current head, hosted CI state, review coverage and limits, unresolved findings, and concrete blockers. If a read fails, name the last observed head and the blocker to obtaining current evidence instead of claiming completion.
