# Implement an issue

Produce tested, committed changes for the requested issue, with enough evidence for another agent to prepare a PR. This skill ends with a local branch and a report. Do not push, open a PR, merge, or remove the worktree.

Read this reference and your handoff first. Open the shared references when their conditions apply, as [Working context and tool output](../shared/context.md) states: [Agent identity](../shared/identity.md#running-commands-under-the-identity) before your first Git or `gh` command; [Board status](../shared/board-status.md) before you move the issue In progress; [Task notes](../shared/task-notes.md) when you create or resume notes; [Decisions](../shared/decisions.md) when a fact or choice is missing; [Evidence](../shared/evidence.md) when you record a check or write your report; [Authorization](../shared/authorization.md) when a step's scope or permission is in question; [GitHub writes](../shared/github-writes.md) before you change a GitHub record. Reading them all before you start delays the work and changes no decision.

Apply [Working context and tool output](../shared/context.md) to selective source reads and complete evidence with concise output.

## Read the issue and current code

Read the project instructions, the issue body, and relevant comments. Identify the intended result, scope limits, success conditions, and confirmed decisions. Do not require labels or documents from another skill.

Inspect the relevant code and tests at the current revision, and determine whether the reported problem still exists. If part of the issue is already satisfied, record the evidence and implement only what remains. If nothing remains, report that. Do not create unrelated work to justify a commit.

When a fact or choice is missing, apply [Decisions](../shared/decisions.md). Settle routine implementation choices from current evidence. Return decisions about the intended result instead of redefining the issue.

## Prepare an isolated workspace

Inspect the current status, branches, and existing worktrees before you change anything. Preserve unrelated work.

Determine the base branch from the project or the request. Do not assume it is `main` or that the current checkout is the right base. Refresh its remote reference when access permits.

Create a worktree and task branch following project conventions. For a new branch, run `python3 "$GHFLOW_CLI" worktree create ISSUE_URL --branch BRANCH` with `--copy` for each file the project facts say to copy, such as `.env`, `--setup` for each setup command, such as `uv sync`, `--notes` when the project commits session notes, and `--owner` and `--project` to move the issue In progress; it refuses an existing branch or path, which means you are resuming. Do not reset or switch the shared checkout. Do not reuse another session's worktree because its name matches the issue.

If resuming, confirm the supplied worktree and branch before you edit, and read their existing changes. Continue that work instead of starting a competing implementation.

Prepare what the baseline checks need, such as generated code, frontend packages, and browser binaries. A Python test suite can need JavaScript tools too. Install declared dependencies as the project directs, before the baseline. Installs into the project or the user's home are part of the task. A system-level install, such as one that uses `sudo` or the operating system's package manager, needs explicit authorization: report the need and the command instead of running it. Do not run an installation at the same time as tests that use or copy those dependencies; some gate commands reinstall packages, so check before running gates in parallel. Run one full test suite at a time. A second full suite on the same machine can starve or kill the first and produce failures that are not in the code; run targeted tests while a full suite runs, not another full suite. Use test configuration and isolated data where required. Do not copy credentials or connect to live services to make tests pass.

Run the relevant baseline before implementation. Record existing failures and environment limits separately from new failures. If a baseline problem prevents meaningful verification, investigate or report it. Independent implementation can continue, but incomplete verification is not success.

Bound that investigation. If the suite passes in one configuration, such as a serial run or a smaller worker count, and fails or dies in another, record each configuration with its command and result, name the failing one as an environment limit, and continue; hosted CI settles it on the published commit. Do not repeat a failing configuration without a new reason. If no configuration passes, report the blocker with what you tried instead of continuing to probe.

## Mark implementation in progress

When implementation starts, move the issue to In progress, following [Board status](../shared/board-status.md). `worktree create` with `--owner` and `--project` does this move. On resumption, keep a later state such as In review or Done. If the update fails, report it and continue implementation.

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

The project's gates, as the facts file names them, decide whether the change is verified. A check outside the gates, such as an evaluation against a live model, adds evidence when it runs. If it fails because of the environment, such as an unreachable endpoint, a missing credential, or broken local configuration, report it as an evidence limit with the error and continue. Do not debug the environment to make it run. Do not switch the check to another model, a paid service, or an account the handoff does not name; that changes cost or permissions and needs authorization.

## Return useful progress for draft publication

When the enclosing flow authorizes publication, apply [Draft PRs and readiness](../shared/pr-lifecycle.md). At the first significant change, inspect the intended diff, run appropriate targeted checks, and commit a coherent checkpoint. Full implementation checks and final self-review still apply before the completed implementation handoff.

When the handoff authorizes you to continue into [submit-pr](submit-pr.md), commit the checkpoint and publish it as a draft through that reference in the same session, then resume implementation on the same branch. Before the completed implementation handoff, publish the final commits to the same draft under the same authorization. Otherwise, return the checkpoint to the coordinator for [submit-pr](submit-pr.md), with the worktree, branch, base, committed head, checks, remaining work, and next action, and do not push or open the PR yourself. State that implementation is incomplete when it is. For a standalone local-only request, continue locally without this publication handoff.

When the handoff gives a deadline, start nothing new at it, even mid-change. Commit the work in progress with a subject that says it is incomplete, publish it to the draft PR, record the remaining steps and the state of the checks in the task notes, and return them with the PR URL and head. Unfinished work that is published can resume; work that stays in the worktree is lost to the next run's evidence.

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
- The implementation model: the ID your runtime states to you, or "unknown". Do not record or mention a configured or default model as your identity, in the return or the notes. The parent uses it to choose a different model for review.
- The changes, and the result for each success condition.
- The commands you ran and their results, including failures and checks you did not run.
- Status: ready for PR preparation, incomplete, or awaiting a decision. A partial or failing implementation is not ready. Include existing failures, remaining human assessments, and unresolved risks.

If blocked or interrupted, preserve the worktree and report completed work and the next useful action. Do not post comments or make further board changes to report a blocker. Hand separately authorized next actions back to the parent.
