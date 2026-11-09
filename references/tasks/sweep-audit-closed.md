# Sweep and audit closed issues

Review issues that were closed autonomously during triage. Present a summary digest of findings and cited evidence to the user, confirm the closures, and reopen any issues the user decides to retain.

Apply [Authorization](../shared/authorization.md) and [Evidence](../shared/evidence.md) throughout. The parent agent conducts the review; subagents execute updates in the subject repository following [Agent identity](../shared/identity.md). Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## List agent-closed issues

Query closed issues in the subject repository carrying the `triage:agent-closed` label:

```bash
gh issue list --repo OWNER/REPO --state closed --label "triage:agent-closed" --limit 50
```

If no issues carry the label, report that there are no agent-closed issues to audit and stop.

## Present the digest

For each issue in the list:

1. Read the closing comment and evidence cited by the triage agent.
2. Build a summary table for the user:
   - Issue number and title.
   - Closure classification (`completed` vs `not planned` / `obsolete`).
   - Cited evidence (commit SHA, PR number, or reason for obsolescence).

Present the digest in conversation for human confirmation.

## Process feedback

Collect the user's evaluation:

- **Confirmed closures**:
  - The issues remain closed.
  - Retain the `triage:agent-closed` label unless the user requests removing it.
- **Reopened issues**:
  - Dispatch a subagent to:
    1. Reopen the issue: `python3 "$GHFLOW_CLI" exec -- gh issue reopen ISSUE_URL`.
    2. Remove the `triage:agent-closed` label with `python3 "$GHFLOW_CLI" exec -- gh issue edit ISSUE_URL --remove-label triage:agent-closed`.
    3. Post a comment with `python3 "$GHFLOW_CLI" exec -- gh issue comment ...` explaining why the issue was reopened and the user's intent.
    4. Apply `triage:needs-input` or `triage:needs-definition` with `python3 "$GHFLOW_CLI" exec -- gh issue edit ...` based on the user's direction.

## Conclude the sweep

Return a summary of confirmed closures, reopened issues, and any pending follow-up tasks.
