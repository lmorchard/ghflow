# Repair a pull request conflict

Resolve a PR that conflicts with its base, push the resolved head, and hand it back for review. This task changes code; it does not review or merge.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), [GitHub writes](../shared/github-writes.md), [Workspace isolation](../shared/workspace.md), and [Agent identity](../shared/identity.md#running-commands-under-the-identity) throughout.

## Establish the conflict

Read the issue, PR, base branch, current head, and mergeability. Confirm that the PR is open and that the head is the one the caller named. Work in the PR's worktree, not the primary checkout. Preserve unrelated work.

## Merge the base

Fetch the base branch and merge it into the PR branch in the worktree. Keep the conflict markers for the next step. Record the conflicting paths.

## Resolve

Read both sides and the merge base before you edit. Preserve both intents; do not drop either side to make the merge quiet. Keep the issue scope: repair the conflict, do not add unrelated changes. If both intents cannot hold, return the product decision to the caller.

## Verify and publish

Run the focused tests for the conflicting paths and the project gates. Commit the merge resolution and push to the same PR branch. Do not force-push over another contributor's work.

## Hand off

Return the PR URL, the new head, the conflicting paths, the resolution decision, the test results, and the evidence limits. The head changed, so the previous clean verdict does not cover it. The caller requests a review of the new head before merge.
