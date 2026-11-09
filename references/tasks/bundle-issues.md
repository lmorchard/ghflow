# Bundle issues under parent issues

Survey an open issue backlog, cluster related items into thematic initiatives, and organize them under native GitHub parent issues. This groups scattered issues by code boundary and outcome before deep triage or implementation.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Agent identity](../shared/identity.md) throughout. Run every Git and GitHub write through `python3 "$GHFLOW_CLI" exec -- ...` or a ghflow command. A plain `git` or `gh` write is a defect. The parent agent discusses proposed clusters with the user; subagents execute issue creation and relationship updates in the subject repository. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Survey the backlog

Read the open issues in the subject repository with GitHub CLI:

```bash
gh issue list --repo OWNER/REPO --state open --limit 200 --json number,title,body,labels
```

Filter out issues that already belong to a parent issue or represent isolated, one-off fixes. If the repository is large, focus the survey on a specific subsystem or area label.

## Synthesize thematic clusters

Group related open issues into bundles of 3 to 8 issues sharing a common purpose:

- **Subsystem or architectural boundary**: Issues touching the same services, database models, API routes, or UI components.
- **User outcome**: Issues working toward a single coherent capability or milestone.
- **Existing umbrellas**: Check whether an existing open issue was already intended as an umbrella for the others.

Identify issues that appear to be duplicates, conflicting approaches, or direct prerequisites of other items in the cluster.

Leave independent, standalone issues unbundled rather than forcing them into artificial groups.

## Propose bundles in conversation

Present candidate bundles to the user in conversation:

- Proposed theme title and high-level goal.
- Existing umbrella issue, or proposed title and summary for a new parent issue.
- Candidate child issues with their numbers, titles, and why they belong together.
- Any direct duplicates or obsolete items noticed during clustering.
- Standalone issues that should remain unparented.

Adjust cluster boundaries and parent titles based on user feedback.

## Establish parent and child relationships

When the user approves a bundle:

1. If a new parent issue is needed, file it in the subject repository following [file-issue](file-issue.md):
   - Include a concise problem statement, the shared boundary, and success criteria for the whole initiative.
   - Apply the `theme` label to identify it as a thematic parent umbrella issue. If the label does not exist, create it:
     ```bash
     python3 "$GHFLOW_CLI" exec -- gh label create "theme" --repo OWNER/REPO --description "Thematic parent umbrella issue" --color "6f42c1"
     ```
   - For an existing parent issue, ensure the `theme` label is applied.
2. Link the child issues to the parent using native GitHub sub-issue relationships:
   ```bash
   python3 "$GHFLOW_CLI" exec -- gh issue edit PARENT_NUMBER --repo OWNER/REPO --add-sub-issue CHILD_NUMBER1,CHILD_NUMBER2
   ```
   Alternatively, set the parent from the child:
   ```bash
   python3 "$GHFLOW_CLI" exec -- gh issue edit CHILD_NUMBER --repo OWNER/REPO --parent PARENT_NUMBER
   ```
3. Read back the updated parent issue to confirm that GitHub reflects the attached sub-issues.

## Return and hand off

Return a summary of established parent-child structures and unbundled standalone issues.

Recommend the next step for each bundle:
- Run [triage-issues](triage-issues.md) on a specific bundle to evaluate completion and currency.
- Run [decompose-parent-issue](decompose-parent-issue.md) if the parent needs further breakdown.
- Advance ready children to [define-issue](define-issue.md) or [implement-issue](implement-issue.md).
