# Merge a pull request

Merge the requested PR after checking its current state, then confirm the merge, issue, and board results. Use the user's existing merge authorization without asking again.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Review](../shared/review.md) throughout. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Establish the current state

Read the project instructions, PR, linked issue, and any review handoff. Confirm the repository, base branch, current head, and merge authorization.

If the PR is already merged, skip to confirming the result. Report any missing historical evidence; it does not block an authorized board correction. If the PR is closed without a merge, report that and do not reopen it without authorization.

## Require green CI

Read hosted CI for the current head with `pr-state`, described in [CLI results](../cli.md#reading-pr-state). Merge only when CI is green.

If CI is pending, wait with a tool that lets you report progress. If CI fails, return the failure for repair, or continue through separately authorized follow-up with [address-pr-review](address-pr-review.md).

If the repository has no CI, report that the green-CI condition cannot be met. Do not waive it. Changing this policy is a user decision.

Green CI counts only when the head contains the current tip of the base branch: `base_behind_by` in `pr-state` must be 0. Each PR can pass alone and still fail after another PR merges. If the head is behind, update the branch with `ghflow exec -- gh api -X PUT repos/OWNER/NAME/pulls/NUMBER/update-branch -f expected_head_sha=HEAD`, wait for CI on the new head, and assess again. <!-- allow-bare-gh: the branch update needs the host login's token scope, so it is deliberate --> `gh pr update-branch` needs the `repo` token scope, which the agent identity does not have. If the update has conflicts, return the PR for repair. Do not merge a head that is behind its base, even with green CI.

A clean update from the base adds no change of its own, so it does not need another independent review. It does need green CI on the new head.

## Require review evidence or permission

Apply the review-source policy in [Review](../shared/review.md). Read the review body, inline discussions, and relevant top-level comments, including all result pages.

Merge only with one of these:

- **Affirmative review**, as defined in [Review](../shared/review.md), within existing merge authorization.
- **Explicit user permission to merge this PR**, such as "merge this PR when CI passes." Keep that permission unless the user changes it or later changes fall outside its scope.

Green CI and an absence of feedback are not enough. If neither condition holds, stop before merging and report what is missing. If Copilot's review is absent, timed out, or unavailable, report that and use the other review evidence. Do not invent an extra approval requirement because a model identity is unknown.

Do not dismiss unresolved defects or human objections because formal approval is optional. Return material disputes and missing decisions to the parent or user.

## Merge the checked commit

Confirm that the PR is open, not a draft, and mergeable. Use the project's merge method when it specifies one. Otherwise choose a permitted method and state it.

Immediately before merging, read the head, check state, and `base_behind_by` again. Merge with `ghflow pr merge PR --repo OWNER/NAME --method METHOD --expect-head SHA`, which repeats the state and head checks and reads the merged state back. If the head changed, repeat the assessment instead of merging unseen changes.

Follow repository rules and required merge queues. Do not use administrator bypass or weaken protection rules. If GitHub requires an approval that this workflow does not, report the repository restriction.

Do not enable automatic merge to get around a failed immediate merge. If a merge queue accepts the PR, report it as queued until GitHub confirms the merge.

## Confirm the result

Read back the PR state, merge commit, and merge time. Confirm the linked issue state.

Move the completed issue to Done, following [Board status](../shared/board-status.md). Apply this step when completing an earlier merge too. A board failure does not make the merge fail. Do not merge again to repair metadata.

Close only issues that this PR completes. Leave a broader parent and its board status unchanged unless its full scope is complete and the update is authorized. Do not add comments that repeat the merge record.

Return the PR URL, merge commit, CI evidence, the review or permission that supported the merge, and the confirmed issue and board states. Report required post-merge checks that remain incomplete. Do not claim a live application test that you did not perform.

Keep local worktrees and branches unless cleanup was requested or project rules require it. Merge authorization does not permit discarding unrelated files.

Before cleanup, fetch, and compare the local and remote branch tips with the merged PR head. Check the worktree for uncommitted and untracked files. If either tip has commits beyond the merged head, or the worktree has changes, report them and return the choice to the user. Otherwise remove the worktree without `--force`, then delete the local branch. After a squash or rebase merge, `git branch -d` refuses because the branch is not an ancestor of the base; when the tips equal the merged head, use `git branch -D`. Report each check and command.

Do not delete the remote branch yourself. The permission classifier can block `git push --delete` as destructive. Report whether the remote branch still exists. If it does, tell the user that the repository's "Automatically delete head branches" setting prevents this, and that `scripts/delete-merged-branches.sh OWNER/REPO` in this repository removes the branches of merged PRs.
