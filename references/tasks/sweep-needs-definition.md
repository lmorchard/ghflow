# Sweep issues needing definition

Develop open issues labeled `triage:needs-definition` into actionable definitions. Use [Define an issue](define-issue.md) for research, scope, and issue content. Keep each definition proportional to its goal and evidence.

Apply [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md) throughout. The parent agent coordinates the sweep; subagents execute research and issue updates in the subject repository following [Agent identity](../shared/identity.md). Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## List pending issues

Query open issues in the subject repository with the label `triage:needs-definition`:

```bash
gh issue list --repo OWNER/REPO --label "triage:needs-definition" --limit 50
```

Optionally filter by a specific parent issue or component area. If no issues carry the label, report that all accepted issues are fully defined and stop.

## Define each issue

Process issues one at a time or in bounded slices of 2 to 5 issues. For each issue, dispatch a subagent to apply [Define an issue](define-issue.md). Give the agent the issue, current evidence, and existing authorization.

Use the shared [Decisions](../shared/decisions.md) rule when facts or choices are missing. Return material product decisions to the parent instead of choosing them in the sweep.

If refinement depends on another open issue that will change the code or supply a contract, follow [Blocked issues](../shared/triage-labels.md#blocked-issues). Set the native blocked-by relationship and apply `triage:blocked`. Optionally replace the body with an outline. Return the issue to the parent. If only part waits, propose a split.

If research finds a product or design decision that needs user judgment, stop the definition. Apply `triage:needs-input`, post the focused question, and return it to the parent.

## Update the issue record

Once the specification is solid:

1. Update the issue body in the subject repository with the reviewed definition:
   ```bash
   ghflow exec -- gh issue edit ISSUE_NUMBER --repo OWNER/REPO --body-file /tmp/defined-body.md
   ```
2. Remove `triage:needs-definition` and add `triage:ready`.
3. Post a brief comment linking to the revised body and noting that the issue is now actionable for implementation.
4. When the issue belongs to a parent theme, update the parent issue's rollup comment to reflect the newly ready status.

## Conclude the sweep

Return a summary to the parent with:

- Issue number, title, and updated label.
- The definition's main boundary and any unresolved question or dependency.
- The next useful step.
- If scenario answers assessed the sweep, report them as samples and state what they do not establish.
