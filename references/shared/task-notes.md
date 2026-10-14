# Task notes

Keep concise working notes outside the conversation when research, decisions, or sustained execution would be costly to reconstruct. Prefer a small file that you can read throughout the task, especially when context is limited. A short task with no useful findings to preserve needs no notes file. Respect read-only requests and project rules for file writes.

## Locate or create the notes

Read project instructions for an existing notes format or session-directory override. Reuse the notes identified by the task or handoff. If no path is supplied, look for notes tied to the selected issue, PR, branch, or worktree; do not select another task merely because its notes are newer.

When no convention exists, use `docs/dev-sessions/{timestamp}-{slug}/notes.md`, with a timestamp in `YYYY-MM-DD-HHMM` format and a short slug from the task branch or issue. Create the directory inside the active worktree, because untracked files in the main checkout are not available in another worktree. A coordinator that owns no worktree, such as a queue or delivery coordinator, does not write in the subject checkout: it keeps its notes at `~/.local/state/ghflow/notes/{timestamp}-{slug}/notes.md` and reports that path in its summary. Create only the notes file that the task needs. Follow project rules for committing or ignoring notes.

When the project commits notes, commit them with the code they describe or once at the end of an operation. Between those commits, keep notes edits in the working tree. Do not amend a published commit or force-push only to change notes; each push restarts hosted CI for a markdown edit. Record the code commit and the checks that cover it; do not record the commit that will contain the notes, because it does not exist until after the commit. Do not wait for hosted CI on a notes-only commit; report the code commit's CI and name the notes-only commits after it. After independent review, do not add a notes-only commit, before or after the PR is marked ready. Record the review outcome in the notes with the correction commit when there is one; when there is none, the notes stay at the reviewed head. The PR description that the ready submission writes is the record of the ready result. A notes-only commit after ready moves the head, restarts hosted CI, and reopens follow-up for a markdown change.

Keep the same file when context is compacted, a session resumes, or a worker hands the task to another worker. Record its absolute path in the task handoff. If work moves to another checkout or machine, make the notes accessible there and report the new path. If the notes are unavailable, report the gap and use the available issue, PR, and Git evidence.

## Write useful entries frequently

Update notes soon after useful discoveries, settled decisions, and failed attempts, and before a handoff or known interruption. Use these events rather than a fixed interval or an entry for every tool call.

Put a short `Resume here` summary at the top of the file. Keep the current goal and scope, issue or PR, worktree and branch, confirmed decisions, latest checks and their revisions, blocker, and next action there. Update this summary at useful checkpoints so a resumed worker can find the next step without reading the whole history. Update the checks and status after the commands run, not before; a resumed worker treats the summary as what happened.

Keep older findings and attempts underneath. Read the summary first, then relevant entries and linked evidence as needed. Condense repetitive or superseded entries while retaining decision reasons and source references. Add concise entries for:

- Findings, with their source, revision, and relevant assumptions.
- Decisions, with who settled them, the reason, and relevant scope or authorization limits. Distinguish proposals and unresolved questions from confirmed decisions.
- Attempts and checks, with what was tried, the actual result, and why another attempt would differ. Record a result only after the command has run. Write a step you have not performed as the next action, not as an outcome; a planned push, check, or verification is not evidence until it happens.

Link to code, commits, discussions, or detailed output instead of copying logs. Correct or mark superseded entries when evidence changes, so a resumed agent can identify the current conclusion. Apply [Evidence](evidence.md) to recorded findings and results, and [Decisions](decisions.md) to choices that remain unresolved. Notes support the task; issues, PRs, and actual code still supply their current state.

## Read before resuming or repeating work

At resumption, after context compaction, or before repeating research or reopening a decision, read the relevant notes. Reuse findings whose sources and assumptions still apply under [Evidence](evidence.md#sources-and-revisions). Recheck the claims affected by changed code or assumptions and preserve unaffected findings. Use confirmed decisions within their scope; return a material conflict or changed requirement through [Decisions](decisions.md#return-unresolved-decisions).

Pass the notes path and relevant facts under [Coordination](coordination.md#handoffs). For independent review, supply necessary facts and source references rather than the author's conversation or desired conclusions, as [review-changes](../tasks/review-changes.md#set-up-the-reviewer) requires.
