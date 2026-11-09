# Sweep blocked issues

Find open issues labeled `triage:blocked` whose blockers have all closed, and return them to `triage:needs-definition` so that they appear with actionable work again. This task changes labels and posts comments. It does not define issues; [sweep-needs-definition](sweep-needs-definition.md) does that next.

Apply [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md) throughout. Subagents perform subject-repository writes following [Agent identity](../shared/identity.md) and [GitHub writes](../shared/github-writes.md).

## List blocked issues

Query open issues in the subject repository with the label `triage:blocked`. If none carry it, report that and stop.

## Check each issue's blockers

For each issue, read its native blocked-by relationships, for example with `gh issue view ISSUE --json blockedBy`, and read the state of each blocking issue. Classify the issue:

- **Unblocked**: it has at least one blocked-by relationship, and every blocking issue is closed.
- **Still blocked**: at least one blocking issue is open.
- **No recorded blocker**: it has no blocked-by relationships. The blocker may exist only in text.

A blocker that closed as `not planned` still counts as closed, but it can invalidate the blocked issue's plan. Say so in the comment and in the report.

## Update the issues

1. For each unblocked issue, replace `triage:blocked` with `triage:needs-definition` with `python3 "$GHFLOW_CLI" exec -- gh issue edit ...`. Post a short comment with `python3 "$GHFLOW_CLI" exec -- gh issue comment ...` that names the closed blockers, with the PR or commit that closed each when GitHub records one, and says that any outline needs a full specification against current code.
2. Leave still-blocked issues unchanged.
3. For an issue with no recorded blocker, read its body and comments. If they name blocking issues, report them so that the relationships can be set. Do not relabel the issue on text alone.

## Return the sweep result

Report each issue with its classification, its blockers and their states, and the label change and comment URL when you made one. List issues with no recorded blocker separately. Suggest sweep-needs-definition for the issues that returned to `triage:needs-definition`.
