# Implement an issue

Produce tested, committed changes for the requested issue, with enough evidence for another agent to prepare a PR. This skill ends with a local branch and a report. Do not push, open a PR, merge, or remove the worktree.

Apply [Authorization](../shared/authorization.md) and [Evidence](../shared/evidence.md) throughout. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

Apply [Working context and tool output](../shared/context.md) to selective source reads and complete evidence with concise output.

## Read the issue and current code

Read the project instructions, the issue body, and relevant comments. Identify the intended result, scope limits, success conditions, and confirmed decisions. Do not require labels or documents from another skill.

Inspect the relevant code and tests at the current revision, and determine whether the reported problem still exists. If part of the issue is already satisfied, record the evidence and implement only what remains. If nothing remains, report that. Do not create unrelated work to justify a commit.

When a fact or choice is missing, apply [Decisions](../shared/decisions.md). Settle routine implementation choices from current evidence. Return decisions about the intended result instead of redefining the issue.

## Prepare an isolated workspace

Inspect the current status, branches, and existing worktrees before you change anything. Preserve unrelated work.

Determine the base branch from the project or the request. Do not assume it is `main` or that the current checkout is the right base. Refresh its remote reference when access permits.

Create a worktree and task branch following project conventions. Do not reset or switch the shared checkout. Do not reuse another session's worktree because its name matches the issue.

If resuming, confirm the supplied worktree and branch before you edit, and read their existing changes. Continue that work instead of starting a competing implementation.

Prepare what the baseline checks need, such as generated code, frontend packages, and browser binaries. A Python test suite can need JavaScript tools too. Install declared dependencies as the project directs, before the baseline. Installs into the project or the user's home are part of the task. A system-level install, such as one that uses `sudo` or the operating system's package manager, needs explicit authorization: report the need and the command instead of running it. Do not run an installation at the same time as tests that use or copy those dependencies; some gate commands reinstall packages, so check before running gates in parallel. Use test configuration and isolated data where required. Do not copy credentials or connect to live services to make tests pass.

Run the relevant baseline before implementation. Record existing failures and environment limits separately from new failures. If a baseline problem prevents meaningful verification, investigate or report it. Independent implementation can continue, but incomplete verification is not success.

## Mark implementation in progress

When implementation starts, move the issue to In progress, following [Board status](../shared/board-status.md). On resumption, keep a later state such as In review or Done. If the update fails, report it and continue implementation.

## Plan the change and its evidence

Make a short plan against the current code. Connect each planned change to an issue requirement. Prefer small steps that show useful behavior across the relevant components.

When a planned change depends on library or runtime behavior that you have not observed in this task, such as escaping, newline handling, encoding, or ordering, confirm it with a short command in the project environment before you write code on it. Apply [Evidence](../shared/evidence.md#sources-and-revisions): your recollection is a claim. Record the command and its result in the notes. Do not describe behavior as verified unless a command showed it.

For each success condition, name a test, command, or human assessment, what it establishes, and its expected result. Mark which checks exist and which you must add. Keep tests of new behavior separate from tests that protect existing behavior. Missing tests or setup errors do not demonstrate the reported bug.

Apply [Task notes](../shared/task-notes.md) to preserve findings, decisions, and useful attempts throughout execution. Use the project's record format when one exists.

## Implement and test

Follow the project's test-first rules. For a bug fix, demonstrate the failure before changing the implementation when feasible. Make sure the failure comes from the reported behavior, not a broken setup.

Make the smallest change that satisfies the issue. Add tests for the intended behavior and relevant error cases. Leave unrelated cleanup out.

Make each new assertion specific to the behavior under test. Assert text or values that the pre-change output and neighboring code paths do not produce; a word that the old output already contains proves nothing. After the suite is green, confirm that each new test fails when the behavior it covers is disabled, not only when the whole change is absent. If the test still passes, it covers something else: fix the test, and check whether the behavior runs at all, before you commit.

Run targeted tests first during implementation iterations to maintain fast feedback. Run the broader test suite and project checks once the implementation is in place, before self-review and commit. Do not repeatedly run the entire test suite on intermediate edits when targeted tests are sufficient.

Change a test when the intended behavior requires it, and explain why. Do not remove useful assertions to make the suite pass. If an issue requirement itself is wrong, return that decision to the parent or user.

If a requirement needs human judgment, prepare the example or demonstration and state what the person must assess.

## Return useful progress for draft publication

When the enclosing flow authorizes publication, apply [Draft PRs and readiness](../shared/pr-lifecycle.md). At the first significant change, inspect the intended diff, run appropriate targeted checks, and commit a coherent checkpoint. Full implementation checks and final self-review still apply before the completed implementation handoff.

When the handoff authorizes you to continue into [submit-pr](submit-pr.md), commit the checkpoint and publish it as a draft through that reference in the same session, then resume implementation on the same branch. Before the completed implementation handoff, publish the final commits to the same draft under the same authorization. Otherwise, return the checkpoint to the coordinator for [submit-pr](submit-pr.md), with the worktree, branch, base, committed head, checks, remaining work, and next action, and do not push or open the PR yourself. State that implementation is incomplete when it is. For a standalone local-only request, continue locally without this publication handoff.

## Review and commit

Inspect the complete task diff from the merge base, including uncommitted and new files. Look for incomplete changes, missed callers, error cases, unrelated edits, and missing documentation. Check that changed tests still establish the intended behavior. Fix what you find within scope, and run the affected checks again.

If the base changes or conflicts need resolution, reassess which results still apply.

Stage only the intended files and inspect the staged diff. Commit logical changes following project conventions. If a commit hook changes tested files, run the affected checks again. Make sure the commits contain the changes your report describes.

This self-review is not independent review. Do not claim independent verification when none occurred.

## Return the result

Return:

- The issue URL, any existing draft PR URL, worktree path, branch, base revision, current commits, the revision you tested, and any remaining uncommitted changes.
- For an unpublished handoff, the supplied checkout path and publication state, plus the full local Git verification result for the reported head and base.
- The board transition result, or why it was skipped or failed.
- The implementation model from session metadata, or "unknown". The parent uses it to choose a different model for review.
- The changes, and the result for each success condition.
- The commands you ran and their results, including failures and checks you did not run.
- Status: ready for PR preparation, incomplete, or awaiting a decision. A partial or failing implementation is not ready. Include existing failures, remaining human assessments, and unresolved risks.

If blocked or interrupted, preserve the worktree and report completed work and the next useful action. Do not post comments or make further board changes to report a blocker. Hand separately authorized next actions back to the parent.
