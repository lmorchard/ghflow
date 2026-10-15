# Curate the ready queue

Select high-priority (`P0`/`P1`) issues from the project board's `Backlog` and advance them to `Ready`. Maintain a bounded work-in-progress (WIP) queue (typically 3 to 5 items) so implementers have a clear, prioritized pipeline without overwhelming the board. This skill does not start implementation or submit pull requests.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), [Board status](../shared/board-status.md), and [Agent identity](../shared/identity.md) throughout. The parent agent discusses candidate tasks with the user; subagents execute board transitions in the subject repository. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Audit current board WIP

Read every board item with the validated traversal in [Audit the Ready queue](burndown-ready-queue.md#audit-the-ready-queue), and use partial output for nothing. From that inventory:

- Count items currently in `Ready`, `In progress`, and `In review`.
- For each item already in `Ready`, recommend that it stay or move back to `Backlog`, with a one-line reason, against the same criteria you use for candidates.
- If the `Ready` column is already at capacity (e.g. 5 items), report the current queue and stop, or propose swapping a blocked or deprioritized item back to `Backlog`.
- Calculate available slots in `Ready` based on the target WIP limit (default 3 to 5 items).

## Select candidates from Backlog

Use the selection criterion that the user states, such as size, language, verification method, or fitness for an unattended run, which [Unattended fit](#unattended-fit) defines. Apply it to `Backlog` items with priority `P0` or `P1` only; without a stated criterion, select from the same tier. Curation narrows attention to that tier and does not change priorities, as [Priority tiers](../shared/board-status.md#priority-tiers) states. Read each plausible candidate's body and comments before you rank it. Labels such as `triage:ready` and an unset Size or Priority field do not show that an issue is small or settled.

1. Sort candidates:
   - `P0` items before `P1`.
   - Small, self-contained tasks (`XS`/`S`) that unblock other work.
   - Tasks with satisfied prerequisites.
2. If the `P0`/`P1` Backlog is empty, recommend running [sweep-prioritize](sweep-prioritize.md) to evaluate unprioritized issues or re-sweep deferred `P2`/`P3` issues.

## Unattended fit

When the user curates for an unattended run, apply this criterion to the `P0` and `P1` candidates. The user's request can change any part of it, such as the size range or the number of issues. A candidate fits when all of these hold:

- Its acceptance criteria are checked by the project's gate commands, which the project facts file names. A criterion that needs a person, a running dev server, a browser, or a live external service disqualifies the issue, even when unit tests also exist.
- Verifying it needs no new service, credential, or account.
- Its scope is settled: the decisions are recorded on the issue, and no open question or proposal awaits the user.
- It is independent of the other selected issues and of open PRs.

Size is a flag, not a condition. Estimate each fitting candidate's change, including tests and documentation, but not lockfiles, vendored files, or other generated output; the default range is about 50 to 200 lines. If the change regenerates a lockfile or vendored bundle, say so beside the estimate and treat it as likely to run long: in the third unattended run, an issue estimated at 120 to 200 lines changed 537 lines with its lockfiles and took three hours. Put a candidate whose estimate reaches past the range last in the proposed order and name the risk, because in the second unattended run an issue estimated at 150 to 240 lines took twice as long as the others. The user decides whether it goes in.

The requested number of issues is a maximum. When fewer candidates fit within the size range, propose only those, say that the pool is thin, and recommend a [sweep-prioritize](sweep-prioritize.md) re-sweep of the lower tiers. Name at most one candidate past the range, as an optional last pick. Do not fill the batch with candidates past the range.

Present the unattended candidates in this table, one row per candidate, including rejected ones:

| Issue | Title | Gates verify acceptance | No new service or credential | Scope settled | Independent | Size estimate | Result |
|---|---|:---:|:---:|:---:|:---:|:---:|---|

Write yes or no in each condition column, with the evidence when the answer is not obvious from the title. In Result, write pick, optional last pick, or the first condition the candidate fails.

## Review selection with the user

Present the candidate queue in conversation. For an unattended run, use the table in [Unattended fit](#unattended-fit); otherwise use this one:

| Issue | Title | Priority | Size | Why Next |
|---|---|:---:|:---:|---|

Highlight sequencing logic (e.g., test guards before new feature tests). Confirm the batch with the user and adjust based on current project goals.

## Advance status on the board

Once approved, dispatch a subagent to make the board changes under the machine identity. Move each selected issue from `Backlog` to `Ready`:

```bash
python3 "$GHFLOW_CLI" board set-status ISSUE_URL --owner OWNER --project NUMBER --status "Ready"
```

A swap of a `Ready` item back to `Backlog` is a backward move. Pass `--allow-backward` with the user's decision as the reason, as [Board status](../shared/board-status.md#limits) requires. Propose a `Size` for each pick from your estimate, because the burndown runs smaller issues first within a priority. When the user decides a Size, set it with `board set-field` under [Other single-select fields](../shared/board-status.md#other-single-select-fields). Do not change Priority here. Confirm each read-back.

## Return and hand off

Display the final `Ready` queue:
- Issues currently staged in `Ready` with their priority, size, and titles.
- Total count of active items in `Ready` against the WIP limit.

Hand off to [implement-issue](implement-issue.md) or [express-issue](express-issue.md) to pick up the top item in the `Ready` queue.
