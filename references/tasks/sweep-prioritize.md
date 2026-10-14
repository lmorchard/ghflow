# Sweep and prioritize issues

Evaluate open `triage:ready` issues, assign their `Priority` and `Size` fields, and stage high-priority (`P0`/`P1`) issues into the project board's `Backlog`. Re-sweep lower-priority issues when the high-priority queue runs low or circumstances warrant a rethink. This is the task that promotes an issue into the `P0`/`P1` tier; [curate-ready-queue](curate-ready-queue.md) never changes priorities, as [Priority tiers](../shared/board-status.md#priority-tiers) states. This skill does not move issues to `Ready` or begin implementation.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), [Board status](../shared/board-status.md), and [Agent identity](../shared/identity.md) throughout. The parent agent conducts the ranking review with the user; subagents execute project board field updates in the subject repository. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Select the candidate pool

Identify the set of issues to prioritize:
- **Unprioritized sweep**: Open issues with label `triage:ready` that lack a `Priority` field on the project board, typically scoped by parent theme.
- **Re-sweep of lower tiers**: Query existing issues below `P1` when curate-ready-queue reports a thin `P0`/`P1` pool, when the active `P0`/`P1` queue is exhausted, when a milestone completes, or when new architecture makes previously deferred tasks high-leverage.

When the user says the re-sweep feeds an unattended run, also check each candidate against the conditions in [Unattended fit](curate-ready-queue.md#unattended-fit) and report the result beside its suggested priority. Fit is evidence for the user's promotion decision, not a promotion by itself.

## Estimate priority and size

For each candidate issue, evaluate its technical specification against current code:

### Priority Tiers
- **P0 (Critical / Blocker)**: Active bug, data loss risk, test execution hazard (e.g. real LLM calls in unit tests), or gate landmine blocking development.
- **P1 (High Priority)**: Core product capability, major user-facing improvement, or high-leverage architectural unblocker.
- **P2 (Medium Priority)**: Quality-of-life improvement, secondary feature, or UI polish without urgent user impact.
- **P3 (Low Priority)**: Minor edge-case optimization, cosmetic cleanup, or low-urgency refactoring.
- **P4 (Someday)**: Kept for reference with no current plan to schedule it.

Use the Priority options the board defines. When they differ from this list, keep the board's order and names, and report the difference.

### Size Tiers
- **XS**: One-liner fix or single config field change.
- **S**: Small, self-contained change (<100 lines, 1–2 files).
- **M**: Medium component or module change with targeted tests.
- **L**: Substantial cross-module change requiring broader integration verification.
- **XL**: Major architectural task (consider whether it should be decomposed).

## Review ranking with the user

Present candidate rankings in a summary table grouped by parent theme:

| Issue | Title | Current Priority | Suggested Priority | Suggested Size | Rationale |
|---|---|:---:|:---:|:---:|---|

For an unattended re-sweep, add the unattended-fit result for each candidate. Highlight items recommended for `P0` or `P1` against those left in a lower tier, and mark each promotion. Discuss adjustments with the user and record confirmed values. Change no field before the user confirms.

## Update project board fields

Once rankings are confirmed, dispatch a subagent to update the project board under the machine identity:

1. If the issue is not on the board, add it with `python3 "$GHFLOW_CLI" board set-status ISSUE_URL --owner OWNER --project NUMBER --status "Backlog"`. Do not use set-status to move an issue that is already on the board.
2. Set the confirmed `Priority` with `python3 "$GHFLOW_CLI" board set-field ISSUE_URL --owner OWNER --project NUMBER --field "Priority" --value "P1"`, and the confirmed `Size` the same way with `--field "Size"`, under [Other single-select fields](../shared/board-status.md#other-single-select-fields).
3. Confirm each read-back. Do not use raw `gh project item-edit` commands.

An issue keeps its Status: a promotion to `P0` or `P1` leaves it in `Backlog` for curation, and a demotion of an issue in an active column is a separate decision under [Priority tiers](../shared/board-status.md#priority-tiers).

## Return and hand off

Return a summary table of prioritized issues:
- Total counts by priority, using the board's options.
- List of newly staged or promoted `P0`/`P1` items in the board's `Backlog`, with the unattended-fit result when the re-sweep feeds an unattended run.

Hand off to [curate-ready-queue](curate-ready-queue.md) to select the next tasks to pull into the board's `Ready` column.
