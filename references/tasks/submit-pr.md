# Submit a pull request

Publish committed progress as a draft PR, or submit completed work as ready for review. For a ready PR, move the issue to In review and arrange the selected review. Return a handoff without waiting for findings. Do not change code to address findings, merge, or enable automatic merge.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Review](../shared/review.md) throughout. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md). Apply [Agent identity](../shared/identity.md#running-commands-under-the-identity) to every Git and `gh` command.

Apply [Draft PRs and readiness](../shared/pr-lifecycle.md) to choose draft publication or readiness. A draft checkpoint returns to implementation or local review; it does not start PR follow-up.

Apply [Working context and tool output](../shared/context.md) to selective source reads and complete evidence with concise output.

## Prepare the branch and description

Read the issue, project instructions, and implementation report. Confirm the repository, worktree, branch, intended base, and authorization to publish.

Inspect the working tree and task commits, and preserve unrelated or uncommitted work. Do not publish an incomplete change as ready for review.

For an unpublished implementation handoff, verify the supplied base and head in its supplied checkout with local Git, following [Evidence](../shared/evidence.md#verifying-a-commit). Confirm the reported branch points at the expected head.

On resumption to update or mark ready an existing PR, read its state with `pr-state`, confirm that the current head is the head that the handoff names, and run `verify-commit` with `--pr-head PR_URL` for that head, following [CLI verification](../cli.md#verifying-a-published-commit). Inspect the diff at that head before you rewrite the description; an earlier read does not describe later commits.

Refresh remote references and inspect changes on the base. Do not rebase merely to get a cleaner history. If integration is necessary, follow the project rules and repeat the affected checks after resolving conflicts.

Review the task diff from the merge base of the base and task branches. Inspect the full list of changed files, including generated output and lockfiles, and explain unexpected changes before you publish. Make sure that the published commits contain the reported changes. For ready submission, confirm that they contain the tested changes. For a draft checkpoint, distinguish tested changes from unfinished or unverified work. Report missing or stale test evidence instead of copying an earlier success claim.

Write a title and body that explain the problem, the resulting behavior, the test evidence, and material limits. Name who ran each check: tests you executed, tests that the implementation report states, and hosted CI. State only facts that you read or ran. If the handoff names a finding or observation without its text, read its source or report the gap; do not describe content you have not read. For a draft checkpoint, include remaining work and the next useful action. Use the repository template when one exists. Keep detail proportional to the change, and distinguish local tests from hosted CI.

Use a closing reference such as `Closes #N` only when the PR completes that issue. A child PR does not close its broader parent.

Write the body to a UTF-8 file outside the task diff, such as the task notes directory or a temporary directory, and pass it with `--body-file`. Report the file path. For a preparation-only request, the prepared body is the result. Do not push or create a PR without publication authorization.

## Publish and confirm

Confirm that `identity` reports the configured login as ready. Before the first GitHub write, confirm that `gh api user` under that identity returns the same login, as [Agent identity](../shared/identity.md#running-commands-under-the-identity) requires. The active account in `gh auth status` does not establish the write identity. Check the installed help for the commands you need.

Search for an existing PR for the same repository, head branch, and base. Use `--json` so that no match is an explicit empty list rather than missing output. On resumption, inspect the known PR URL first.

Push the branch explicitly. Then run `verify-commit HEAD_SHA --repo OWNER/NAME --on BRANCH`, following [CLI verification](../cli.md#verifying-a-published-commit), to make sure that the remote commit is the intended local commit. If the remote has unexpected work, resolve the difference before publishing. Do not force-push over it.

Reuse a matching existing PR and preserve intervening edits to its description. Otherwise create the PR with an explicit repository, head, base, title, and body file. Use `--draft` for early progress or when requested. Do not add labels, assignees, or comments that nobody requested. Do not use `gh pr create --dry-run` to avoid writes: it can push changes.

Record the returned URL immediately. Read back the body, branch, base, head commit, and draft state. Run `verify-commit HEAD_SHA --repo OWNER/NAME --pr-head PR_URL` for the published head. For a draft checkpoint, skip the readiness, board transition, and review request below, and return to the coordinator with remaining work.

When the work meets the shared readiness conditions, update the description and read the body back. Then mark the existing draft ready with `gh pr ready PR_URL` as a separate command, and read back the ready state and head. Do not chain the description update and the readiness change in one command; each write needs its own read-back under [GitHub writes](../shared/github-writes.md). Leave an explicit draft-only request in draft status.

## Mark the issue in review

When the PR is ready for review, move the issue it implements to In review, following [Board status](../shared/board-status.md). The transition command reports the earlier status; do not query the board separately first. A draft PR for unfinished work does not qualify. If the board update fails, report it and continue with the review request.

## Request a review

Apply any [user-approved exception](../shared/review.md#user-approved-exceptions) before arranging review or a fallback below. Report a waived requirement and its approved scope instead of requesting a substitute that the user made optional.

For an agent pull request, the primary review source is a different-model local review, as [Review](../shared/review.md) states. A completed independent local review of the published head lets the PR proceed. A review that covers an earlier commit does not qualify. Do not request Copilot by default.

Request Copilot review only when the user asked for it. Read the current requests and reviews with `pr-state`, described in [CLI results](../cli.md#reading-pr-state). Follow the request rules in [Review](../shared/review.md): check for an existing request first, including an automatic one.

Record the request time, the requested head, and existing review identifiers. Read back the request or the resulting review.

If the user requested Copilot and it is unavailable, use a completed different-model local review that covers the head as the review source. Only when no such review covers the head, return the reason and a handoff for local review with [review-changes](review-changes.md), supplying the issue, repository, base and head commits, and the implementation model if known. Do not recreate the PR because a review request failed.

## Report and hand off

Read the CI and review state for the published head with `pr-state`. Return:

- The issue and PR URLs, base and published head commits, worktree, branch, body file path, and confirmed draft or ready state.
- The `verify-commit` results for the published head.
- Exact source revisions used for instructions and tools, and authorization limits for the remaining endpoint.
- The review source used, the approved waiver and its scope, or review not yet performed for a draft checkpoint. For a local review, include its head, findings, and recorded model identities, with any approved same-model exception. For a Copilot request, include its time, requested reviewer, and existing review identifiers.
- The observed CI and review state, with checks and reviews tied to their commits. Preserve original review request times, deadlines, and identifiers on resumption.
- The board transition result, or why it was skipped or failed.
- Any other incomplete operations and any fact you could not read.

For a draft checkpoint, return completed work, remaining work, and the next action to the coordinator. Do not dispatch review follow-up or claim the delivery endpoint is complete.

For a ready submission whose authorized endpoint includes follow-up, return the handoff under [PR follow-up ownership](../shared/coordination.md#pr-follow-up-ownership). Mark follow-up incomplete when a check is pending or failed, a review is requested or pending, or a finding is unresolved. In that case the parent directly dispatches [address-pr-review](address-pr-review.md) within the existing authorization. For a submission-only request, stop here. Each follow-up task can also start from an existing PR without this handoff.
