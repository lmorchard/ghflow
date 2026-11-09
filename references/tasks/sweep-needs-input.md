# Sweep issues needing input

Conduct an interactive review of issues marked `triage:needs-input`. Settle the blocking product and design questions with the user, update the issue records, and advance each issue to its next state.

Apply [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md) throughout. The parent agent conducts the conversation; subagents execute updates in the subject repository following [Agent identity](../shared/identity.md). Run every Git and GitHub write through `python3 "$GHFLOW_CLI" exec -- ...` or a ghflow command. A plain `git` or `gh` write is a defect. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## List pending issues

Query open issues in the subject repository with the label `triage:needs-input`:

```bash
gh issue list --repo OWNER/REPO --label "triage:needs-input" --limit 50
```

If no issues carry the label, report that the input backlog is clear and stop.

## Present issues for review

Group related issues into decision clusters when multiple issues share a common architectural pattern (such as replacing bespoke skills with standard MCP servers, deferring complex speculative infrastructure, or setting platform scope). Clustering allows the user to resolve related questions in a single decision rather than stepping through serial turns. For isolated issues, present them one at a time.

For each issue or cluster:

1. Read the issue title, body, and recent comments, focusing on the triage findings comment.
2. Present a short summary in conversation:
   - Issue number, title, and URL.
   - Core problem and current code status.
   - The specific 1 to 2 questions needing the user's decision, with clear choices or trade-offs.
3. If more background is needed, follow [interview-issue](interview-issue.md) to explore the tradeoffs.

Do not ask the user to read raw code or diffs unless they ask.

## Record the decision

Once the user provides a direction:

1. Dispatch a subagent to update the issue in the subject repository:
   - Post a comment with `python3 "$GHFLOW_CLI" exec -- gh issue comment ...` recording the user's confirmed decision and rationale.
   - Remove the `triage:needs-input` label with `python3 "$GHFLOW_CLI" exec -- gh issue edit ISSUE_URL --remove-label triage:needs-input`.
2. Apply the resulting state:
   - **User decided not to proceed**: Close the issue with `python3 "$GHFLOW_CLI" exec -- gh issue close ISSUE_URL --reason "not planned"` (and add `wontfix` if used).
   - **Decision makes the task actionable as-is**: Add `triage:ready` with `python3 "$GHFLOW_CLI" exec -- gh issue edit ISSUE_URL --add-label triage:ready`.
   - **Decision settles direction, but technical details or criteria remain open**: Add `triage:needs-definition` with `python3 "$GHFLOW_CLI" exec -- gh issue edit ISSUE_URL --add-label triage:needs-definition`.
   - **Decision makes the issue wait for other open issues**: Set native blocked-by relationships and add `triage:blocked` with `python3 "$GHFLOW_CLI" exec -- gh issue edit ...`.
   - **User decided to keep the issue as a parking lot or a parent tracked by children**: Add `triage:parked` with `python3 "$GHFLOW_CLI" exec -- gh issue edit ISSUE_URL --add-label triage:parked`.
3. If the issue belongs to a parent theme, update the parent issue's rollup comment to reflect the new state.
4. Report the updated status to the user and proceed to the next issue or cluster.

## Conclude or pause

Stop when all `triage:needs-input` issues have been resolved, or when the user requests a pause. Return a summary of issues updated, closed, or queued for technical definition.
