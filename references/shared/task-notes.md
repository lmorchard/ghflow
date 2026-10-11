# Task notes

Keep concise working notes outside the conversation when research, decisions, or sustained execution would be costly to reconstruct. Prefer a small file that you can read throughout the task, especially when context is limited. A short task with no useful findings to preserve needs no notes file. Respect read-only requests and project rules for file writes.

## Locate or create the notes

Read project instructions for an existing notes format or session-directory override. Reuse the notes identified by the task or handoff. If no path is supplied, look for notes tied to the selected issue, PR, branch, or worktree; do not select another task merely because its notes are newer.

When no convention exists, use `docs/dev-sessions/{timestamp}-{slug}/notes.md`, with a timestamp in `YYYY-MM-DD-HHMM` format and a short slug from the task branch or issue. Create the directory inside the active worktree, because untracked files in the main checkout are not available in another worktree. Create only the notes file that the task needs. Follow project rules for committing or ignoring notes.

Keep the same file when context is compacted, a session resumes, or a worker hands the task to another worker. Record its absolute path in the task handoff. If work moves to another checkout or machine, make the notes accessible there and report the new path. If the notes are unavailable, report the gap and use the available issue, PR, and Git evidence.

## Write useful entries frequently

Update notes soon after useful discoveries, settled decisions, and failed attempts, and before a handoff or known interruption. Use these events rather than a fixed interval or an entry for every tool call.

Put a short `Resume here` summary at the top of the file. Keep the current goal and scope, issue or PR, worktree and branch, confirmed decisions, latest checks and their revisions, blocker, and next action there. Update this summary at useful checkpoints so a resumed worker can find the next step without reading the whole history.

Keep older findings and attempts underneath. Read the summary first, then relevant entries and linked evidence as needed. Condense repetitive or superseded entries while retaining decision reasons and source references. Add concise entries for:

- Findings, with their source, revision, and relevant assumptions.
- Decisions, with who settled them, the reason, and relevant scope or authorization limits. Distinguish proposals and unresolved questions from confirmed decisions.
- Attempts and checks, with what was tried, the actual result, and why another attempt would differ.

Link to code, commits, discussions, or detailed output instead of copying logs. Correct or mark superseded entries when evidence changes, so a resumed agent can identify the current conclusion. Apply [Evidence](evidence.md) to recorded findings and results, and [Decisions](decisions.md) to choices that remain unresolved. Notes support the task; issues, PRs, and actual code still supply their current state.

## Read before resuming or repeating work

At resumption, after context compaction, or before repeating research or reopening a decision, read the relevant notes. Reuse findings whose sources and assumptions still apply under [Evidence](evidence.md#sources-and-revisions). Recheck the claims affected by changed code or assumptions and preserve unaffected findings. Use confirmed decisions within their scope; return a material conflict or changed requirement through [Decisions](decisions.md#return-unresolved-decisions).

Pass the notes path and relevant facts under [Coordination](coordination.md#handoffs). For independent review, supply necessary facts and source references rather than the author's conversation or desired conclusions, as [review-changes](../tasks/review-changes.md#set-up-the-reviewer) requires.
